"use client";

import { useEffect, useRef, useState } from "react";

type PartUsed = { part_name: string; quantity: number };
type TelemetryAnnotation = {
  asset_id: string;
  claimed_status: string;
  notes: string;
};
type FieldNoteExtraction = {
  note_type: "site_report" | "failure_postmortem" | "general";
  summary: string;
  action_items: string[];
  parts_used: PartUsed[];
  telemetry_annotations: TelemetryAnnotation[];
};
type SafetyCheckResult = { ok: boolean; warnings: string[] };
type NoteProcessingResult = {
  extraction: FieldNoteExtraction;
  safety: SafetyCheckResult;
};

const NOTETAKER_URL =
  process.env.NEXT_PUBLIC_NOTETAKER_URL ?? "http://localhost:8000";

const NOTE_TYPE_LABEL: Record<FieldNoteExtraction["note_type"], string> = {
  site_report: "Site report",
  failure_postmortem: "Failure post-mortem",
  general: "General note",
};

export default function FieldNoteForm() {
  const [assetId, setAssetId] = useState("");
  const [rawText, setRawText] = useState("");
  const [listening, setListening] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<NoteProcessingResult | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Computed post-mount only: `window` is unavailable during SSR, and
  // branching on it during render causes a client/server hydration mismatch.
  const [speechSupported, setSpeechSupported] = useState(false);
  useEffect(() => {
    setSpeechSupported(
      "SpeechRecognition" in window || "webkitSpeechRecognition" in window
    );
  }, []);

  function toggleListening() {
    if (!speechSupported) return;

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    const SpeechRecognitionImpl =
      window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SpeechRecognitionImpl) return;
    const recognition = new SpeechRecognitionImpl();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setRawText((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rawText.trim()) return;

    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${NOTETAKER_URL}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_text: rawText,
          asset_id: assetId.trim() || null,
        }),
      });
      if (!res.ok) {
        throw new Error(`Notetaker service returned ${res.status}`);
      }
      const data: NoteProcessingResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't reach the notetaker service."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-8">
      <header>
        <h1 className="text-xl font-semibold">Zenith Field Note</h1>
        <p className="text-sm text-foreground/60">
          Log a repair or inspection. We&apos;ll extract action items, parts
          used, and check your notes against live telemetry.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Asset ID (optional)</span>
          <input
            type="text"
            value={assetId}
            onChange={(e) => setAssetId(e.target.value)}
            placeholder="asset-0042"
            className="rounded-lg border border-foreground/20 bg-transparent px-3 py-3 text-base outline-none focus:border-foreground/50"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Note</span>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={6}
            placeholder="Replaced the power supply, running fine now..."
            className="rounded-lg border border-foreground/20 bg-transparent px-3 py-3 text-base outline-none focus:border-foreground/50"
          />
        </label>

        {speechSupported && (
          <button
            type="button"
            onClick={toggleListening}
            className={`rounded-lg border px-4 py-3 text-sm font-medium transition ${
              listening
                ? "border-red-500 bg-red-500/10 text-red-500"
                : "border-foreground/20 text-foreground/80"
            }`}
          >
            {listening ? "● Listening… tap to stop" : "🎙️ Dictate note"}
          </button>
        )}

        <button
          type="submit"
          disabled={submitting || !rawText.trim()}
          className="rounded-lg bg-foreground px-4 py-3 text-base font-medium text-background disabled:opacity-40"
        >
          {submitting ? "Processing…" : "Submit note"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error}
        </div>
      )}

      {result && <ResultView result={result} />}
    </div>
  );
}

function ResultView({ result }: { result: NoteProcessingResult }) {
  const { extraction, safety } = result;

  return (
    <div className="flex flex-col gap-4">
      {!safety.ok && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3">
          <p className="text-sm font-semibold text-red-500">
            ⚠ Telemetry contradiction detected
          </p>
          <ul className="mt-1 list-disc pl-5 text-sm text-red-500/90">
            {safety.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      {safety.ok && extraction.telemetry_annotations.length > 0 && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-500">
          ✓ Consistent with live telemetry
        </div>
      )}

      <section className="rounded-lg border border-foreground/15 px-4 py-3">
        <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">
          {NOTE_TYPE_LABEL[extraction.note_type]}
        </p>
        <p className="mt-1 text-sm">{extraction.summary}</p>
      </section>

      {extraction.action_items.length > 0 && (
        <Section title="Action items">
          <ul className="list-disc pl-5 text-sm">
            {extraction.action_items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </Section>
      )}

      {extraction.parts_used.length > 0 && (
        <Section title="Parts used">
          <ul className="list-disc pl-5 text-sm">
            {extraction.parts_used.map((p, i) => (
              <li key={i}>
                {p.part_name} × {p.quantity}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {extraction.telemetry_annotations.length > 0 && (
        <Section title="Telemetry claims">
          <ul className="flex flex-col gap-1 text-sm">
            {extraction.telemetry_annotations.map((a, i) => (
              <li key={i}>
                <span className="font-mono text-foreground/70">
                  {a.asset_id}
                </span>{" "}
                — claimed <span className="font-medium">{a.claimed_status}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-foreground/15 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">
        {title}
      </p>
      <div className="mt-2">{children}</div>
    </section>
  );
}
