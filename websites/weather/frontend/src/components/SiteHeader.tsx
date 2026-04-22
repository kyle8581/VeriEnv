"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { apiGet } from "@/lib/api";

type LocationSuggestion = {
  name: string;
  state: string | null;
  country: string;
  zip_code: string | null;
  slug: string;
};

const NAV = [
  { label: "Today", href: "/today" },
  { label: "Hourly", href: "/hourly" },
  { label: "10 Day", href: "/tenday" },
  { label: "Radar", href: "/radar" },
  { label: "Video", href: "/video" },
  { label: "More Forecasts", href: "/forecasts" },
];

export function SiteHeader() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<LocationSuggestion[]>([]);
  const blurTimer = useRef<number | null>(null);

  const canSearch = useMemo(() => q.trim().length >= 2, [q]);

  useEffect(() => {
    if (!canSearch) {
      setItems([]);
      return;
    }

    const t = window.setTimeout(async () => {
      setLoading(true);
      try {
        const res = await apiGet<LocationSuggestion[]>(
          `/locations/search?q=${encodeURIComponent(q.trim())}&limit=8`,
        );
        setItems(res);
        setOpen(true);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }, 150);

    return () => window.clearTimeout(t);
  }, [q, canSearch]);

  return (
    <header className="w-full bg-[#0b5672] text-white shadow-[0_2px_12px_rgba(0,0,0,0.2)]">
      <div className="mx-auto flex w-full max-w-[1120px] items-center gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-7 w-7 rounded bg-white/15" aria-hidden />
          <div className="leading-tight">
            <div className="text-sm font-semibold tracking-tight">
              The Weather
            </div>
            <div className="-mt-0.5 text-sm font-semibold tracking-tight">
              Channel
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-5 text-sm font-semibold md:flex">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="rounded px-1 py-1 text-white/90 hover:text-white"
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div className="relative ml-auto w-full max-w-[360px]">
          <div className="relative">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onFocus={() => setOpen(true)}
              onBlur={() => {
                if (blurTimer.current) window.clearTimeout(blurTimer.current);
                blurTimer.current = window.setTimeout(() => setOpen(false), 120);
              }}
              placeholder="Search City or Zip Code"
              className="w-full rounded-md bg-white px-3 py-2 pr-10 text-sm text-[#0b1f2a] outline-none ring-1 ring-black/10 placeholder:text-black/45 focus:ring-2 focus:ring-white/40"
            />
            <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center text-[11px] font-semibold text-black/45">
              {loading ? "…" : "Search"}
            </div>
          </div>

          {open && items.length > 0 ? (
            <div className="absolute left-0 right-0 top-[44px] z-50 overflow-hidden rounded-md border border-black/10 bg-white text-[#0b1f2a] shadow-xl">
              {items.map((it) => (
                <Link
                  key={it.slug}
                  href={`/weather/${it.slug}`}
                  className="flex items-center justify-between px-3 py-2 text-sm hover:bg-black/[0.04]"
                  onMouseDown={(e) => e.preventDefault()}
                >
                  <span className="font-medium">
                    {it.name}
                    {it.state ? `, ${it.state}` : ""}
                  </span>
                  <span className="text-xs text-black/50">
                    {it.zip_code ?? it.country}
                  </span>
                </Link>
              ))}
            </div>
          ) : null}
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <Link
            href="/account/sign-in"
            className="whitespace-nowrap rounded px-2 py-1 text-sm font-semibold text-white/90 hover:text-white"
          >
            Sign In
          </Link>
          <Link
            href="/subscribe"
            className="whitespace-nowrap rounded-full bg-white px-3 py-1.5 text-sm font-semibold text-[#0b5672] hover:bg-white/95"
          >
            Subscribe
          </Link>
        </div>
      </div>

      <div className="mx-auto w-full max-w-[1120px] px-4 pb-2 md:hidden">
        <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-white/90">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className="hover:text-white">
              {n.label}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}

