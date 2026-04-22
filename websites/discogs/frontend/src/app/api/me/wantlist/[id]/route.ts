import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const resp = await backendFetch(`/me/wantlist/${id}`, { method: "POST" });
  const text = await resp.text();
  return new NextResponse(text || JSON.stringify({ ok: resp.ok }), {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function DELETE(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const resp = await backendFetch(`/me/wantlist/${id}`, { method: "DELETE" });
  const text = await resp.text();
  return new NextResponse(text || JSON.stringify({ ok: resp.ok }), {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

