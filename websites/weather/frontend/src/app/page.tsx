import Image from "next/image";
import Link from "next/link";

import { serverGet } from "@/lib/serverApi";

type Article = {
  title: string;
  slug: string;
  summary: string;
  hero_image_url: string;
  is_video: boolean;
  source: string;
  reading_minutes: number;
  published_at: string;
  category: { name: string; slug: string };
};

type Photo = {
  id: string;
  title: string;
  image_url: string;
  caption: string | null;
  published_at: string;
};

type Deal = {
  id: string;
  title: string;
  image_url: string;
  provider: string;
  price_usd: number | null;
  badge: string | null;
  cta_url: string;
};

async function getArticles(category: string, limit: number) {
  return serverGet<Article[]>(
    `/content/articles?category=${encodeURIComponent(category)}&limit=${limit}`,
  );
}

async function getPhotos(limit: number) {
  return serverGet<Photo[]>(`/content/photos?limit=${limit}&offset=0`);
}

async function getDeals(limit: number) {
  return serverGet<Deal[]>(`/content/deals?limit=${limit}&offset=0`);
}

export default function Home() {
  const topStoriesPromise = getArticles("top-stories", 6);
  const latestPromise = getArticles("latest-news", 6);
  const recommendedPromise = getArticles("recommended", 6);
  const photosPromise = getPhotos(6);
  const dealsPromise = getDeals(6);
  const editorsPromise = getArticles("editors-picks", 4);
  const staySafePromise = getArticles("stay-safe", 3);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_330px]">
      <div className="twc-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">Top Stories</h2>
          <Link
            href="/news"
            className="text-xs font-semibold text-[#0b5672] hover:underline"
          >
            See More
          </Link>
        </div>

        <TopStories topStoriesPromise={topStoriesPromise} />

        <div className="mt-6 mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">Latest News</h2>
          <Link
            href="/news"
            className="text-xs font-semibold text-[#0b5672] hover:underline"
          >
            See More
          </Link>
        </div>

        <LatestNews latestPromise={latestPromise} />

        <div className="mt-7 mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">
            Weather Today Across the Country
          </h2>
          <Link
            href="/today"
            className="text-xs font-semibold text-[#0b5672] hover:underline"
          >
            See More
          </Link>
        </div>
        <UsMapModule />

        <div className="mt-7 mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">Recommended</h2>
          <Link
            href="/news"
            className="text-xs font-semibold text-[#0b5672] hover:underline"
          >
            See More
          </Link>
        </div>
        <Recommended recommendedPromise={recommendedPromise} />

        <div className="mt-7 mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">Photos</h2>
          <Link
            href="/photos"
            className="text-xs font-semibold text-[#0b5672] hover:underline"
          >
            See More
          </Link>
        </div>
        <PhotosStrip photosPromise={photosPromise} />

        <div className="mt-7 mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#0b1f2a]">
            Sponsored Content
          </h2>
        </div>
        <SponsoredDeals dealsPromise={dealsPromise} />
      </div>

      <aside className="space-y-4">
        <div className="twc-card p-4">
          <div className="text-sm font-semibold">New: Subscription Bundle</div>
          <div className="mt-2 text-xs text-black/60">
            Premium maps, fewer ads, and enhanced alerts.
          </div>
          <Link
            href="/subscribe"
            className="mt-3 inline-flex rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#0a4f67]"
          >
            View plans
          </Link>
        </div>

        <div className="twc-card p-4">
          <div className="mb-2 text-sm font-semibold">Editor&apos;s Picks</div>
          <SidebarArticles articlesPromise={editorsPromise} />
        </div>

        <div className="twc-card p-4">
          <div className="mb-2 text-sm font-semibold">Stay Safe</div>
          <SidebarArticles articlesPromise={staySafePromise} />
        </div>

        <div className="twc-card overflow-hidden">
          <div className="p-4">
            <div className="text-sm font-semibold">Stunning Sights in Nature</div>
            <div className="mt-1 text-xs text-black/60">
              Curated photos from our gallery.
            </div>
          </div>
          <Image
            src="https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80"
            alt="Nature"
            width={1200}
            height={700}
            className="h-[160px] w-full object-cover"
          />
          <div className="p-4 pt-3">
            <Link
              href="/photos"
              className="text-xs font-semibold text-[#0b5672] hover:underline"
            >
              Browse photos
            </Link>
          </div>
        </div>
      </aside>
    </div>
  );
}

