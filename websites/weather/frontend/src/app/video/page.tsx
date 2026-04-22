import Image from "next/image";
import Link from "next/link";

import { serverGet } from "@/lib/serverApi";

type Article = {
  title: string;
  slug: string;
  summary: string;
  hero_image_url: string;
  published_at: string;
  category: { name: string; slug: string };
};

export default async function VideoPage() {
  const items = await serverGet<Article[]>("/content/articles?kind=video&limit=30");
  return (
    <div className="twc-card p-4">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Video</h1>
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((a) => (
          <Link
            key={a.slug}
            href={`/news/${a.slug}`}
            className="group overflow-hidden rounded-lg border border-black/10 bg-white"
          >
            <div className="relative">
              <Image
                src={a.hero_image_url}
                alt={a.title}
                width={1000}
                height={650}
                className="h-[160px] w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
              />
              <div className="absolute left-3 top-3 rounded bg-black/60 px-2 py-1 text-[11px] font-semibold text-white">
                Video
              </div>
            </div>
            <div className="p-3">
              <div className="line-clamp-2 text-sm font-semibold text-[#0b1f2a]">
                {a.title}
              </div>
              <div className="mt-2 line-clamp-3 text-xs text-black/60">
                {a.summary}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

