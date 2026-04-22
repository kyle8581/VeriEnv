import { NextResponse } from "next/server";

import { backendFetch, COOKIE_NAME } from "@/lib/backend";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });

  const resp = await backendFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

  const text = await resp.text();
  if (!resp.ok) {
    return new NextResponse(text, { status: resp.status });
  }

  const data = JSON.parse(text) as { access_token: string; token_type: string };

  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE_NAME, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
  });
  return res;
}

