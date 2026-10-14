package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
    "strconv"
)

func main() {
	remote, err := url.Parse("http://opa:8181")
	if err != nil {
		panic(err)
	}

	proxy := httputil.NewSingleHostReverseProxy(remote)

	// REQUEST: POST -> { "input": ... }
	originalDirector := proxy.Director
	proxy.Director = func(r *http.Request) {
		originalDirector(r)

		if r.Method == http.MethodPost && r.Body != nil {
			body, err := io.ReadAll(r.Body)
            r.Body.Close()
			if err != nil {
				log.Println("request read error:", err)
				return
			}

			wrapped := map[string]json.RawMessage{
				"input": json.RawMessage(body),
			}

			newBody, _ := json.Marshal(wrapped)

			r.Body = io.NopCloser(bytes.NewBuffer(newBody))
			r.ContentLength = int64(len(newBody))
			r.Header.Set("Content-Type", "application/json")
		}
	}

	// RESPONSE: { "result": X } -> X
    proxy.ModifyResponse = func(resp *http.Response) error {
	    if resp.Body == nil {
	    	return nil
	    }

	    body, err := io.ReadAll(resp.Body)
	    if err != nil {
	    	return err
	    }
	    resp.Body.Close()

	    var envelope struct {
	    	Result json.RawMessage `json:"result"`
	    }

	    if err := json.Unmarshal(body, &envelope); err != nil {
	    	resp.Body = io.NopCloser(bytes.NewBuffer(body))
	    	resp.ContentLength = int64(len(body))
	    	resp.Header.Set("Content-Length", strconv.Itoa(len(body)))
	    	return nil
	    }

	    newBody := envelope.Result

	    resp.Body = io.NopCloser(bytes.NewBuffer(newBody))
	    resp.ContentLength = int64(len(newBody))
	    resp.Header.Set("Content-Length", strconv.Itoa(len(newBody)))
	    resp.Header.Set("Content-Type", "application/json")
	    resp.Header.Del("Content-Encoding")

	    return nil
    }
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Println(r.Method, r.URL.Path)
		proxy.ServeHTTP(w, r)
	})

	log.Fatal(http.ListenAndServe(":8282", nil))
}

