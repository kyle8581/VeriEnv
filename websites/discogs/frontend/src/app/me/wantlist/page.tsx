"use client";

import { useEffect, useState } from "react";

import { ReleaseCard } from "@/components/ReleaseCard";
import type { ReleaseCard as ReleaseCardType } from "@/lib/types";

export const dynamic = "force-dynamic";

export default function WantlistPage() {
  const [items, setItems] = useState<ReleaseCardType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/me/wantlist");
        if (res.status === 401) {
          window.location.href = `/login?next=${encodeURIComponent("/me/wantlist")}`;
          return;
        }
        const data = (await res.json()) as ReleaseCardType[];
        if (!res.ok) throw new Error(JSON.stringify(data));
        setItems(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load wantlist");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3 py-5">
        <div className="text-lg font-bold text-neutral-900">My Wantlist</div>
        <div className="mt-1 text-sm text-neutral-600">
          Releases you&apos;re looking for.
        </div>

        {loading ? (
          <div className="mt-6 rounded-sm border border-neutral-200 bg-white p-4 text-sm">
            Loading...
          </div>
        ) : error ? (
          <div className="mt-6 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
            {items.map((r) => (
              <ReleaseCard key={r.id} release={r} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

