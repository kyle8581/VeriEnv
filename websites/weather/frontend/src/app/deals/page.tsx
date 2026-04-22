import Image from "next/image";

import { serverGet } from "@/lib/serverApi";

type Deal = {
  id: string;
  title: string;
  image_url: string;
  provider: string;
  price_usd: number | null;
  badge: string | null;
  cta_url: string;
};

export default async function DealsPage() {
  const items = await serverGet<Deal[]>("/content/deals?limit=60&offset=0");

  return (
    <div className="twc-card p-4">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Featured Deals</h1>
      <div className="mt-2 text-sm text-black/60">
        Curated gear and essentials for every season.
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((d) => (
          <a
            key={d.id}
            href={d.cta_url}
            target="_blank"
            rel="noreferrer"
            className="group overflow-hidden rounded-lg border border-black/10 bg-white"
          >
            <Image
              src={d.image_url}
              alt={d.title}
              width={1000}
              height={650}
              className="h-[170px] w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
            />
            <div className="p-3">
              <div className="line-clamp-2 text-sm font-semibold text-[#0b1f2a]">
                {d.title}
              </div>
              <div className="mt-1 text-xs text-black/55">
                {d.provider}
                {d.price_usd !== null ? ` • $${d.price_usd.toFixed(2)}` : ""}
                {d.badge ? ` • ${d.badge}` : ""}
              </div>
              <div className="mt-3 inline-flex rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white">
                View deal
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

