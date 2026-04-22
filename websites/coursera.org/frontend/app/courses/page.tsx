import Image from "next/image";
import Link from "next/link";

import { apiGet } from "@/lib/api";

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; partner?: string; level?: string }>;
}) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  if (sp.q) qs.set("q", sp.q);
  if (sp.partner) qs.set("partner", sp.partner);
  if (sp.level) qs.set("level", sp.level);
  qs.set("limit", "24");

  const data = await apiGet<{
    items: {
      id: number;
      title: string;
      slug: string;
      headline: string;
      level: string;
      language: string;
      duration_hours: number;
      skills_csv: string;
      image_url: string;
      partner_name: string;
      partner_slug: string;
    }[];
    total: number;
  }>(`/api/courses?${qs.toString()}`, { cache: "no-store" });

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Course Catalog</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          Browse courses from leading universities and industry partners.
        </p>

        <form className="mt-8 grid gap-3 md:grid-cols-[1fr_220px_220px_120px]">
          <input
            name="q"
            defaultValue={sp.q ?? ""}
            placeholder="Search courses"
            className="h-10 rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
          />
          <input
            name="partner"
            defaultValue={sp.partner ?? ""}
            placeholder="Partner slug (optional)"
            className="h-10 rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
          />
          <select
            name="level"
            defaultValue={sp.level ?? ""}
            className="h-10 rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
          >
            <option value="">Any level</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
          <button
            type="submit"
            className="h-10 rounded bg-[#0056D2] px-4 text-sm font-semibold text-white hover:bg-[#004bb8]"
          >
            Search
          </button>
        </form>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {data.items.map((c) => (
            <Link
              key={c.id}
              href={`/courses/${c.slug}`}
              className="group overflow-hidden rounded border border-zinc-200 bg-white"
            >
              <div className="relative h-40 w-full">
                <Image
                  src={c.image_url}
                  alt={c.title}
                  fill
                  className="object-cover transition group-hover:scale-[1.02]"
                />
              </div>
              <div className="p-5">
                <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  {c.partner_name}
                </div>
                <div className="mt-2 text-sm font-semibold text-zinc-900">{c.title}</div>
                <div className="mt-2 text-sm leading-6 text-zinc-600 line-clamp-2">{c.headline}</div>
                <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-600">
                  <span className="rounded bg-zinc-100 px-2 py-1">{c.level}</span>
                  <span className="rounded bg-zinc-100 px-2 py-1">{c.language}</span>
                  <span className="rounded bg-zinc-100 px-2 py-1">{c.duration_hours}h</span>
                </div>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-8 text-sm text-zinc-600">
          Showing {data.items.length} of {data.total}
        </div>
      </div>
    </div>
  );
}

