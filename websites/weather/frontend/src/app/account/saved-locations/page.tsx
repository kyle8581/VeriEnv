"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import { clearTokens, loadTokens } from "@/lib/auth";

type Me = {
  id: string;
  email: string;
  name: string | null;
};

type Location = {
  name: string;
  state: string | null;
  country: string;
  zip_code: string | null;
  latitude: number;
  longitude: number;
  timezone: string;
  slug: string;
};

export default function SavedLocationsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [items, setItems] = useState<Location[]>([]);
  const [error, setError] = useState<string | null>(null);
  const tokens = typeof window !== "undefined" ? loadTokens() : null;

  async function refresh() {
    if (!tokens) return;
    setError(null);
    try {
      const meRes = await apiGet<Me>("/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setMe(meRes);
      const locs = await apiGet<Location[]>("/me/locations", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setItems(locs);
    } catch (err) {
      setError(
        typeof err === "object" && err && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to load account",
      );
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function remove(slug: string) {
    if (!tokens) return;
    await apiGet<{ status: string }>(`/me/locations/${slug}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });
    await refresh();
  }

  async function signOut() {
    if (tokens) {
      try {
        await apiGet<{ status: string }>("/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: tokens.refresh_token }),
        });
      } catch {
        // ignore
      }
    }
    clearTokens();
    window.location.href = "/";
  }

  if (!tokens) {
    return (
      <div className="twc-card mx-auto max-w-[720px] p-5">
        <h1 className="text-lg font-semibold text-[#0b1f2a]">
          Saved Locations
        </h1>
        <div className="mt-2 text-sm text-black/60">
          Sign in to save locations.
        </div>
        <Link
          href="/account/sign-in"
          className="mt-4 inline-flex rounded-full bg-[#0b5672] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0a4f67]"
        >
          Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="twc-card p-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[#0b1f2a]">
            Saved Locations
          </h1>
          <div className="text-sm text-black/60">
            {me ? `Signed in as ${me.email}` : "Loading account…"}
          </div>
        </div>
        <button
          onClick={signOut}
          className="inline-flex w-fit rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black/70 hover:bg-black/[0.03]"
        >
          Sign out
        </button>
      </div>

      <div className="mt-4 text-sm text-black/60">
        Add locations using the search box in the header.
      </div>

      {error ? (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((l) => (
          <div
            key={l.slug}
            className="rounded-lg border border-black/10 bg-white p-4"
          >
            <div className="text-sm font-semibold text-[#0b1f2a]">
              {l.name}
              {l.state ? `, ${l.state}` : ""}
            </div>
            <div className="mt-1 text-xs text-black/60">{l.timezone}</div>
            <div className="mt-3 flex items-center gap-2">
              <Link
                href={`/weather/${l.slug}`}
                className="rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#0a4f67]"
              >
                View forecast
              </Link>
              <button
                onClick={() => void remove(l.slug)}
                className="rounded-full border border-black/10 bg-white px-3 py-1.5 text-xs font-semibold text-black/70 hover:bg-black/[0.03]"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      {items.length === 0 ? (
        <div className="mt-6 text-sm text-black/60">
          No saved locations yet.
        </div>
      ) : null}
    </div>
  );
}

