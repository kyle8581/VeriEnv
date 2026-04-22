import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function GET() {
  const resp = await backendFetch("/me/collection", { method: "GET" });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

