// Command ingestor runs the Zenith telemetry ingestion mesh: it simulates
// asset telemetry, validates and ingests it through a worker pool, and
// serves the resulting state over HTTP.
package main

import (
	"context"
	"log"
	"net/http"
	"os/signal"
	"runtime"
	"syscall"
	"time"

	"zenith/ingestion-mesh/internal/api"
	"zenith/ingestion-mesh/internal/ingest"
	"zenith/ingestion-mesh/internal/simulator"
	"zenith/ingestion-mesh/internal/store"
)

const (
	addr          = ":8080"
	ingressBuf    = 10_000
	deadLetterBuf = 1_000
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	s := store.New()
	pipeline := ingest.New(s, runtime.NumCPU(), ingressBuf, deadLetterBuf)

	go func() {
		for dl := range pipeline.DeadLetter {
			log.Printf("dead-letter: asset=%s err=%v", dl.Packet.Params.AssetID, dl.Err)
		}
	}()

	go pipeline.Run(ctx)
	go simulator.Run(ctx, simulator.DefaultConfig(), pipeline)
	go logThroughput(ctx, pipeline)

	srv := &http.Server{Addr: addr, Handler: api.NewMux(s, pipeline)}
	go func() {
		log.Printf("ingestion mesh listening on %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("http server error: %v", err)
		}
	}()

	<-ctx.Done()
	log.Println("shutting down...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Printf("http shutdown error: %v", err)
	}
}

func logThroughput(ctx context.Context, p *ingest.Pipeline) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	var lastValid uint64
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			snap := p.Metrics.Snapshot()
			rate := float64(snap.Valid-lastValid) / 5.0
			lastValid = snap.Valid
			log.Printf("throughput: %.0f packets/sec valid=%d invalid=%d dropped=%d",
				rate, snap.Valid, snap.Invalid, snap.Dropped)
		}
	}
}
