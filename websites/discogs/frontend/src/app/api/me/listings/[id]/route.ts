import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function PATCH(
  req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });

  const resp = await backendFetch(`/me/listings/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function DELETE(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const resp = await backendFetch(`/me/listings/${id}`, { method: "DELETE" });
  const text = await resp.text();
  return new NextResponse(text || JSON.stringify({ ok: resp.ok }), {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

