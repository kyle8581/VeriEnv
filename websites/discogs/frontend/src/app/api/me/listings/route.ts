import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function GET() {
  const resp = await backendFetch("/me/listings", { method: "GET" });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });

  const resp = await backendFetch("/me/listings", {
    method: "POST",
    body: JSON.stringify(body),
  });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