async function TopStories({
  topStoriesPromise,
}: {
  topStoriesPromise: Promise<Article[]>;
}) {
  const items = await topStoriesPromise;
  const hero = items[0];
  const rest = items.slice(1);

  if (!hero) {
    return (
      <div className="text-sm text-black/60">
        No stories available yet. Run <code>./reset_servers.sh</code> to seed
        content.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-[1.15fr_0.85fr]">
      <Link
        href={`/news/${hero.slug}`}
        className="group overflow-hidden rounded-lg border border-black/10 bg-white"
      >
        <div className="relative">
          <Image
            src={hero.hero_image_url}
            alt={hero.title}
            width={1200}
            height={700}
            className="h-[230px] w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
            priority
          />
          {hero.is_video ? (
            <div className="absolute left-3 top-3 rounded bg-black/60 px-2 py-1 text-[11px] font-semibold text-white">
              Video
            </div>
          ) : null}
        </div>
        <div className="p-4">
          <div className="text-lg font-semibold leading-snug text-[#0b1f2a]">
            {hero.title}
          </div>
          <div className="mt-2 text-sm text-black/60">{hero.summary}</div>
        </div>
      </Link>

      <div className="space-y-3">
        {rest.map((a) => (
          <Link
            key={a.slug}
            href={`/news/${a.slug}`}
            className="flex gap-3 rounded-lg border border-black/10 bg-white p-3 hover:bg-black/[0.02]"
          >
            <Image
              src={a.hero_image_url}
              alt={a.title}
              width={240}
              height={160}
              className="h-[70px] w-[110px] rounded-md object-cover"
            />
            <div className="min-w-0">
              <div className="line-clamp-2 text-sm font-semibold text-[#0b1f2a]">
                {a.title}
              </div>
              <div className="mt-1 text-xs text-black/50">{a.category.name}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

async function LatestNews({
  latestPromise,
}: {
  latestPromise: Promise<Article[]>;
}) {
  const items = await latestPromise;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((a) => (
        <Link
          key={a.slug}
          href={`/news/${a.slug}`}
          className="group overflow-hidden rounded-lg border border-black/10 bg-white"
        >
          <Image
            src={a.hero_image_url}
            alt={a.title}
            width={900}
            height={600}
            className="h-[110px] w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
          <div className="p-3">
            <div className="line-clamp-2 text-sm font-semibold text-[#0b1f2a]">
              {a.title}
            </div>
            <div className="mt-1 line-clamp-2 text-xs text-black/60">
              {a.summary}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

function UsMapModule() {
  return (
    <div className="overflow-hidden rounded-lg border border-black/10 bg-white">
      <Image
        src="/us-map.png"
        alt="Weather Today Across the Country"
        width={770}
        height={395}
        className="h-auto w-full object-cover"
      />
    </div>
  );
}

async function Recommended({
  recommendedPromise,
}: {
  recommendedPromise: Promise<Article[]>;
}) {
  const items = await recommendedPromise;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((a) => (
        <Link
          key={a.slug}
          href={`/news/${a.slug}`}
          className="rounded-lg border border-black/10 bg-white p-4 hover:bg-black/[0.02]"
        >
          <div className="line-clamp-2 text-sm font-semibold text-[#0b1f2a]">
            {a.title}
          </div>
          <div className="mt-2 line-clamp-3 text-xs text-black/60">
            {a.summary}
          </div>
        </Link>
      ))}
    </div>
  );
}

async function PhotosStrip({ photosPromise }: { photosPromise: Promise<Photo[]> }) {
  const items = await photosPromise;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((p) => (
        <Link
          key={p.id}
          href="/photos"
          className="overflow-hidden rounded-lg border border-black/10 bg-white hover:bg-black/[0.02]"
        >
          <Image
            src={p.image_url}
            alt={p.title}
            width={600}
            height={400}
            className="h-[90px] w-full object-cover"
          />
          <div className="p-2">
            <div className="line-clamp-2 text-[11px] font-semibold text-[#0b1f2a]">
              {p.title}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

async function SponsoredDeals({ dealsPromise }: { dealsPromise: Promise<Deal[]> }) {
  const items = await dealsPromise;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
            width={900}
            height={600}
            className="h-[140px] w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
          <div className="p-3">
            <div className="line-clamp-2 text-xs font-semibold text-[#0b1f2a]">
              {d.title}
            </div>
            <div className="mt-1 text-[11px] text-black/55">
              {d.provider}
              {d.price_usd !== null ? ` • $${d.price_usd.toFixed(2)}` : ""}
              {d.badge ? ` • ${d.badge}` : ""}
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}

async function SidebarArticles({
  articlesPromise,
}: {
  articlesPromise: Promise<Article[]>;
}) {
  const items = await articlesPromise;
  return (
    <div className="space-y-2">
      {items.map((a) => (
        <Link
          key={a.slug}
          href={`/news/${a.slug}`}
          className="block rounded-lg border border-black/10 bg-white p-3 hover:bg-black/[0.02]"
        >
          <div className="line-clamp-2 text-xs font-semibold text-[#0b1f2a]">
            {a.title}
          </div>
          <div className="mt-1 text-[11px] text-black/55">{a.category.name}</div>
        </Link>
      ))}
    </div>
  );
}
