import type { AssetState } from "@/lib/types";
import StatusBadge from "./status-badge";

const DISPLAY_CAP = 40;

export default function NodeGrid({ assets }: { assets: AssetState[] }) {
  // The Phase 1 simulator runs thousands of assets by design (to
  // demonstrate high-volume ingestion) -- rendering all of them as cards
  // would overwhelm the grid, so prioritize non-nominal nodes and cap the
  // total shown. Stat tiles above still reflect the full set.
  const sorted = [...assets].sort((a, b) => {
    const rank = (s?: string) => (s === "critical" ? 0 : s === "degraded" ? 1 : 2);
    const byStatus = rank(a.latest?.status) - rank(b.latest?.status);
    return byStatus !== 0 ? byStatus : a.asset_id.localeCompare(b.asset_id);
  });
  const shown = sorted.slice(0, DISPLAY_CAP);

  return (
    <div className="flex flex-col gap-2">
      {assets.length > DISPLAY_CAP && (
        <p className="text-xs" style={{ color: "var(--muted)" }}>
          Showing {DISPLAY_CAP} of {assets.length} assets (critical/degraded prioritized).
        </p>
      )}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
        {shown.map((asset) => (
          <div
            key={asset.asset_id}
            className="flex flex-col gap-1 rounded-md border p-3"
            style={{ borderColor: "var(--border)", background: "var(--surface)" }}
          >
            <span className="font-mono text-xs" style={{ color: "var(--secondary)" }}>
              {asset.asset_id}
            </span>
            <StatusBadge status={asset.latest?.status ?? "unknown"} />
            {asset.latest && (
              <span className="text-xs tabular-nums" style={{ color: "var(--muted)" }}>
                {asset.latest.metric}: {asset.latest.value.toFixed(1)}
              </span>
            )}
          </div>
        ))}
        {sorted.length === 0 && (
          <p className="col-span-full text-sm" style={{ color: "var(--muted)" }}>
            No asset telemetry yet.
          </p>
        )}
      </div>
    </div>
  );
}
