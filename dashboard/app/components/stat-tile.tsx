export default function StatTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div
      className="flex flex-col gap-1 rounded-lg border p-4"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <span className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--muted)" }}>
        {label}
      </span>
      <span className="text-2xl font-semibold tabular-nums" style={{ color: accent ?? "var(--foreground)" }}>
        {value}
      </span>
    </div>
  );
}
