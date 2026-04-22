import Link from "next/link";

import { apiGet } from "@/lib/api";
import { EbookLeadForm } from "@/components/resources/EbookLeadForm";

export default async function ResourceDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const res = await apiGet<{
    id: number;
    kind: string;
    title: string;
    slug: string;
    summary: string;
    body_md: string;
    hero_image_url: string;
    cta_label: string;
  }>(`/api/resources/${encodeURIComponent(slug)}`, { cache: "no-store" });

  // Reference page: Job Skills of 2023 Report (ebook form layout)
  if (res.slug === "job-skills-of-2023-report") {
    return (
      <div className="bg-white">
        <div className="bg-zinc-100/70">
          <div className="mx-auto max-w-6xl px-4 py-12">
            <div className="text-xs font-semibold tracking-wide text-zinc-600">EBOOK</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-zinc-900">
              {res.title}
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-600">{res.summary}</p>
          </div>
        </div>

        <div className="mx-auto max-w-6xl px-4 py-12">
          <div className="grid gap-10 md:grid-cols-[1fr_420px]">
            <div className="max-w-xl">
              <p className="text-sm leading-6 text-zinc-700">
                Explore the fastest-growing human and digital skills for 2023 and understand which skills you can
                prioritize to strengthen student employment outcomes.
              </p>
              <p className="mt-4 text-sm leading-6 text-zinc-700">
                This report draws on data specifically from Coursera’s 4 million enterprise learners across 3,000
                businesses, 3,600 higher education institutions, and governments in over 100 countries.
              </p>
              <p className="mt-4 text-sm leading-6 text-zinc-700">Download your report.</p>
            </div>

            <EbookLeadForm resourceSlug={res.slug} />
          </div>
        </div>
      </div>
    );
  }

  // Generic resource page
  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{res.kind}</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{res.title}</h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-600">{res.summary}</p>
        <div className="mt-6">
          <Link href="/resources" className="text-sm font-semibold text-[#0056D2] hover:underline">
            Back to resources
          </Link>
        </div>

        {res.body_md ? (
          <div className="mt-10 max-w-3xl space-y-4 text-sm leading-7 text-zinc-700">
            {res.body_md.split("\n").map((line, idx) => (
              <p key={idx}>{line}</p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

