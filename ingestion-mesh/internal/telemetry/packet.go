// Package telemetry defines the JSON-RPC 2.0 telemetry packet shape and
// the validation rules the ingestion pipeline enforces on it.
package telemetry

import (
	"errors"
	"time"
)

// Metric enumerates the recognized telemetry metric kinds.
type Metric string

const (
	MetricCPUTemp        Metric = "cpu_temp"
	MetricSignalStrength Metric = "signal_strength"
	MetricPowerDraw      Metric = "power_draw"
	MetricLatency        Metric = "latency_ms"
	MetricPacketLoss     Metric = "packet_loss_pct"
)

var validMetrics = map[Metric]struct {
	min, max float64
}{
	MetricCPUTemp:        {min: -20, max: 120},
	MetricSignalStrength: {min: -120, max: 0},
	MetricPowerDraw:      {min: 0, max: 10000},
	MetricLatency:        {min: 0, max: 60000},
	MetricPacketLoss:     {min: 0, max: 100},
}

// Status enumerates the recognized asset health statuses.
type Status string

const (
	StatusNominal  Status = "nominal"
	StatusDegraded Status = "degraded"
	StatusCritical Status = "critical"
)

var validStatuses = map[Status]bool{
	StatusNominal:  true,
	StatusDegraded: true,
	StatusCritical: true,
}

// Params is the payload of a telemetry.update JSON-RPC notification.
type Params struct {
	AssetID   string    `json:"asset_id"`
	Metric    Metric    `json:"metric"`
	Value     float64   `json:"value"`
	Status    Status    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
}

// Packet is a JSON-RPC 2.0 notification carrying an asset telemetry update.
type Packet struct {
	JSONRPC string `json:"jsonrpc"`
	Method  string `json:"method"`
	Params  Params `json:"params"`
}

const telemetryMethod = "telemetry.update"

var (
	ErrBadEnvelope     = errors.New("telemetry: not a valid JSON-RPC 2.0 envelope")
	ErrUnknownMethod   = errors.New("telemetry: unrecognized method")
	ErrMissingAsset    = errors.New("telemetry: missing asset_id")
	ErrUnknownMetric   = errors.New("telemetry: unrecognized metric")
	ErrValueOutOfRange = errors.New("telemetry: value out of range for metric")
	ErrUnknownStatus   = errors.New("telemetry: unrecognized status")
	ErrBadTimestamp    = errors.New("telemetry: timestamp missing or out of sane range")
)

// Validate checks the JSON-RPC envelope and the telemetry schema. It returns
// the first violation found, or nil if the packet is well-formed.
func (p Packet) Validate(now time.Time) error {
	if p.JSONRPC != "2.0" {
		return ErrBadEnvelope
	}
	if p.Method != telemetryMethod {
		return ErrUnknownMethod
	}
	if p.Params.AssetID == "" {
		return ErrMissingAsset
	}
	bounds, ok := validMetrics[p.Params.Metric]
	if !ok {
		return ErrUnknownMetric
	}
	if p.Params.Value < bounds.min || p.Params.Value > bounds.max {
		return ErrValueOutOfRange
	}
	if !validStatuses[p.Params.Status] {
		return ErrUnknownStatus
	}
	if p.Params.Timestamp.IsZero() {
		return ErrBadTimestamp
	}
	// Reject timestamps too far in the future or absurdly stale — guards
	// against clock-skew garbage without needing wall-clock precision.
	skew := now.Sub(p.Params.Timestamp)
	if skew < -time.Minute || skew > 24*time.Hour {
		return ErrBadTimestamp
	}
	return nil
}
