package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
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

		// Expects: { "result": ... }
		var envelope struct {
			Result json.RawMessage `json:"result"`
		}

		if err := json.Unmarshal(body, &envelope); err != nil {
			// If no result: Redirect original message
			resp.Body = io.NopCloser(bytes.NewBuffer(body))
			return nil
		}

		resp.Body = io.NopCloser(bytes.NewBuffer(envelope.Result))
		resp.ContentLength = int64(len(envelope.Result))
		resp.Header.Set("Content-Type", "application/json")
		resp.Header.Del("Content-Encoding")

		return nil
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Println(r.Method, r.URL.Path)
		proxy.ServeHTTP(w, r)
	})

	log.Fatal(http.ListenAndServe(":8484", nil))
}

