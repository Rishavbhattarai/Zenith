import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { AUTH_COOKIE, INVENTORY_SERVICE_URL } from "@/lib/backend";

export async function POST(request: Request) {
  const body = await request.json();

  const resp = await fetch(`${INVENTORY_SERVICE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
  }

  const { access_token, role } = await resp.json();

  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE, access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24,
  });

  return NextResponse.json({ role });
}
