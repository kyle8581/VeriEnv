import Link from "next/link";

import { ReleaseCard } from "@/components/ReleaseCard";
import { apiGet } from "@/lib/api";
import type { GenreOverviewData } from "@/lib/types";

export const dynamic = "force-dynamic";

function BarChart({
  title,
  rows,
  leftLabel,
  rightLabel,
}: {
  title: string;
  rows: { label: string; value: number }[];
  leftLabel: string;
  rightLabel: string;
}) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <div className="rounded-sm border border-neutral-200 bg-white p-3">
      <div className="text-sm font-bold text-neutral-900">{title}</div>
      <div className="mt-3 space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center gap-2">
            <div className="w-12 text-[11px] text-neutral-600">{r.label}</div>
            <div className="h-3 flex-1 bg-neutral-100">
              <div
                className="h-3 bg-blue-600"
                style={{ width: `${(r.value / max) * 100}%` }}
              />
            </div>
            <div className="w-10 text-right text-[11px] text-neutral-700">
              {r.value}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 text-[11px] text-neutral-500">
        <div>{leftLabel}</div>
        <div className="text-right">{rightLabel}</div>
      </div>
    </div>
  );
}

export default async function GenrePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const data = await apiGet<GenreOverviewData>(`/genres/${slug}/overview`);

  const title = `${data.genre.name} Genre Overview`;

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3">
        <div className="py-4">
          <div className="text-lg font-bold text-neutral-900">{title}</div>
        </div>

        {/* Sub-nav bar */}
        <div className="mb-4 bg-[#111] px-2 py-2 text-white">
          <div className="flex flex-wrap gap-4 text-xs">
            <Link className="hover:underline" href={`/genre/${slug}`}>
              {data.genre.name} Overview
            </Link>
            <Link className="hover:underline" href={`/search?q=${slug}`}>
              {data.genre.name} Releases
            </Link>
            <Link className="hover:underline" href={`/search?q=${slug}%20artist`}>
              {data.genre.name} Artists
            </Link>
          </div>
        </div>

        {/* Description */}
        <section className="rounded-sm border border-neutral-200 bg-white p-4">
          <div className="text-sm font-bold text-neutral-900">
            {data.genre.name} Music Description
          </div>
          <div className="mt-3 text-sm leading-6 text-neutral-700">
            {data.genre.description}
          </div>
        </section>

        {/* Most Collected */}
        <section className="mt-6">
          <div className="flex items-baseline justify-between">
            <div className="text-sm font-bold text-neutral-900">
              Most Collected {data.genre.name} Music
            </div>
            <Link href={`/search?q=${slug}`} className="text-xs hover:underline">
              Explore the Popular {data.genre.name} Music
            </Link>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {data.most_collected.map((r) => (
              <ReleaseCard key={r.id} release={r} />
            ))}
          </div>
        </section>

        {/* Artists (visual placeholder, like the reference) */}
        <section className="mt-6">
          <div className="text-sm font-bold text-neutral-900">
            {data.genre.name} Artists
          </div>
          <div className="mt-3 grid grid-cols-3 gap-3 sm:grid-cols-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <div
                key={i}
                className="aspect-square rounded-sm border border-neutral-200 bg-neutral-50"
              />
            ))}
          </div>
        </section>

        {/* Early Releases */}
        <section className="mt-6">
          <div className="flex items-baseline justify-between">
            <div className="text-sm font-bold text-neutral-900">
              Early {data.genre.name} Releases
            </div>
            <Link href={`/search?q=early%20${slug}`} className="text-xs hover:underline">
              Explore Early {data.genre.name} Music
            </Link>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {data.early_releases.map((r) => (
              <ReleaseCard key={r.id} release={r} />
            ))}
          </div>
        </section>

        {/* Charts */}
        <section className="mt-8 grid gap-4 md:grid-cols-2">
          <BarChart
            title={`${data.genre.name} Music Releases by Decade`}
            rows={data.stats.releases_by_decade}
            leftLabel="Decade"
            rightLabel="Number of releases"
          />
          <BarChart
            title={`Top Submitters of ${data.genre.name} Music`}
            rows={data.stats.top_submitters}
            leftLabel="Contributor"
            rightLabel="Number of releases"
          />
        </section>

        {/* Most sold */}
        <section className="mt-8">
          <div className="flex items-baseline justify-between">
            <div className="text-sm font-bold text-neutral-900">
              Most Sold {data.genre.name} Releases This Month
            </div>
            <Link href={`/search?q=trending%20${slug}`} className="text-xs hover:underline">
              Explore more Trending {data.genre.name} Music
            </Link>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
            {data.most_sold_this_month.map((r) => (
              <ReleaseCard key={r.id} release={r} />
            ))}
          </div>
        </section>

        {/* Related styles */}
        <section className="mt-8 pb-8">
          <div className="text-sm font-bold text-neutral-900">
            Related Styles of Music
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.related_styles.map((s) => (
              <Link
                key={s}
                href={`/search?q=${encodeURIComponent(s)}`}
                className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs text-neutral-800 hover:bg-neutral-50"
              >
                {s}
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

