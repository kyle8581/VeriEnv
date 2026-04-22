"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function ReleaseActions({
  releaseId,
  forSaleCount,
  haveCount,
  wantCount,
}: {
  releaseId: number;
  forSaleCount: number;
  haveCount: number;
  wantCount: number;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [have, setHave] = useState(haveCount);
  const [want, setWant] = useState(wantCount);

  async function toggle(kind: "collection" | "wantlist") {
    setBusy(true);
    try {
      const res = await fetch(`/api/me/${kind}/${releaseId}`, { method: "POST" });
      if (res.status === 401) {
        router.push(`/login?next=${encodeURIComponent(`/release/${releaseId}`)}`);
        return;
      }
      if (!res.ok) throw new Error(await res.text());
      if (kind === "collection") setHave((v) => v + 1);
      else setWant((v) => v + 1);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 space-y-2">
      <button
        disabled={busy}
        onClick={() => void toggle("wantlist")}
        className="w-full rounded-sm border border-neutral-300 bg-white px-3 py-2 text-xs font-semibold hover:bg-neutral-50 disabled:opacity-60"
      >
        Add to Wantlist
      </button>
      <button
        disabled={busy}
        onClick={() => void toggle("collection")}
        className="w-full rounded-sm border border-neutral-300 bg-white px-3 py-2 text-xs font-semibold hover:bg-neutral-50 disabled:opacity-60"
      >
        Add to Collection
      </button>
      <Link
        href={`/sell/release/${releaseId}`}
        className="block w-full rounded-sm bg-neutral-900 px-3 py-2 text-center text-xs font-semibold text-white hover:bg-neutral-800"
      >
        Marketplace ({forSaleCount} for sale)
      </Link>
      <div className="grid grid-cols-2 gap-2 pt-1 text-xs text-neutral-600">
        <div>
          Have: <span className="font-semibold text-neutral-900">{have}</span>
        </div>
        <div className="text-right">
          Want: <span className="font-semibold text-neutral-900">{want}</span>
        </div>
      </div>
    </div>
  );
}

