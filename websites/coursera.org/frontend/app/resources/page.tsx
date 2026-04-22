import Link from "next/link";
import Image from "next/image";

import { apiGet } from "@/lib/api";

export default async function ResourcesPage({
  searchParams,
}: {
  searchParams: Promise<{ kind?: string }>;
}) {
  const { kind } = await searchParams;
  const query = kind ? `?kind=${encodeURIComponent(kind)}&limit=24` : "?limit=24";

  const resources = await apiGet<{
    items: {
      id: number;
      kind: string;
      title: string;
      slug: string;
      summary: string;
      hero_image_url: string;
      cta_label: string;
    }[];
    total: number;
  }>(`/api/resources${query}`, { cache: "no-store" });

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Resources</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          Explore ebooks, events, and articles to support program design and student outcomes.
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {resources.items.map((r) => (
            <Link
              key={r.id}
              href={`/resources/${r.slug}`}
              className="group overflow-hidden rounded border border-zinc-200 bg-white"
            >
              <div className="relative h-36 w-full">
                <Image
                  src={r.hero_image_url}
                  alt={r.title}
                  fill
                  className="object-cover transition group-hover:scale-[1.02]"
                />
              </div>
              <div className="p-5">
                <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{r.kind}</div>
                <div className="mt-2 text-sm font-semibold text-zinc-900">{r.title}</div>
                <div className="mt-2 text-sm leading-6 text-zinc-600 line-clamp-2">{r.summary}</div>
                <div className="mt-4 text-sm font-semibold text-[#0056D2]">{r.cta_label}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

