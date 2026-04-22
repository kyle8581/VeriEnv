import Image from "next/image";
import Link from "next/link";

import { apiGet } from "@/lib/api";

export default async function CourseDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const course = await apiGet<{
    id: number;
    title: string;
    slug: string;
    headline: string;
    description: string;
    level: string;
    language: string;
    duration_hours: number;
    skills_csv: string;
    image_url: string;
    partner: { id: number; name: string; slug: string; kind: string; logo_url: string };
  }>(`/api/courses/${encodeURIComponent(slug)}`, { cache: "no-store" });

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <Link href="/courses" className="text-sm font-semibold text-[#0056D2] hover:underline">
          Back to course catalog
        </Link>

        <div className="mt-6 grid gap-10 md:grid-cols-[1.2fr_1fr]">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
              {course.partner.name}
            </div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{course.title}</h1>
            <p className="mt-4 text-sm leading-6 text-zinc-600">{course.headline}</p>

            <div className="mt-6 flex flex-wrap gap-2 text-xs text-zinc-600">
              <span className="rounded bg-zinc-100 px-2 py-1">{course.level}</span>
              <span className="rounded bg-zinc-100 px-2 py-1">{course.language}</span>
              <span className="rounded bg-zinc-100 px-2 py-1">{course.duration_hours} hours</span>
            </div>

            <div className="mt-8 space-y-4 text-sm leading-7 text-zinc-700">
              {course.description.split("\n").map((p, idx) => (
                <p key={idx}>{p}</p>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="relative h-56 w-full overflow-hidden rounded border border-zinc-200">
              <Image src={course.image_url} alt={course.title} fill className="object-cover" />
            </div>
            <div className="rounded border border-zinc-200 bg-white p-5">
              <div className="text-sm font-semibold text-zinc-900">Skills you’ll gain</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {course.skills_csv
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .slice(0, 10)
                  .map((s) => (
                    <span key={s} className="rounded bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                      {s}
                    </span>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

