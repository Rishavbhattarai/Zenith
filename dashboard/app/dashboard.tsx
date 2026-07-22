"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { DashboardData } from "@/lib/types";
import StatTile from "./components/stat-tile";
import NodeGrid from "./components/node-grid";
import ThoughtLog from "./components/thought-log";
import InventoryPanel from "./components/inventory-panel";
import SupportAgentBox from "./components/support-agent-box";

const POLL_INTERVAL_MS = 3000;

export default function Dashboard() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loggedOut, setLoggedOut] = useState(false);

  const poll = useCallback(async () => {
    const resp = await fetch("/api/dashboard-data", { cache: "no-store" });
    if (resp.status === 401) {
      setLoggedOut(true);
      return;
    }
    setData(await resp.json());
  }, []);

  useEffect(() => {
    // Intentional fetch-on-mount + poll; setState happens inside `poll`
    // after an await, not synchronously in the effect body.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [poll]);

  useEffect(() => {
    if (loggedOut) router.refresh();
  }, [loggedOut, router]);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.refresh();
  }

  if (loggedOut) {
    return null;
  }

  const counts = { nominal: 0, degraded: 0, critical: 0 };
  for (const asset of data?.assets ?? []) {
    const status = asset.latest?.status;
    if (status && status in counts) counts[status as keyof typeof counts]++;
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Zenith Command Center</h1>
          <p className="text-sm" style={{ color: "var(--secondary)" }}>
            Live telemetry, agent activity, and inventory across the mesh.
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-md border px-3 py-1.5 text-sm"
          style={{ borderColor: "var(--border)" }}
        >
          Sign out
        </button>
      </header>

      {data && data.errors.length > 0 && (
        <div
          className="rounded-md border p-3 text-sm"
          style={{ borderColor: "var(--status-warning)", color: "var(--status-warning)" }}
        >
          Some data sources are unavailable: {data.errors.join(", ")}
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Assets" value={data?.assets.length ?? "—"} />
        <StatTile label="Nominal" value={counts.nominal} accent="var(--status-good)" />
        <StatTile label="Degraded" value={counts.degraded} accent="var(--status-warning)" />
        <StatTile label="Critical" value={counts.critical} accent="var(--status-critical)" />
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold">Node Health</h2>
        <NodeGrid assets={data?.assets ?? []} />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-2 text-sm font-semibold">Agent Thought Log</h2>
          <ThoughtLog events={data?.events ?? []} />
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold">Support Agent</h2>
          <SupportAgentBox />
        </section>
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold">Inventory &amp; Reorders</h2>
        <InventoryPanel parts={data?.parts ?? []} reorderRequests={data?.reorderRequests ?? []} />
      </section>
    </div>
  );
}
