package ingest

import (
	"context"
	"testing"
	"time"

	"zenith/ingestion-mesh/internal/store"
	"zenith/ingestion-mesh/internal/telemetry"
)

func TestPipeline_ValidAndInvalidPackets(t *testing.T) {
	s := store.New()
	p := New(s, 4, 100, 100)

	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan struct{})
	go func() {
		p.Run(ctx)
		close(done)
	}()

	now := time.Now()
	valid := telemetry.Packet{
		JSONRPC: "2.0",
		Method:  "telemetry.update",
		Params: telemetry.Params{
			AssetID:   "asset-1",
			Metric:    telemetry.MetricCPUTemp,
			Value:     55,
			Status:    telemetry.StatusNominal,
			Timestamp: now,
		},
	}
	invalid := telemetry.Packet{JSONRPC: "1.0"}

	const numValid = 50
	const numInvalid = 25
	for i := 0; i < numValid; i++ {
		p.Send(valid)
	}
	for i := 0; i < numInvalid; i++ {
		p.Send(invalid)
	}

	deadline := time.After(2 * time.Second)
	for {
		snap := p.Metrics.Snapshot()
		if snap.Valid == numValid && snap.Invalid == numInvalid {
			break
		}
		select {
		case <-deadline:
			t.Fatalf("timed out waiting for metrics, got %+v", snap)
		case <-time.After(10 * time.Millisecond):
		}
	}

	cancel()
	<-done

	if state, ok := s.Get("asset-1"); !ok || state.Latest.Value != 55 {
		t.Fatalf("expected asset-1 state to be recorded, got %+v ok=%v", state, ok)
	}
}

func TestPipeline_SendDropsWhenFull(t *testing.T) {
	s := store.New()
	p := New(s, 0, 1, 1) // no workers draining, buffer size 1

	pkt := telemetry.Packet{JSONRPC: "2.0"}
	p.Send(pkt) // fills the buffer
	p.Send(pkt) // should be dropped

	snap := p.Metrics.Snapshot()
	if snap.Received != 2 {
		t.Fatalf("expected 2 received, got %d", snap.Received)
	}
	if snap.Dropped != 1 {
		t.Fatalf("expected 1 dropped, got %d", snap.Dropped)
	}
}
