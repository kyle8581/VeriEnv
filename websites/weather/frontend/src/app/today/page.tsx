import Link from "next/link";

import { serverGet } from "@/lib/serverApi";

type Article = {
  title: string;
  slug: string;
  summary: string;
  category: { name: string; slug: string };
};

export default async function TodayPage() {
  const items = await serverGet<Article[]>(
    "/content/articles?limit=20&offset=0",
  );

  return (
    <div className="twc-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-[#0b1f2a]">Today</h1>
        <Link
          href="/news"
          className="text-xs font-semibold text-[#0b5672] hover:underline"
        >
          Browse all news
        </Link>
      </div>

      <div className="space-y-3">
        {items.map((a) => (
          <Link
            key={a.slug}
            href={`/news/${a.slug}`}
            className="block rounded-lg border border-black/10 bg-white p-4 hover:bg-black/[0.02]"
          >
            <div className="text-xs font-semibold text-black/50">
              {a.category.name}
            </div>
            <div className="mt-1 text-sm font-semibold text-[#0b1f2a]">
              {a.title}
            </div>
            <div className="mt-1 text-xs text-black/60">{a.summary}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}

