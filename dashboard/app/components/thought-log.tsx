import type { AgentEvent } from "@/lib/types";

const STAGE_LABEL: Record<string, string> = {
  received: "Received",
  extracted: "Extracted",
  safety_checked: "Safety check",
  inventory_recorded: "Inventory",
  complete: "Done",
  retrieval: "Retrieval",
  answered: "Answered",
};

export default function ThoughtLog({ events }: { events: AgentEvent[] }) {
  return (
    <div className="flex max-h-80 flex-col gap-2 overflow-y-auto">
      {events.map((event, i) => (
        <div key={`${event.note_id}-${event.stage}-${i}`} className="flex items-start gap-2 text-xs">
          <span className="shrink-0 tabular-nums" style={{ color: "var(--muted)" }}>
            {new Date(event.timestamp).toLocaleTimeString()}
          </span>
          <span
            className="shrink-0 rounded px-1.5 py-0.5 font-medium"
            style={{ background: "var(--gridline)", color: "var(--secondary)" }}
          >
            {STAGE_LABEL[event.stage] ?? event.stage}
          </span>
          <span className="font-mono" style={{ color: "var(--muted)" }}>
            {event.note_id}
          </span>
          <span>{event.message}</span>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No agent activity yet — submit a field note or ask the support agent a question.
        </p>
      )}
    </div>
  );
}
