"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Header } from "@/components/Header";
import { ListingCard } from "@/components/ListingCard";
import { MapView } from "@/components/MapView";
import { createSavedSearch, listFavorites, searchListings } from "@/lib/api";
import { getToken } from "@/lib/auth_client";
import type { Listing, ListingSearchResponse } from "@/lib/types";

function parseCityState(q: string): { city?: string; state?: string } {
  const raw = (q || "").trim();
  if (!raw) return {};
  if (raw.includes(",")) {
    const [city, state] = raw.split(",", 2).map((s) => s.trim());
    return { city, state: state?.toUpperCase()?.slice(0, 2) };
  }
  return { city: raw };
}

function pillLabelForBeds(minBeds: number | null) {
  if (minBeds == null) return null;
  if (minBeds === 0) return "Studio+";
  if (minBeds === 1) return "1+ Beds";
  if (minBeds === 2) return "2+ Beds";
  if (minBeds === 3) return "3+ Beds";
  return "4+ Beds";
}

export function SearchPageClient({
  initialQuery,
  initialData,
}: {
  initialQuery: string;
  initialData: ListingSearchResponse;
}) {
  const [q, setQ] = useState(initialQuery);
  const [data, setData] = useState(initialData);
  const [priceOpen, setPriceOpen] = useState(false);
  const [bedsOpen, setBedsOpen] = useState(false);
  const [typeOpen, setTypeOpen] = useState(false);
  const [moveInOpen, setMoveInOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const [minPrice, setMinPrice] = useState<number | null>(null);
  const [maxPrice, setMaxPrice] = useState<number | null>(null);
  const [minBeds, setMinBeds] = useState<number | null>(null);
  const [maxBeds, setMaxBeds] = useState<number | null>(null);
  const [propertyType, setPropertyType] = useState<string | null>(null);
  const [moveInDate, setMoveInDate] = useState<string | null>(null); // yyyy-mm-dd
  const [hasVideos, setHasVideos] = useState(false);
  const [hasVirtualTour, setHasVirtualTour] = useState(false);
  const [specialsOnly, setSpecialsOnly] = useState(false);
  const [petFriendly, setPetFriendly] = useState(false);
  const [sort, setSort] = useState<"newest" | "price_asc" | "price_desc">(
    "newest",
  );
  const [loading, setLoading] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(() => new Set());

  const bedsPill = pillLabelForBeds(minBeds);

  const center = useMemo(() => {
    const parsed = parseCityState(q);
    const key = `${parsed.city ?? ""},${parsed.state ?? ""}`.toLowerCase();
    if (key.includes("boston")) return { lat: 42.3601, lon: -71.0589 };
    if (key.includes("columbus")) return { lat: 39.9612, lon: -82.9988 };
    const first = data.items[0];
    if (first) return { lat: first.latitude, lon: first.longitude };
    return { lat: 42.3601, lon: -71.0589 };
  }, [q, data.items]);

  async function runSearch(next?: Partial<{ q: string }>) {
    const nextQ = next?.q ?? q;
    setLoading(true);
    try {
      const res = await searchListings({
        q: nextQ,
        min_price: minPrice ?? undefined,
        max_price: maxPrice ?? undefined,
        min_beds: minBeds ?? undefined,
        max_beds: maxBeds ?? undefined,
        property_type: propertyType ?? undefined,
        move_in_date: moveInDate ?? undefined,
        has_videos: hasVideos || undefined,
        has_virtual_tour: hasVirtualTour || undefined,
        specials_only: specialsOnly || undefined,
        amenity: petFriendly ? "Dog & Cat Friendly" : undefined,
        sort,
        limit: 25,
      });
      setData(res);
    } finally {
      setLoading(false);
    }
  }

  // Close dropdowns when clicking outside.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      const t = e.target as HTMLElement | null;
      if (!t) return;
      if (
        t.closest("[data-dd='price']") ||
        t.closest("[data-dd='beds']") ||
        t.closest("[data-dd='type']") ||
        t.closest("[data-dd='movein']") ||
        t.closest("[data-dd='more']") ||
        t.closest("[data-dd='sort']")
      )
        return;
      setPriceOpen(false);
      setBedsOpen(false);
      setTypeOpen(false);
      setMoveInOpen(false);
      setMoreOpen(false);
      setSortOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    listFavorites(token)
      .then((items) => setFavoriteIds(new Set(items.map((i) => i.id))))
      .catch(() => {});
  }, []);

  const listings: Listing[] = data.items;

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-[1400px] items-center gap-3 px-3 py-2">
          <input
            className="h-10 w-[240px] rounded-sm border border-black/20 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch();
            }}
            aria-label="Location"
          />

          <div className="relative" data-dd="price">
            <button
              type="button"
              className="flex h-10 items-center gap-2 rounded-sm border border-black/20 bg-white px-4 text-[14px] text-[#333]"
              onClick={() => {
                setPriceOpen((v) => !v);
                setBedsOpen(false);
                setTypeOpen(false);
                setMoveInOpen(false);
                setMoreOpen(false);
                setSortOpen(false);
              }}
            >
              Price <span className="text-apts-green">▾</span>
            </button>
            {priceOpen ? (
              <div className="absolute left-0 top-[44px] z-30 w-[320px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                <div className="grid grid-cols-2 gap-3 p-4">
                  <label className="block">
                    <div className="text-[11px] font-semibold text-[#666]">
                      No Min
                    </div>
                    <input
                      inputMode="numeric"
                      className="mt-1 h-9 w-full rounded-sm border border-black/15 px-3 text-[13px] outline-none focus:ring-2 ring-apts-green"
                      value={minPrice ?? ""}
                      onChange={(e) =>
                        setMinPrice(e.target.value ? Number(e.target.value) : null)
                      }
                      placeholder="0"
                    />
                  </label>
                  <label className="block">
                    <div className="text-[11px] font-semibold text-[#666]">
                      No Max
                    </div>
                    <input
                      inputMode="numeric"
                      className="mt-1 h-9 w-full rounded-sm border border-black/15 px-3 text-[13px] outline-none focus:ring-2 ring-apts-green"
                      value={maxPrice ?? ""}
                      onChange={(e) =>
                        setMaxPrice(e.target.value ? Number(e.target.value) : null)
                      }
                      placeholder="Any"
                    />
                  </label>
                </div>
                <div className="flex items-center justify-between border-t border-black/10 px-4 py-3">
                  <button
                    type="button"
                    className="text-[12px] font-semibold text-[#0b6fbf]"
                    onClick={() => {
                      setMinPrice(null);
                      setMaxPrice(null);
                    }}
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    className="h-9 rounded-sm bg-apts-green px-5 text-[13px] font-semibold text-white"
                    onClick={() => {
                      setPriceOpen(false);
                      runSearch();
                    }}
                  >
                    Apply
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          <div className="relative" data-dd="beds">
            <button
              type="button"
              className={`flex h-10 items-center gap-2 rounded-sm border px-4 text-[14px] ${
                bedsPill
                  ? "border-apts-green bg-apts-green text-white"
                  : "border-black/20 bg-white text-[#333]"
              }`}
              onClick={() => {
                setBedsOpen((v) => !v);
                setPriceOpen(false);
                setTypeOpen(false);
                setMoveInOpen(false);
                setMoreOpen(false);
                setSortOpen(false);
              }}
            >
              {bedsPill ?? "Beds"}{" "}
              <span className={bedsPill ? "text-white" : "text-apts-green"}>
                ▾
              </span>
              {bedsPill ? (
                <span
                  className="ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/20 text-[12px]"
                  role="button"
                  aria-label="Clear beds"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMinBeds(null);
                    setMaxBeds(null);
                    runSearch();
                  }}
                >
                  ×
                </span>
              ) : null}
            </button>
            {bedsOpen ? (
              <div className="absolute left-0 top-[44px] z-30 w-[420px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 p-4">
                  <label className="block">
                    <div className="text-[11px] font-semibold text-[#666]">
                      No Min
                    </div>
                    <select
                      className="mt-1 h-9 w-full rounded-sm border border-black/15 bg-white px-3 text-[13px] outline-none focus:ring-2 ring-apts-green"
                      value={minBeds ?? ""}
                      onChange={(e) =>
                        setMinBeds(e.target.value ? Number(e.target.value) : null)
                      }
                    >
                      <option value="">No Min</option>
                      <option value="0">Studio</option>
                      <option value="1">1 Bed</option>
                      <option value="2">2 Beds</option>
                      <option value="3">3 Beds</option>
                      <option value="4">4+ Beds</option>
                    </select>
                  </label>
                  <div className="pt-6 text-[#777]">–</div>
                  <label className="block">
                    <div className="text-[11px] font-semibold text-[#666]">
                      No Max
                    </div>
                    <select
                      className="mt-1 h-9 w-full rounded-sm border border-black/15 bg-white px-3 text-[13px] outline-none focus:ring-2 ring-apts-green"
                      value={maxBeds ?? ""}
                      onChange={(e) =>
                        setMaxBeds(e.target.value ? Number(e.target.value) : null)
                      }
                    >
                      <option value="">No Max</option>
                      <option value="0">Studio</option>
                      <option value="1">1 Bed</option>
                      <option value="2">2 Beds</option>
                      <option value="3">3 Beds</option>
                      <option value="4">4+ Beds</option>
                    </select>
                  </label>
                </div>
                <div className="border-t border-black/10">
                  {[
                    ["No Min", null],
                    ["1 Bed", 1],
                    ["2 Beds", 2],
                    ["3 Beds", 3],
                    ["4+ Beds", 4],
                  ].map(([label, value]) => (
                    <button
                      key={label}
                      type="button"
                      className={`flex w-full items-center justify-between px-4 py-3 text-left text-[13px] ${
                        value === minBeds ? "bg-[#e9f2ea]" : "bg-white"
                      }`}
                      onClick={() => {
                        setMinBeds(value as number | null);
                        setBedsOpen(false);
                        runSearch();
                      }}
                    >
                      <span>{label}</span>
                      <span className="text-[#777]"> </span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="relative" data-dd="type">
            <button
              type="button"
              className="flex h-10 items-center gap-2 rounded-sm border border-black/20 bg-white px-4 text-[14px] text-[#333]"
              onClick={() => {
                setTypeOpen((v) => !v);
                setPriceOpen(false);
                setBedsOpen(false);
                setMoveInOpen(false);
                setMoreOpen(false);
                setSortOpen(false);
              }}
            >
              Type <span className="text-apts-green">▾</span>
            </button>
            {typeOpen ? (
              <div className="absolute left-0 top-[44px] z-30 w-[240px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                {[
                  ["Any", null],
                  ["Apartment", "apartment"],
                  ["Condo", "condo"],
                  ["Townhome", "townhome"],
                ].map(([label, value]) => (
                  <button
                    key={label}
                    type="button"
                    className={`flex w-full items-center justify-between px-4 py-3 text-left text-[13px] ${
                      value === propertyType ? "bg-[#e9f2ea]" : "bg-white"
                    }`}
                    onClick={() => {
                      setPropertyType(value as string | null);
                      setTypeOpen(false);
                      runSearch();
                    }}
                  >
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="relative" data-dd="movein">
            <button
              type="button"
              className="flex h-10 items-center gap-2 rounded-sm border border-black/20 bg-white px-4 text-[14px] text-[#333]"
              onClick={() => {
                setMoveInOpen((v) => !v);
                setPriceOpen(false);
                setBedsOpen(false);
                setTypeOpen(false);
                setMoreOpen(false);
                setSortOpen(false);
              }}
            >
              Move-In Date <span className="text-apts-green">▾</span>
            </button>
            {moveInOpen ? (
              <div className="absolute left-0 top-[44px] z-30 w-[300px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                <div className="p-4">
                  <label className="block">
                    <div className="text-[11px] font-semibold text-[#666]">
                      Available by
                    </div>
                    <input
                      type="date"
                      className="mt-1 h-9 w-full rounded-sm border border-black/15 bg-white px-3 text-[13px] outline-none focus:ring-2 ring-apts-green"
                      value={moveInDate ?? ""}
                      onChange={(e) =>
                        setMoveInDate(e.target.value ? e.target.value : null)
                      }
                    />
                  </label>
                </div>
                <div className="flex items-center justify-between border-t border-black/10 px-4 py-3">
                  <button
                    type="button"
                    className="text-[12px] font-semibold text-[#0b6fbf]"
                    onClick={() => setMoveInDate(null)}
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    className="h-9 rounded-sm bg-apts-green px-5 text-[13px] font-semibold text-white"
                    onClick={() => {
                      setMoveInOpen(false);
                      runSearch();
                    }}
                  >
                    Apply
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          <div className="relative" data-dd="more">
            <button
              type="button"
              className="flex h-10 items-center gap-2 rounded-sm border border-black/20 bg-white px-4 text-[14px] text-[#333]"
              onClick={() => {
                setMoreOpen((v) => !v);
                setPriceOpen(false);
                setBedsOpen(false);
                setTypeOpen(false);
                setMoveInOpen(false);
                setSortOpen(false);
              }}
            >
              More <span className="text-apts-green">▾</span>
            </button>
            {moreOpen ? (
              <div className="absolute left-0 top-[44px] z-30 w-[320px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                <div className="space-y-3 p-4 text-[13px] text-[#333]">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={specialsOnly}
                      onChange={(e) => setSpecialsOnly(e.target.checked)}
                    />
                    <span>Specials</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={petFriendly}
                      onChange={(e) => setPetFriendly(e.target.checked)}
                    />
                    <span>Dog &amp; Cat Friendly</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={hasVideos}
                      onChange={(e) => setHasVideos(e.target.checked)}
                    />
                    <span>Videos</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={hasVirtualTour}
                      onChange={(e) => setHasVirtualTour(e.target.checked)}
                    />
                    <span>Virtual Tour</span>
                  </label>
                </div>
                <div className="flex items-center justify-between border-t border-black/10 px-4 py-3">
                  <button
                    type="button"
                    className="text-[12px] font-semibold text-[#0b6fbf]"
                    onClick={() => {
                      setSpecialsOnly(false);
                      setPetFriendly(false);
                      setHasVideos(false);
                      setHasVirtualTour(false);
                    }}
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    className="h-9 rounded-sm bg-apts-green px-5 text-[13px] font-semibold text-white"
                    onClick={() => {
                      setMoreOpen(false);
                      runSearch();
                    }}
                  >
                    Apply
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          <div className="ml-auto flex items-center gap-6 pr-1 text-[14px] text-[#0b6fbf]">
            <div className="relative" data-dd="sort">
              <button
                type="button"
                className="inline-flex items-center gap-2 hover:underline"
                onClick={() => {
                  setSortOpen((v) => !v);
                  setPriceOpen(false);
                  setBedsOpen(false);
                  setTypeOpen(false);
                  setMoveInOpen(false);
                  setMoreOpen(false);
                }}
              >
                Sort <span className="text-[#0b6fbf]">⇅</span>
              </button>
              {sortOpen ? (
                <div className="absolute right-0 top-[30px] z-30 w-[220px] rounded-sm border border-black/15 bg-white shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
                  {[
                    ["Newest", "newest"],
                    ["Price (Low to High)", "price_asc"],
                    ["Price (High to Low)", "price_desc"],
                  ].map(([label, value]) => (
                    <button
                      key={value}
                      type="button"
                      className={`flex w-full items-center justify-between px-4 py-3 text-left text-[13px] ${
                        sort === value ? "bg-[#e9f2ea]" : "bg-white"
                      }`}
                      onClick={() => {
                        setSort(value as typeof sort);
                        setSortOpen(false);
                        runSearch();
                      }}
                    >
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            <button
              type="button"
              className="hover:underline"
              onClick={async () => {
                const token = getToken();
                if (!token) {
                  window.location.href = "/auth";
                  return;
                }
                await createSavedSearch({
                  token,
                  name: `Search: ${q}`,
                  query: q,
                  filters: {
                    min_price: minPrice,
                    max_price: maxPrice,
                    min_beds: minBeds,
                    max_beds: maxBeds,
                    property_type: propertyType,
                    move_in_date: moveInDate,
                    has_videos: hasVideos,
                    has_virtual_tour: hasVirtualTour,
                    specials_only: specialsOnly,
                    pet_friendly: petFriendly,
                    sort,
                  },
                });
                window.alert("Saved search created.");
              }}
            >
              Save Search
            </button>
            <Link
              className="hover:underline"
              href="/notifications"
              aria-label="Notifications"
            >
              🔔
            </Link>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-112px)]">
        <div className="relative w-[68%] border-r border-black/10">
          <div className="absolute left-3 top-3 z-20 flex items-center gap-2 rounded-sm bg-white/90 px-3 py-2 text-[14px] text-[#333] shadow-[0_2px_10px_rgba(0,0,0,0.12)]">
            <span className="inline-block h-4 w-4 rotate-45 rounded-sm bg-apts-green" />
            <span className="font-semibold">{data.total.toLocaleString()}</span>{" "}
            Apartments for Rent
          </div>
          <MapView listings={listings} center={center} />
        </div>

        <div className="w-[32%] overflow-y-auto bg-white">
          {loading ? (
            <div className="px-4 py-6 text-[13px] text-[#666]">
              Loading…
            </div>
          ) : null}
          {listings.map((l) => (
            <ListingCard
              key={l.id}
              listing={l}
              isFavoriteInitial={favoriteIds.has(l.id)}
              onFavoriteChange={(next) => {
                setFavoriteIds((prev) => {
                  const copy = new Set(prev);
                  if (next) copy.add(l.id);
                  else copy.delete(l.id);
                  return copy;
                });
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

