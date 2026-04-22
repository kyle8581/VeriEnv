import Image from "next/image";
import Link from "next/link";

import { ReleaseCard } from "@/components/ReleaseCard";
import { apiGet } from "@/lib/api";
import type { HomeData } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const data = await apiGet<HomeData>("/home");

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3">
        {/* Hero */}
        <section className="relative mt-4 overflow-hidden rounded-sm bg-neutral-900">
          <div className="relative h-[220px] w-full sm:h-[260px]">
            <Image
              src={data.hero_image_url}
              alt=""
              fill
              className="object-cover opacity-80"
              priority
              sizes="1040px"
            />
          </div>
          <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-black/20" />
          <div className="absolute inset-0 flex flex-col justify-end gap-3 p-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-[520px]">
              <h1 className="text-2xl font-semibold text-white sm:text-3xl">
                {data.hero_title}
              </h1>
            </div>
            <div className="grid w-full max-w-[360px] gap-2 sm:grid-cols-1">
              {data.hero_tiles.map((t) => (
                <Link
                  key={t.title}
                  href="/"
                  className="group flex items-center gap-3 rounded-sm bg-black/50 p-2 hover:bg-black/60"
                >
                  <div className="relative h-12 w-12 overflow-hidden rounded-sm bg-white/10">
                    <Image
                      src={t.image_url}
                      alt=""
                      fill
                      className="object-cover"
                      sizes="48px"
                    />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-white">
                      {t.title}
                    </div>
                    <div className="truncate text-xs text-white/80">
                      {t.subtitle}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Banner ad */}
        <section className="mt-4 overflow-hidden rounded-sm border border-neutral-200 bg-white">
          <Link
            href={data.banner.release_id ? `/release/${data.banner.release_id}` : "/"}
            className="relative block h-[90px] w-full bg-neutral-50 sm:h-[110px]"
          >
            <Image
              src={data.banner.image_url}
              alt={data.banner.title}
              fill
              className="object-cover"
              sizes="1040px"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
              <div className="text-center text-white">
                <div className="text-sm font-semibold">{data.banner.title}</div>
                <div className="text-xs">{data.banner.subtitle}</div>
              </div>
            </div>
          </Link>
        </section>

        {/* Trending */}
        <section className="mt-6">
          <div className="flex items-baseline justify-between">
            <h2 className="text-sm font-bold text-neutral-900">
              Trending Releases
            </h2>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {data.trending_releases.map((r) => (
              <ReleaseCard key={r.id} release={r} />
            ))}
          </div>
        </section>
      </div>

      {/* Expensive sold */}
      <section className="mt-8 bg-[#111]">
        <div className="mx-auto max-w-[1040px] px-3 py-8">
          <div className="flex items-baseline justify-between">
            <h2 className="text-sm font-bold text-white">
              Most Expensive Releases Sold This Month
            </h2>
            <Link href="/" className="text-xs text-white/80 hover:underline">
              See how these expensive items sold
            </Link>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {data.most_expensive_sold.map((row) => (
              <div key={row.release.id} className="space-y-2">
                <ReleaseCard release={row.release} />
                <div className="text-xs text-white/80">
                  ${(row.price_cents / 100).toFixed(2)} {row.currency}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-end gap-2">
            <label className="text-xs text-white/80">Email</label>
            <input
              placeholder=""
              className="h-8 w-[220px] rounded-sm border border-white/10 bg-white/10 px-2 text-xs text-white placeholder:text-white/40 outline-none"
            />
            <button className="h-8 rounded-sm bg-green-600 px-3 text-xs font-semibold text-white hover:bg-green-500">
              Subscribe
            </button>
          </div>
        </div>
      </section>

      {/* Newly added */}
      <section className="mx-auto max-w-[1040px] px-3 py-8">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-bold text-neutral-900">
            Explore Newly Added
          </h2>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
          {data.newly_added.map((r) => (
            <ReleaseCard key={r.id} release={r} />
          ))}
        </div>
      </section>

      {/* App promo */}
      <section className="bg-[#111]">
        <div className="mx-auto flex max-w-[1040px] flex-col items-center gap-6 px-3 py-10 md:flex-row md:items-end md:justify-between">
          <div className="flex w-full items-end justify-center gap-3 md:justify-start">
            <div className="relative h-[220px] w-[130px] rounded-lg bg-neutral-800" />
            <div className="relative h-[260px] w-[150px] rounded-lg bg-neutral-800" />
          </div>
          <div className="text-center md:text-right">
            <div className="text-sm font-semibold text-white">
              It&apos;s everywhere!
            </div>
            <div className="mt-1 text-xs text-white/80">
              (The Discogs iOS/Android app)
            </div>
            <div className="mt-3 flex justify-center gap-2 md:justify-end">
              <div className="rounded bg-white/10 px-3 py-2 text-xs text-white">
                App Store
              </div>
              <div className="rounded bg-white/10 px-3 py-2 text-xs text-white">
                Google Play
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

