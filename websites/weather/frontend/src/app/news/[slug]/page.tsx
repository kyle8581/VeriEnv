import Image from "next/image";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

import { serverGet } from "@/lib/serverApi";

type ArticleDetail = {
  title: string;
  slug: string;
  summary: string;
  body_md: string;
  hero_image_url: string;
  is_video: boolean;
  source: string;
  reading_minutes: number;
  published_at: string;
  category: { name: string; slug: string };
};

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const a = await serverGet<ArticleDetail>(`/content/articles/${slug}`);

  return (
    <div className="twc-card overflow-hidden">
      <div className="p-4">
        <Link
          href="/news"
          className="text-xs font-semibold text-[#0b5672] hover:underline"
        >
          Back to news
        </Link>
      </div>
      <div className="relative">
        <Image
          src={a.hero_image_url}
          alt={a.title}
          width={1600}
          height={900}
          className="h-[260px] w-full object-cover"
          priority
        />
        {a.is_video ? (
          <div className="absolute left-4 top-4 rounded bg-black/60 px-2 py-1 text-[11px] font-semibold text-white">
            Video
          </div>
        ) : null}
      </div>
      <div className="p-5">
        <div className="text-xs font-semibold text-black/50">{a.category.name}</div>
        <h1 className="mt-1 text-2xl font-semibold leading-snug text-[#0b1f2a]">
          {a.title}
        </h1>
        <div className="mt-2 text-sm text-black/60">{a.summary}</div>
        <div className="mt-3 text-xs text-black/45">
          {a.source} • {a.reading_minutes} min read
        </div>
        <div className="prose prose-slate mt-6 max-w-none">
          <ReactMarkdown>{a.body_md}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

