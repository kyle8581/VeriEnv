import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });

  const resp = await backendFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });

  const text = await resp.text();
  if (!resp.ok) {
    return new NextResponse(text, { status: resp.status });
  }
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

