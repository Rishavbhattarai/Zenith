// Package simulator generates synthetic telemetry to stand in for real
// satellite ground station / data center node feeds during development.
package simulator

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"zenith/ingestion-mesh/internal/telemetry"
)

// Sink is anything that can accept a produced packet without blocking the
// caller indefinitely (the ingest.Pipeline satisfies this via Send).
type Sink interface {
	Send(telemetry.Packet)
}

var metrics = []telemetry.Metric{
	telemetry.MetricCPUTemp,
	telemetry.MetricSignalStrength,
	telemetry.MetricPowerDraw,
	telemetry.MetricLatency,
	telemetry.MetricPacketLoss,
}

var metricRange = map[telemetry.Metric][2]float64{
	telemetry.MetricCPUTemp:        {30, 90},
	telemetry.MetricSignalStrength: {-90, -30},
	telemetry.MetricPowerDraw:      {100, 4000},
	telemetry.MetricLatency:        {5, 300},
	telemetry.MetricPacketLoss:     {0, 5},
}

// Config controls simulation volume and fault injection rate.
type Config struct {
	NumAssets      int
	TickInterval   time.Duration
	MalformedRatio float64 // fraction in [0,1) of packets that are deliberately invalid
}

func DefaultConfig() Config {
	return Config{
		NumAssets:      2000,
		TickInterval:   50 * time.Millisecond,
		MalformedRatio: 0.015,
	}
}

// Run spins up one goroutine per simulated asset, each emitting telemetry
// on a jittered ticker until ctx is canceled.
func Run(ctx context.Context, cfg Config, sink Sink) {
	var wg sync.WaitGroup
	wg.Add(cfg.NumAssets)
	for i := 0; i < cfg.NumAssets; i++ {
		assetID := fmt.Sprintf("asset-%04d", i)
		go func(assetID string) {
			defer wg.Done()
			runAsset(ctx, assetID, cfg, sink)
		}(assetID)
	}
	wg.Wait()
}

func runAsset(ctx context.Context, assetID string, cfg Config, sink Sink) {
	rng := rand.New(rand.NewSource(time.Now().UnixNano() ^ int64(len(assetID))))
	jitter := time.Duration(rng.Int63n(int64(cfg.TickInterval)))
	timer := time.NewTimer(jitter)
	defer timer.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-timer.C:
			sink.Send(nextPacket(rng, assetID, cfg))
			timer.Reset(cfg.TickInterval)
		}
	}
}

func nextPacket(rng *rand.Rand, assetID string, cfg Config) telemetry.Packet {
	if rng.Float64() < cfg.MalformedRatio {
		return malformedPacket(rng, assetID)
	}

	metric := metrics[rng.Intn(len(metrics))]
	bounds := metricRange[metric]
	value := bounds[0] + rng.Float64()*(bounds[1]-bounds[0])

	status := telemetry.StatusNominal
	switch {
	case value > bounds[0]+0.9*(bounds[1]-bounds[0]):
		status = telemetry.StatusCritical
	case value > bounds[0]+0.7*(bounds[1]-bounds[0]):
		status = telemetry.StatusDegraded
	}

	return telemetry.Packet{
		JSONRPC: "2.0",
		Method:  "telemetry.update",
		Params: telemetry.Params{
			AssetID:   assetID,
			Metric:    metric,
			Value:     value,
			Status:    status,
			Timestamp: time.Now(),
		},
	}
}

// malformedPacket deliberately produces a packet that fails validation, to
// exercise the pipeline's fault-tolerance path.
func malformedPacket(rng *rand.Rand, assetID string) telemetry.Packet {
	switch rng.Intn(4) {
	case 0:
		return telemetry.Packet{JSONRPC: "1.0", Method: "telemetry.update"}
	case 1:
		return telemetry.Packet{JSONRPC: "2.0", Method: "unknown.method"}
	case 2:
		return telemetry.Packet{
			JSONRPC: "2.0",
			Method:  "telemetry.update",
			Params: telemetry.Params{
				AssetID:   assetID,
				Metric:    telemetry.MetricCPUTemp,
				Value:     99999,
				Status:    telemetry.StatusNominal,
				Timestamp: time.Now(),
			},
		}
	default:
		return telemetry.Packet{
			JSONRPC: "2.0",
			Method:  "telemetry.update",
			Params: telemetry.Params{
				AssetID: assetID,
				Metric:  telemetry.MetricCPUTemp,
				Value:   50,
				Status:  telemetry.StatusNominal,
				// zero Timestamp -> fails validation
			},
		}
	}
}
