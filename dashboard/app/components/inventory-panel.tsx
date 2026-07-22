import type { Part, ReorderRequest } from "@/lib/types";

export default function InventoryPanel({
  parts,
  reorderRequests,
}: {
  parts: Part[];
  reorderRequests: ReorderRequest[];
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row">
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr style={{ color: "var(--muted)" }} className="text-xs uppercase tracking-wide">
              <th className="pb-2 font-medium">Part</th>
              <th className="pb-2 font-medium">Stock</th>
              <th className="pb-2 font-medium">Threshold</th>
            </tr>
          </thead>
          <tbody>
            {parts.map((part) => {
              const low = part.stock_quantity < part.reorder_threshold;
              return (
                <tr key={part.id} style={{ borderTop: "1px solid var(--gridline)" }}>
                  <td className="py-1.5">{part.part_name}</td>
                  <td
                    className="py-1.5 tabular-nums font-medium"
                    style={{ color: low ? "var(--status-critical)" : "var(--foreground)" }}
                  >
                    {part.stock_quantity}
                    {low && " ⚠"}
                  </td>
                  <td className="py-1.5 tabular-nums" style={{ color: "var(--muted)" }}>
                    {part.reorder_threshold}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex-1">
        <table className="w-full text-left text-sm">
          <thead>
            <tr style={{ color: "var(--muted)" }} className="text-xs uppercase tracking-wide">
              <th className="pb-2 font-medium">Reorder request</th>
              <th className="pb-2 font-medium">Qty</th>
              <th className="pb-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {reorderRequests.map((r) => (
              <tr key={r.id} style={{ borderTop: "1px solid var(--gridline)" }}>
                <td className="py-1.5">{r.part_name}</td>
                <td className="py-1.5 tabular-nums">{r.quantity}</td>
                <td className="py-1.5" style={{ color: "var(--status-warning)" }}>
                  {r.status}
                </td>
              </tr>
            ))}
            {reorderRequests.length === 0 && (
              <tr>
                <td colSpan={3} className="py-2 text-sm" style={{ color: "var(--muted)" }}>
                  No pending reorder requests.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
