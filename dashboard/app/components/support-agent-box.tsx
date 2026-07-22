"use client";

import { useState } from "react";
import type { SupportAnswer } from "@/lib/types";

export default function SupportAgentBox() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<SupportAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const resp = await fetch("/api/support", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!resp.ok) throw new Error("Support agent unavailable");
      setAnswer(await resp.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about a failure mode, escalation policy, reorder logic…"
          className="flex-1 rounded-md border px-3 py-2 text-sm outline-none"
          style={{ borderColor: "var(--border)" }}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="rounded-md px-4 py-2 text-sm font-medium text-background disabled:opacity-40"
          style={{ background: "var(--foreground)" }}
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && (
        <p className="text-sm" style={{ color: "var(--status-critical)" }}>
          {error}
        </p>
      )}

      {answer && (
        <div
          className="flex flex-col gap-2 rounded-md border p-3 text-sm"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}
        >
          <p className="whitespace-pre-wrap">{answer.answer}</p>
          {answer.sources.length > 0 && (
            <p className="text-xs" style={{ color: "var(--muted)" }}>
              Sources: {answer.sources.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
