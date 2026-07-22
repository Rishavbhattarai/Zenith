import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  AUTH_COOKIE,
  INGESTION_MESH_URL,
  INVENTORY_SERVICE_URL,
  NOTETAKER_URL,
} from "@/lib/backend";

async function fetchJson(url: string, init?: RequestInit) {
  const resp = await fetch(url, { ...init, cache: "no-store" });
  if (!resp.ok) throw new Error(`${url} -> ${resp.status}`);
  return resp.json();
}

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }
  const authHeaders = { Authorization: `Bearer ${token}` };

  const [assets, metrics, events, parts, reorderRequests] = await Promise.allSettled([
    fetchJson(`${INGESTION_MESH_URL}/assets`),
    fetchJson(`${INGESTION_MESH_URL}/metrics`),
    fetchJson(`${NOTETAKER_URL}/events?limit=50`),
    fetchJson(`${INVENTORY_SERVICE_URL}/parts`, { headers: authHeaders }),
    fetchJson(`${INVENTORY_SERVICE_URL}/reorder-requests`, { headers: authHeaders }),
  ]);

  const unwrap = <T,>(r: PromiseSettledResult<T>, fallback: T) =>
    r.status === "fulfilled" ? r.value : fallback;

  return NextResponse.json({
    assets: unwrap(assets, []),
    metrics: unwrap(metrics, null),
    events: unwrap(events, []),
    parts: unwrap(parts, []),
    reorderRequests: unwrap(reorderRequests, []),
    errors: [assets, metrics, events, parts, reorderRequests]
      .map((r, i) => (r.status === "rejected" ? ["assets", "metrics", "events", "parts", "reorderRequests"][i] : null))
      .filter(Boolean),
  });
}
