package telemetry

import (
	"testing"
	"time"
)

func validPacket(now time.Time) Packet {
	return Packet{
		JSONRPC: "2.0",
		Method:  telemetryMethod,
		Params: Params{
			AssetID:   "asset-1",
			Metric:    MetricCPUTemp,
			Value:     42.0,
			Status:    StatusNominal,
			Timestamp: now,
		},
	}
}

func TestValidate_ValidPacket(t *testing.T) {
	now := time.Now()
	if err := validPacket(now).Validate(now); err != nil {
		t.Fatalf("expected valid packet to pass, got %v", err)
	}
}

func TestValidate_Cases(t *testing.T) {
	now := time.Now()

	cases := []struct {
		name    string
		mutate  func(p Packet) Packet
		wantErr error
	}{
		{"bad envelope", func(p Packet) Packet { p.JSONRPC = "1.0"; return p }, ErrBadEnvelope},
		{"unknown method", func(p Packet) Packet { p.Method = "unknown"; return p }, ErrUnknownMethod},
		{"missing asset", func(p Packet) Packet { p.Params.AssetID = ""; return p }, ErrMissingAsset},
		{"unknown metric", func(p Packet) Packet { p.Params.Metric = "bogus"; return p }, ErrUnknownMetric},
		{"value out of range", func(p Packet) Packet { p.Params.Value = 999999; return p }, ErrValueOutOfRange},
		{"unknown status", func(p Packet) Packet { p.Params.Status = "bogus"; return p }, ErrUnknownStatus},
		{"zero timestamp", func(p Packet) Packet { p.Params.Timestamp = time.Time{}; return p }, ErrBadTimestamp},
		{"future skew", func(p Packet) Packet { p.Params.Timestamp = now.Add(time.Hour); return p }, ErrBadTimestamp},
		{"stale timestamp", func(p Packet) Packet { p.Params.Timestamp = now.Add(-48 * time.Hour); return p }, ErrBadTimestamp},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			p := tc.mutate(validPacket(now))
			err := p.Validate(now)
			if err != tc.wantErr {
				t.Fatalf("got %v, want %v", err, tc.wantErr)
			}
		})
	}
}
