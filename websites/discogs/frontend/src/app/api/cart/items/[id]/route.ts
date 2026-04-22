import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function DELETE(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const resp = await backendFetch(`/cart/items/${id}`, { method: "DELETE" });
  const text = await resp.text();
  return new NextResponse(text || JSON.stringify({ ok: resp.ok }), {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

