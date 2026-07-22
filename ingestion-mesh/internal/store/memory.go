// Package store holds the current in-memory asset state, keyed by asset ID.
// It will be superseded by the Postgres-backed store in Phase 3, but the
// interface (Apply/Get/List) is designed to carry over.
package store

import (
	"sync"

	"zenith/ingestion-mesh/internal/telemetry"
)

// historyLimit bounds the ring buffer of recent readings kept per asset.
const historyLimit = 20

// AssetState is the latest known snapshot of an asset plus recent history.
type AssetState struct {
	AssetID string             `json:"asset_id"`
	Latest  telemetry.Params   `json:"latest"`
	History []telemetry.Params `json:"history"`
}

// Store is a concurrent-safe in-memory table of asset states.
type Store struct {
	mu     sync.RWMutex
	assets map[string]*AssetState
}

func New() *Store {
	return &Store{assets: make(map[string]*AssetState)}
}

// Apply records a validated telemetry reading against its asset.
func (s *Store) Apply(p telemetry.Params) {
	s.mu.Lock()
	defer s.mu.Unlock()

	state, ok := s.assets[p.AssetID]
	if !ok {
		state = &AssetState{AssetID: p.AssetID}
		s.assets[p.AssetID] = state
	}
	state.Latest = p
	state.History = append(state.History, p)
	if len(state.History) > historyLimit {
		state.History = state.History[len(state.History)-historyLimit:]
	}
}

// Get returns a copy of a single asset's state.
func (s *Store) Get(assetID string) (AssetState, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	state, ok := s.assets[assetID]
	if !ok {
		return AssetState{}, false
	}
	return *state, true
}

// List returns a snapshot of all known asset states.
func (s *Store) List() []AssetState {
	s.mu.RLock()
	defer s.mu.RUnlock()

	out := make([]AssetState, 0, len(s.assets))
	for _, state := range s.assets {
		out = append(out, *state)
	}
	return out
}
