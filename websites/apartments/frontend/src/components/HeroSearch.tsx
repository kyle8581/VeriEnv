"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function HeroSearch({ defaultQuery }: { defaultQuery: string }) {
  const router = useRouter();
  const [q, setQ] = useState(defaultQuery);

  return (
    <form
      className="mx-auto mt-6 flex w-full max-w-[760px] overflow-hidden rounded-sm bg-white shadow-[0_6px_20px_rgba(0,0,0,0.25)]"
      onSubmit={(e) => {
        e.preventDefault();
        const query = q.trim();
        router.push(`/apartments?q=${encodeURIComponent(query || defaultQuery)}`);
      }}
    >
      <input
        className="h-12 w-full px-4 text-[15px] text-[#333] outline-none"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Enter City, State, Zip, or Neighborhood"
        aria-label="Location"
      />
      <button
        type="submit"
        className="h-12 w-[110px] bg-apts-green text-[15px] font-semibold text-white"
      >
        Search
      </button>
    </form>
  );
}

