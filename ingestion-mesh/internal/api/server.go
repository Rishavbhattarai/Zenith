// Package api exposes the ingestion engine's state over HTTP.
package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"zenith/ingestion-mesh/internal/ingest"
	"zenith/ingestion-mesh/internal/store"
)

// NewMux builds the HTTP routing for the ingestion service.
func NewMux(s *store.Store, p *ingest.Pipeline) *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	mux.HandleFunc("GET /assets", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, s.List())
	})

	mux.HandleFunc("GET /assets/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := strings.TrimSpace(r.PathValue("id"))
		state, ok := s.Get(id)
		if !ok {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "asset not found"})
			return
		}
		writeJSON(w, http.StatusOK, state)
	})

	mux.HandleFunc("GET /metrics", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, p.Metrics.Snapshot())
	})

	return mux
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
