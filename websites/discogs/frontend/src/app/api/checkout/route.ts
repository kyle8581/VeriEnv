import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST() {
  const resp = await backendFetch("/checkout", { method: "POST" });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  });
}

