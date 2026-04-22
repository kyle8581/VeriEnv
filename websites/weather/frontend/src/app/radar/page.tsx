import Link from "next/link";

import { serverGet } from "@/lib/serverApi";

type Location = {
  name: string;
  state: string | null;
  slug: string;
};

export default async function RadarPage() {
  const popular = await serverGet<Location[]>("/locations/search?q=New&limit=8");
  return (
    <div className="twc-card p-5">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Radar</h1>
      <div className="mt-2 text-sm text-black/60">
        Choose a location to view radar-style precipitation context.
      </div>

      <div className="mt-5 rounded-lg border border-black/10 bg-white p-4">
        <div className="text-sm font-semibold">Popular locations</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {popular.map((l) => (
            <Link
              key={l.slug}
              href={`/weather/${l.slug}`}
              className="rounded-full border border-black/10 bg-white px-3 py-1 text-xs font-semibold text-black/70 hover:bg-black/[0.03]"
            >
              {l.name}
              {l.state ? `, ${l.state}` : ""}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

