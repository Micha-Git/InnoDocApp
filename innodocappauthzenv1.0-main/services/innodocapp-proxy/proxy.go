package main

import (
	"bytes"
	"encoding/json"
	"fmt"
    "time"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
    "net/url"
	"os"
	"strings"
	"proxy/authzen"
	"github.com/golang-jwt/jwt/v5"
    "github.com/MicahParks/keyfunc/v3"
)

func main() {
	BACKEND := os.Getenv("INNODOCAPP_HOST")
	PDP_EVALUATION_URL := os.Getenv("OPA_EVALUATION_URL")
	OIDC_CONFIG := os.Getenv("OIDC_CONFIG")

	if BACKEND == "" || PDP_EVALUATION_URL == "" || OIDC_CONFIG == "" {
		vars := []string{"OPA_EVALUATION_URL", "INNODOCAPP_HOST", "OIDC_CONFIG"}
		panic(fmt.Sprintf("The following environment variables MUST be defined: %v", vars))
	}

	log.Printf("Starting proxy. BACKEND: %s, PDP_HOST: %s", BACKEND, PDP_EVALUATION_URL)

    for i := 0; i < 10; i++ {
        resp, err := http.Get(OIDC_CONFIG)
        if err == nil && resp.StatusCode == 200 {
            break
        }
        log.Printf("IDP not ready, try %d", i+1)
        time.Sleep(5 * time.Second)
    }

    var jwks keyfunc.Keyfunc
    var err error

   	jwksURL, err := FetchJWKSURI(OIDC_CONFIG)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

    jwks, err = keyfunc.NewDefault([]string{jwksURL})

	backendRemote, err := url.Parse(BACKEND)
	if err != nil {
		log.Printf("Failed to parse BACKEND url: %v", err)
		panic(err)
	}

	proxy := httputil.NewSingleHostReverseProxy(backendRemote)

	// Create the main handler that performs authz
	mainHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Received request: %s %s", r.Method, r.URL.Path)
		log.Printf("Request headers: %v", r.Header)

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			log.Println("Authorization header missing")
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		var token string
		if strings.HasPrefix(authHeader, "Bearer ") {
			token = strings.TrimPrefix(authHeader, "Bearer ")
			token = strings.TrimSpace(token)
            fmt.Println("TOKEN oben:", token)
			log.Printf("Extracted Bearer token: %s", token[:50]+"...")
		} else {
			log.Printf("Authorization header present but not Bearer: %s", authHeader)
			http.Error(w, "Invalid Authorization header format", http.StatusUnauthorized)
			return
		}

		var bodyBytes []byte
		if r.Body != nil {
			bodyBytes, _ = io.ReadAll(r.Body)
			log.Printf("Request body: %s", string(bodyBytes))
			// Restore the body for downstream handlers
			r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))
		} else {
			log.Println("Request body is nil")
		}

		// Validate JWT and extract subject
		subjectInfo, err := validateAndExtractSubject(token, jwks)
		if err != nil {
			log.Printf("JWT validation failed: %v", err)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		authXRequest := createAuthZENRequest(subjectInfo, r)
		log.Printf("AuthZEN request: %+v", authXRequest)

		// Send request to pdp
		reqBody, err := json.Marshal(authXRequest)
		if err != nil {
			log.Printf("Failed to marshal AuthZEN request: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		log.Printf("AuthZEN request JSON: %s", string(reqBody))

		log.Printf("Sending request to PDP: %s", PDP_EVALUATION_URL)
		pdpReq, err := http.NewRequest("POST", PDP_EVALUATION_URL, bytes.NewBuffer(reqBody))
		if err != nil {
			log.Printf("Failed to create PDP request: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		pdpReq.Header.Set("Content-Type", "application/json")
		if token != "" {
			pdpReq.Header.Set("Authorization", "Bearer "+token)
		}
		log.Printf("PDP request headers: %v", pdpReq.Header)

		client := &http.Client{}
		pdpResp, err := client.Do(pdpReq)
		if err != nil {
			log.Printf("Failed to contact PDP: %v", err)
			// Deny by default
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		defer pdpResp.Body.Close()
		log.Printf("PDP response status: %s", pdpResp.Status)

		respBody, err := io.ReadAll(pdpResp.Body)
		if err != nil {
			log.Printf("Failed to read PDP response: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		log.Printf("PDP response body: %s", string(respBody))

		var authzResponse authzen.AuthZResponse
		if err := json.Unmarshal(respBody, &authzResponse); err != nil {
			log.Printf("Failed to unmarshal PDP response: %v", err)
			http.Error(w, "Forbidden", http.StatusForbidden)
			return
		}
		log.Printf("Parsed PDP response: %+v", authzResponse)

		decision := authzResponse.Decision
		log.Printf("PDP decision: %v", decision)
		var httpStatus int
		if authzResponse.Context != nil {
			log.Printf("PDP context: %+v", authzResponse.Context)
			if status, ok := authzResponse.Context["httpStatus"].(float64); ok {
				httpStatus = int(status)
				log.Printf("PDP context httpStatus: %d", httpStatus)
			}
		} else {
			log.Println("PDP context is nil")
		}

		if !decision {
			log.Printf("Access denied by PDP")
			if httpStatus != 0 {
				http.Error(w, "Forbidden", httpStatus)
			} else {
				// Fallback if PDP does not set the status code
				http.Error(w, "Forbidden", http.StatusForbidden)
			}
			return
		}

		subjectJSON, err := json.Marshal(subjectInfo)
		if err != nil {
			log.Printf("Failed to marshal subject: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		r.Header.Set("Authorization", string(subjectJSON))
		log.Printf("Forwarding request to backend with updated Authorization header: %s", r.Header.Get("Authorization"))
		proxy.ServeHTTP(w, r)
	})

	// Wrap handler with CORS middleware
	handler := corsMiddleware(mainHandler)

	log.Println("Proxy server listening on :80")
	log.Fatal(http.ListenAndServe(":80", handler))
}

// Struct for the relevant JSON response
type OpenIDConfig struct {
	JWKSURI string `json:"jwks_uri"`
}

// Method to fetch the jwks_uri
func FetchJWKSURI(url string) (string, error) {

	resp, err := http.Get(url)
	if err != nil {
		return "", fmt.Errorf("error making HTTP request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var config OpenIDConfig
	if err := json.NewDecoder(resp.Body).Decode(&config); err != nil {
		return "", fmt.Errorf("error decoding JSON: %w", err)
	}

	return config.JWKSURI, nil
}

func validateAndExtractSubject(tokenString string, jwks keyfunc.Keyfunc) (map[string]interface{}, error) {

	// Parse and validate the JWT
	claims := jwt.MapClaims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, jwks.Keyfunc)

    fmt.Println("TOKEN:", tokenString)
    parts := strings.Split(tokenString, ".")
    fmt.Println(len(parts)) // muss 3 sein

	if err != nil {
		return nil, fmt.Errorf("invalid token: %v", err)
	}

	if !token.Valid {
		return nil, fmt.Errorf("token is invalid")
	}

	// Extract the subject data from the "subject" claim
	subjectInfo := make(map[string]interface{})
	if subject, ok := claims["subject"].(map[string]interface{}); ok {
		// Copy subject data as properties
		for key, value := range subject {
			subjectInfo[key] = value
		}
	} else {
		// Fallback: use claims directly
		for key, value := range claims {
			if key != "subject" {
				subjectInfo[key] = value
			}
		}
	}

	return subjectInfo, nil
}
func createAuthZENRequest(subjectInfo map[string]interface{}, r *http.Request) *authzen.AuthZRequest {
	// Extract subject ID - check for "id" field (since we map email to id)
	subjectID := ""
	if id, ok := subjectInfo["id"]; ok {
		subjectID = fmt.Sprintf("%v", id)
	}

	authnAuthzRequest := &authzen.AuthZRequest{
		Subject: &authzen.Subject{
			Type:       "partner",
			ID:         subjectID,
			Properties: subjectInfo,
		},
		Action: &authzen.Action{
			Name: r.Method,
		},
		Resource: &authzen.Resource{
			Type: "route",
			ID:   r.URL.String(),
		},
	}
	return authnAuthzRequest
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Max-Age", "86400")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
