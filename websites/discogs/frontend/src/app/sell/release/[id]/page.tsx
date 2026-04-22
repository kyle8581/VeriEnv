import Link from "next/link";

import { apiGet } from "@/lib/api";

export const dynamic = "force-dynamic";

function money(cents: number, currency: string) {
  return `${currency} ${(cents / 100).toFixed(2)}`;
}

export default async function MarketplaceReleasePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const sp = await searchParams;

  const qs = new URLSearchParams();
  const media_condition = typeof sp.media_condition === "string" ? sp.media_condition : undefined;
  const sleeve_condition = typeof sp.sleeve_condition === "string" ? sp.sleeve_condition : undefined;
  const ships_from = typeof sp.ships_from === "string" ? sp.ships_from : undefined;
  const min_rating = typeof sp.min_rating === "string" ? sp.min_rating : undefined;
  const sort = typeof sp.sort === "string" ? sp.sort : "price_asc";

  if (media_condition) qs.set("media_condition", media_condition);
  if (sleeve_condition) qs.set("sleeve_condition", sleeve_condition);
  if (ships_from) qs.set("ships_from", ships_from);
  if (min_rating) qs.set("min_rating", min_rating);
  if (sort) qs.set("sort", sort);

  const data = await apiGet<{
    release: { id: number; title: string; artist: string | null; cover_image_url: string | null };
    total: number;
    items: {
      id: number;
      seller: { username: string; seller_rating: number; location: string | null };
      ships_from: string;
      media_condition: string;
      sleeve_condition: string;
      price_cents: number;
      currency: string;
      quantity: number;
    }[];
  }>(`/releases/${id}/listings?${qs.toString()}`);

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3 py-5">
        <div className="flex flex-col gap-1">
          <div className="text-lg font-bold text-neutral-900">
            {data.release.artist ? `${data.release.artist} - ` : ""}
            {data.release.title}
          </div>
          <div className="text-xs text-neutral-600">
            Marketplace listings • {data.total} for sale
          </div>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[260px_1fr]">
          {/* Filters */}
          <aside className="rounded-sm border border-neutral-200 bg-white p-3">
            <div className="text-xs font-semibold text-neutral-800">Filter</div>
            <form className="mt-3 space-y-3 text-xs">
              <div>
                <div className="mb-1 text-neutral-600">Media Condition</div>
                <input
                  name="media_condition"
                  defaultValue={media_condition || ""}
                  className="h-8 w-full rounded-sm border border-neutral-300 px-2"
                />
              </div>
              <div>
                <div className="mb-1 text-neutral-600">Sleeve Condition</div>
                <input
                  name="sleeve_condition"
                  defaultValue={sleeve_condition || ""}
                  className="h-8 w-full rounded-sm border border-neutral-300 px-2"
                />
              </div>
              <div>
                <div className="mb-1 text-neutral-600">Ships From</div>
                <input
                  name="ships_from"
                  defaultValue={ships_from || ""}
                  className="h-8 w-full rounded-sm border border-neutral-300 px-2"
                />
              </div>
              <div>
                <div className="mb-1 text-neutral-600">Minimum Rating</div>
                <input
                  name="min_rating"
                  defaultValue={min_rating || ""}
                  className="h-8 w-full rounded-sm border border-neutral-300 px-2"
                />
              </div>
              <div>
                <div className="mb-1 text-neutral-600">Sort</div>
                <select
                  name="sort"
                  defaultValue={sort}
                  className="h-8 w-full rounded-sm border border-neutral-300 bg-white px-2"
                >
                  <option value="price_asc">Price (low to high)</option>
                  <option value="price_desc">Price (high to low)</option>
                  <option value="newest">Newest</option>
                </select>
              </div>

              <button className="w-full rounded-sm bg-neutral-900 px-3 py-2 font-semibold text-white hover:bg-neutral-800">
                Apply
              </button>
            </form>
          </aside>

          {/* Listings table */}
          <section className="rounded-sm border border-neutral-200 bg-white">
            <div className="border-b border-neutral-200 px-3 py-2 text-xs font-semibold text-neutral-800">
              Listings
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-neutral-500">
                  <th className="px-3 py-2 font-semibold">Seller</th>
                  <th className="px-3 py-2 font-semibold">Ships From</th>
                  <th className="px-3 py-2 font-semibold">Condition</th>
                  <th className="px-3 py-2 text-right font-semibold">Price</th>
                  <th className="px-3 py-2 text-right font-semibold"> </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((it) => (
                  <tr key={it.id} className="border-t border-neutral-100">
                    <td className="px-3 py-3">
                      <div className="font-semibold text-neutral-900">
                        {it.seller.username}
                      </div>
                      <div className="text-[11px] text-neutral-600">
                        {it.seller.seller_rating.toFixed(1)}% •{" "}
                        {it.seller.location || "—"}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-neutral-700">
                      {it.ships_from}
                    </td>
                    <td className="px-3 py-3 text-neutral-700">
                      {it.media_condition} / {it.sleeve_condition}
                    </td>
                    <td className="px-3 py-3 text-right font-semibold text-neutral-900">
                      {money(it.price_cents, it.currency)}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Link
                        href={`/cart?add=${it.id}`}
                        className="inline-flex items-center justify-center rounded-sm border border-neutral-300 bg-white px-2 py-1 font-semibold text-neutral-800 hover:bg-neutral-50"
                      >
                        Add to Cart
                      </Link>
                    </td>
                  </tr>
                ))}
                {data.items.length === 0 ? (
                  <tr>
                    <td className="px-3 py-6 text-sm text-neutral-600" colSpan={5}>
                      No listings match these filters.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </section>
        </div>

        {/* Thread placeholder */}
        <section className="mt-6 rounded-sm border border-neutral-200 bg-white p-3">
          <div className="text-xs font-semibold text-neutral-800">
            Discussion
          </div>
          <div className="mt-2 text-sm text-neutral-700">
            This section mirrors the reference page’s comment thread area.
          </div>
        </section>
      </div>
    </main>
  );
}

