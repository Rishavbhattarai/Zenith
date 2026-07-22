const STATUS_STYLE: Record<string, { color: string; label: string }> = {
  nominal: { color: "var(--status-good)", label: "Nominal" },
  degraded: { color: "var(--status-warning)", label: "Degraded" },
  critical: { color: "var(--status-critical)", label: "Critical" },
};

export default function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLE[status] ?? { color: "var(--muted)", label: status };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium">
      <span
        aria-hidden
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ background: style.color }}
      />
      {style.label}
    </span>
  );
}
