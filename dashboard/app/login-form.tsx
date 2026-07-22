"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!resp.ok) {
        throw new Error("Invalid username or password");
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-lg border p-6"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div>
          <h1 className="text-lg font-semibold">Zenith Command Center</h1>
          <p className="text-sm" style={{ color: "var(--secondary)" }}>
            Sign in to view live telemetry, agent activity, and inventory.
          </p>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Username</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded-md border px-3 py-2 text-sm outline-none"
            style={{ borderColor: "var(--border)" }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border px-3 py-2 text-sm outline-none"
            style={{ borderColor: "var(--border)" }}
          />
        </label>

        {error && (
          <p className="text-sm" style={{ color: "var(--status-critical)" }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md px-4 py-2 text-sm font-medium text-background disabled:opacity-40"
          style={{ background: "var(--foreground)" }}
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>

        <p className="text-xs" style={{ color: "var(--muted)" }}>
          Demo credentials: admin / admin-demo-pw
        </p>
      </form>
    </div>
  );
}
