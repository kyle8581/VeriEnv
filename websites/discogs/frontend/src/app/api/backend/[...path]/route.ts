import { NextResponse } from "next/server";

import { backendUrl } from "@/lib/backend";

async function handler(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const url = backendUrl("/" + path.join("/"));

  // Forward headers (including Authorization), but drop host-specific ones.
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");

  const resp = await fetch(url, {
    method: req.method,
    headers,
    body: ["GET", "HEAD"].includes(req.method) ? undefined : req.body,
    // @ts-expect-error duplex is required by some runtimes for streaming bodies
    duplex: "half",
  });

  const outHeaders = new Headers(resp.headers);
  outHeaders.delete("content-encoding");
  outHeaders.delete("transfer-encoding");

  return new NextResponse(resp.body, {
    status: resp.status,
    headers: outHeaders,
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
