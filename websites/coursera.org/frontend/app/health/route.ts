import { NextResponse } from "next/server";

export const runtime = "nodejs";

export function GET() {
  return NextResponse.json({
    ok: true,
    site: "coursera.org",
    service: "frontend",
    ts: new Date().toISOString(),
  });
}

