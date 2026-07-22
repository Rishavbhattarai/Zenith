// Package ingest implements the fault-tolerant worker pool that consumes
// raw telemetry packets, validates them, and applies valid ones to the
// asset store. Malformed input is counted and dropped rather than allowed
// to crash a worker.
package ingest

import (
	"context"
	"sync"
	"sync/atomic"
	"time"

	"zenith/ingestion-mesh/internal/store"
	"zenith/ingestion-mesh/internal/telemetry"
)

// Metrics tracks pipeline throughput and error counts using atomics so it
// can be read concurrently without locking.
type Metrics struct {
	Received atomic.Uint64
	Valid    atomic.Uint64
	Invalid  atomic.Uint64
	Dropped  atomic.Uint64 // ingress channel was full
}

// Snapshot is a point-in-time, JSON-friendly view of Metrics.
type Snapshot struct {
	Received uint64 `json:"received"`
	Valid    uint64 `json:"valid"`
	Invalid  uint64 `json:"invalid"`
	Dropped  uint64 `json:"dropped"`
}

func (m *Metrics) Snapshot() Snapshot {
	return Snapshot{
		Received: m.Received.Load(),
		Valid:    m.Valid.Load(),
		Invalid:  m.Invalid.Load(),
		Dropped:  m.Dropped.Load(),
	}
}

// DeadLetter is a packet (raw bytes-equivalent struct here) that failed
// validation, kept for inspection/debugging.
type DeadLetter struct {
	Packet telemetry.Packet
	Err    error
}

// Pipeline is a fixed-size worker pool that drains an ingress channel of
// telemetry packets, validates each one, and applies valid packets to the
// store. It never blocks indefinitely and never crashes on bad input.
type Pipeline struct {
	Ingress    chan telemetry.Packet
	DeadLetter chan DeadLetter
	Metrics    *Metrics
	store      *store.Store
	workers    int
}

// New creates a Pipeline with the given worker count and ingress buffer
// size. deadLetterBuf bounds how many invalid packets are retained for
// inspection before older ones are dropped.
func New(s *store.Store, workers, ingressBuf, deadLetterBuf int) *Pipeline {
	return &Pipeline{
		Ingress:    make(chan telemetry.Packet, ingressBuf),
		DeadLetter: make(chan DeadLetter, deadLetterBuf),
		Metrics:    &Metrics{},
		store:      s,
		workers:    workers,
	}
}

// Send offers a packet to the pipeline without blocking. If the ingress
// channel is full (the pipeline can't keep up with the producer), the
// packet is dropped and counted rather than stalling the caller.
func (p *Pipeline) Send(pkt telemetry.Packet) {
	p.Metrics.Received.Add(1)
	select {
	case p.Ingress <- pkt:
	default:
		p.Metrics.Dropped.Add(1)
	}
}

// Run starts the worker pool and blocks until ctx is canceled and all
// in-flight work has drained.
func (p *Pipeline) Run(ctx context.Context) {
	var wg sync.WaitGroup
	wg.Add(p.workers)
	for i := 0; i < p.workers; i++ {
		go func() {
			defer wg.Done()
			p.worker(ctx)
		}()
	}
	<-ctx.Done()
	wg.Wait()
}

func (p *Pipeline) worker(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			// Drain any remaining buffered packets before exiting so a
			// shutdown doesn't silently discard work already accepted.
			for {
				select {
				case pkt := <-p.Ingress:
					p.process(pkt)
				default:
					return
				}
			}
		case pkt := <-p.Ingress:
			p.process(pkt)
		}
	}
}

func (p *Pipeline) process(pkt telemetry.Packet) {
	if err := pkt.Validate(time.Now()); err != nil {
		p.Metrics.Invalid.Add(1)
		select {
		case p.DeadLetter <- DeadLetter{Packet: pkt, Err: err}:
		default:
			// Dead-letter buffer full; oldest diagnostics are less
			// important than keeping the worker unblocked.
		}
		return
	}
	p.Metrics.Valid.Add(1)
	p.store.Apply(pkt.Params)
}
