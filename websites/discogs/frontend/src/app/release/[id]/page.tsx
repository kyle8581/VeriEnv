import Image from "next/image";

import { apiGet } from "@/lib/api";
import { ReleaseActions } from "@/components/ReleaseActions";

export const dynamic = "force-dynamic";

function fmtDuration(secs?: number | null) {
  if (!secs) return "";
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default async function ReleasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const r = await apiGet<{
    id: number;
    title: string;
    year: number | null;
    released_date: string | null;
    country: string | null;
    notes: string | null;
    cover_image_url: string | null;
    artists: { name: string; role: string }[];
    labels: { name: string; catalog_no: string | null }[];
    genres: string[];
    styles: string[];
    formats: { name: string; qty: number; text: string | null }[];
    tracks: { position: string; title: string; duration_seconds: number | null }[];
    have_count: number;
    want_count: number;
    for_sale_count: number;
    lowest_price_cents: number | null;
    currency: string;
  }>(`/releases/${id}`);

  const mainArtist = r.artists.find((a) => a.role === "Main")?.name;

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3 py-5">
        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          {/* Left: cover + actions */}
          <div>
            <div className="overflow-hidden rounded-sm border border-neutral-200 bg-white">
              <div className="relative aspect-square w-full bg-neutral-100">
                {r.cover_image_url ? (
                  <Image
                    src={r.cover_image_url}
                    alt={r.title}
                    fill
                    className="object-cover"
                    sizes="300px"
                  />
                ) : null}
              </div>
            </div>
            <ReleaseActions
              releaseId={r.id}
              forSaleCount={r.for_sale_count}
              haveCount={r.have_count}
              wantCount={r.want_count}
            />
          </div>

          {/* Right: main content */}
          <div>
            <div className="flex flex-col gap-1">
              <div className="text-lg font-bold text-neutral-900">
                {mainArtist ? `${mainArtist} - ` : ""}
                {r.title}
              </div>
              <div className="text-sm text-neutral-600">
                {r.year ? r.year : null}
              </div>
            </div>

            {/* Summary stats */}
            <div className="mt-4 grid gap-3 rounded-sm border border-neutral-200 bg-white p-3 sm:grid-cols-3">
              <div>
                <div className="text-xs text-neutral-500">Have</div>
                <div className="text-sm font-semibold text-neutral-900">
                  {r.have_count}
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-500">Want</div>
                <div className="text-sm font-semibold text-neutral-900">
                  {r.want_count}
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-500">For Sale</div>
                <div className="text-sm font-semibold text-neutral-900">
                  {r.for_sale_count}
                  {r.lowest_price_cents != null ? (
                    <span className="ml-2 text-xs font-normal text-neutral-600">
                      from ${(r.lowest_price_cents / 100).toFixed(2)}
                    </span>
                  ) : null}
                </div>
              </div>
            </div>

            {/* Metadata table */}
            <div className="mt-4 rounded-sm border border-neutral-200 bg-white">
              <div className="border-b border-neutral-200 px-3 py-2 text-xs font-semibold text-neutral-800">
                Release Information
              </div>
              <div className="grid gap-x-6 gap-y-2 px-3 py-3 text-sm sm:grid-cols-2">
                <div className="text-xs text-neutral-500">Label</div>
                <div className="text-xs text-neutral-800">
                  {r.labels.map((l) => `${l.name}${l.catalog_no ? ` — ${l.catalog_no}` : ""}`).join(", ")}
                </div>
                <div className="text-xs text-neutral-500">Format</div>
                <div className="text-xs text-neutral-800">
                  {r.formats.map((f) => `${f.qty} x ${f.name}${f.text ? `, ${f.text}` : ""}`).join(" • ")}
                </div>
                <div className="text-xs text-neutral-500">Country</div>
                <div className="text-xs text-neutral-800">{r.country || "-"}</div>
                <div className="text-xs text-neutral-500">Released</div>
                <div className="text-xs text-neutral-800">
                  {r.released_date || "-"}
                </div>
                <div className="text-xs text-neutral-500">Genre</div>
                <div className="text-xs text-neutral-800">
                  {r.genres.join(", ")}
                </div>
                <div className="text-xs text-neutral-500">Style</div>
                <div className="text-xs text-neutral-800">
                  {r.styles.join(", ")}
                </div>
              </div>
            </div>

            {/* Tracklist */}
            <div className="mt-4 rounded-sm border border-neutral-200 bg-white">
              <div className="border-b border-neutral-200 px-3 py-2 text-xs font-semibold text-neutral-800">
                Tracklist
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-neutral-500">
                    <th className="px-3 py-2 font-semibold">Position</th>
                    <th className="px-3 py-2 font-semibold">Title</th>
                    <th className="px-3 py-2 text-right font-semibold">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {r.tracks.map((t) => (
                    <tr key={t.position + t.title} className="border-t border-neutral-100">
                      <td className="px-3 py-2 text-neutral-600">{t.position}</td>
                      <td className="px-3 py-2 text-neutral-900">{t.title}</td>
                      <td className="px-3 py-2 text-right text-neutral-600">
                        {fmtDuration(t.duration_seconds)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Notes */}
            {r.notes ? (
              <div className="mt-4 rounded-sm border border-neutral-200 bg-white p-3">
                <div className="text-xs font-semibold text-neutral-800">Notes</div>
                <div className="mt-2 whitespace-pre-line text-sm leading-6 text-neutral-700">
                  {r.notes}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}

