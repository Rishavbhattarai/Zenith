import { NextResponse } from "next/server";
import { NOTETAKER_URL } from "@/lib/backend";

export async function POST(request: Request) {
  const body = await request.json();

  const resp = await fetch(`${NOTETAKER_URL}/support/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    return NextResponse.json({ error: "Support agent unavailable" }, { status: 502 });
  }

  return NextResponse.json(await resp.json());
}
