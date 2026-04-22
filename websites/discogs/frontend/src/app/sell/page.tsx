"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { ReleaseCard as ReleaseCardType } from "@/lib/types";

export const dynamic = "force-dynamic";

type MyListing = {
  id: number;
  release_id: number;
  release_title: string;
  media_condition: string;
  sleeve_condition: string;
  price_cents: number;
  currency: string;
  ships_from: string;
  quantity: number;
  status: string;
  created_at: string;
};

function money(cents: number, currency: string) {
  return `${currency} ${(cents / 100).toFixed(2)}`;
}

export default function SellPage() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<ReleaseCardType[]>([]);
  const [selected, setSelected] = useState<ReleaseCardType | null>(null);

  const [mediaCondition, setMediaCondition] = useState("Near Mint (NM or M-)");
  const [sleeveCondition, setSleeveCondition] = useState("Very Good Plus (VG+)");
  const [shipsFrom, setShipsFrom] = useState("US");
  const [price, setPrice] = useState("1999");
  const [qty, setQty] = useState("1");
  const [comments, setComments] = useState("Fast shipping. Stored safely.");

  const [listings, setListings] = useState<MyListing[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const priceCents = useMemo(() => Number(price || "0"), [price]);

  async function loadListings() {
    const res = await fetch("/api/me/listings");
    if (res.status === 401) {
      window.location.href = `/login?next=${encodeURIComponent("/sell")}`;
      return;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(JSON.stringify(data));
    setListings((data.items || []) as MyListing[]);
  }

  useEffect(() => {
    void loadListings().catch((e) =>
      setError(e instanceof Error ? e.message : "Failed to load listings"),
    );
  }, []);

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3 py-5">
        <div className="text-lg font-bold text-neutral-900">Sell on Discogs</div>
        <div className="mt-1 text-sm text-neutral-600">
          Create and manage your marketplace listings.
        </div>

        {error ? (
          <div className="mt-4 rounded-sm border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {error}
          </div>
        ) : null}

        <div className="mt-6 grid gap-4 lg:grid-cols-[420px_1fr]">
          {/* Create listing */}
          <section className="rounded-sm border border-neutral-200 bg-white p-4">
            <div className="text-sm font-semibold text-neutral-900">
              Create a listing
            </div>

            <div className="mt-3">
              <div className="mb-1 text-xs font-semibold text-neutral-700">
                Find a release
              </div>
              <div className="flex gap-2">
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                  placeholder="Search releases..."
                />
                <button
                  className="h-10 rounded-sm bg-neutral-900 px-3 text-sm font-semibold text-white hover:bg-neutral-800"
                  onClick={async () => {
                    setBusy(true);
                    setError(null);
                    try {
                      const res = await fetch(
                        `/api/backend/search?q=${encodeURIComponent(q)}`,
                      );
                      const data = (await res.json()) as ReleaseCardType[];
                      if (!res.ok) throw new Error(JSON.stringify(data));
                      setResults(data);
                      setSelected(data[0] || null);
                    } catch (e: unknown) {
                      setError(e instanceof Error ? e.message : "Search failed");
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Search
                </button>
              </div>

              {results.length > 0 ? (
                <div className="mt-3 max-h-[180px] overflow-auto rounded-sm border border-neutral-200">
                  {results.map((r) => (
                    <button
                      key={r.id}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-neutral-50 ${
                        selected?.id === r.id ? "bg-neutral-50" : ""
                      }`}
                      onClick={() => setSelected(r)}
                    >
                      <span className="truncate">
                        {r.artist ? `${r.artist} - ` : ""}
                        {r.title}
                      </span>
                      <span className="ml-2 text-xs text-neutral-500">
                        #{r.id}
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}

              {selected ? (
                <div className="mt-2 text-xs text-neutral-600">
                  Selected:{" "}
                  <span className="font-semibold text-neutral-900">
                    {selected.artist ? `${selected.artist} - ` : ""}
                    {selected.title}
                  </span>
                </div>
              ) : null}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div>
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Media Condition
                </div>
                <input
                  value={mediaCondition}
                  onChange={(e) => setMediaCondition(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Sleeve Condition
                </div>
                <input
                  value={sleeveCondition}
                  onChange={(e) => setSleeveCondition(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Ships From
                </div>
                <input
                  value={shipsFrom}
                  onChange={(e) => setShipsFrom(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Quantity
                </div>
                <input
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Price (cents)
                </div>
                <input
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
              <div className="col-span-2">
                <div className="mb-1 text-xs font-semibold text-neutral-700">
                  Comments
                </div>
                <input
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
                />
              </div>
            </div>

            <button
              disabled={busy || !selected || priceCents <= 0}
              className="mt-4 h-10 w-full rounded-sm bg-green-600 px-3 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-60"
              onClick={async () => {
                if (!selected) return;
                setBusy(true);
                setError(null);
                try {
                  const res = await fetch("/api/me/listings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      release_id: selected.id,
                      media_condition: mediaCondition,
                      sleeve_condition: sleeveCondition,
                      price_cents: priceCents,
                      currency: "USD",
                      ships_from: shipsFrom,
                      quantity: Number(qty || "1"),
                      comments,
                    }),
                  });
                  if (res.status === 401) {
                    window.location.href = `/login?next=${encodeURIComponent("/sell")}`;
                    return;
                  }
                  if (!res.ok) throw new Error(await res.text());
                  await loadListings();
                } catch (e: unknown) {
                  setError(e instanceof Error ? e.message : "Create failed");
                } finally {
                  setBusy(false);
                }
              }}
            >
              Create Listing
            </button>
          </section>

          {/* My listings */}
          <section className="rounded-sm border border-neutral-200 bg-white">
            <div className="border-b border-neutral-200 px-3 py-2 text-xs font-semibold text-neutral-800">
              My Listings
            </div>
            <div className="divide-y divide-neutral-100">
              {listings.map((l) => (
                <div key={l.id} className="flex items-center gap-3 px-3 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-neutral-900">
                      {l.release_title}
                    </div>
                    <div className="mt-0.5 text-xs text-neutral-600">
                      {l.media_condition} / {l.sleeve_condition} • Qty {l.quantity} •{" "}
                      {l.ships_from} • <span className="font-semibold">{l.status}</span>
                    </div>
                    <div className="mt-1">
                      <Link
                        className="text-xs text-neutral-600 hover:underline"
                        href={`/sell/release/${l.release_id}`}
                      >
                        View marketplace for this release
                      </Link>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-neutral-900">
                      {money(l.price_cents, l.currency)}
                    </div>
                    <button
                      disabled={busy}
                      className="mt-1 text-xs text-neutral-600 hover:underline disabled:opacity-60"
                      onClick={async () => {
                        setBusy(true);
                        setError(null);
                        try {
                          const res = await fetch(`/api/me/listings/${l.id}`, {
                            method: "DELETE",
                          });
                          if (!res.ok) throw new Error(await res.text());
                          await loadListings();
                        } catch (e: unknown) {
                          setError(e instanceof Error ? e.message : "Delete failed");
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Deactivate
                    </button>
                  </div>
                </div>
              ))}
              {listings.length === 0 ? (
                <div className="px-3 py-6 text-sm text-neutral-600">
                  You don&apos;t have any listings yet.
                </div>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

