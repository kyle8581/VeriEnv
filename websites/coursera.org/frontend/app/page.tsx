import Image from "next/image";
import Link from "next/link";
import { apiGet } from "@/lib/api";

export default async function Home() {
  const partners = await apiGet<
    { id: number; name: string; slug: string; logo_url: string; kind: string }[]
  >("/api/partners", { cache: "no-store" }).catch(() => []);
  const resources = await apiGet<{
    items: { id: number; title: string; slug: string; summary: string; hero_image_url: string; cta_label: string }[];
    total: number;
  }>("/api/resources?limit=6", { cache: "no-store" }).catch(() => ({ items: [], total: 0 }));

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4">
        {/* Hero */}
        <section className="grid items-center gap-10 py-10 md:grid-cols-2 md:py-14">
          <div>
            <h1 className="text-4xl font-semibold leading-tight tracking-tight text-zinc-900 md:text-5xl">
              Strengthen employability to attract more students
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-zinc-600">
              Equip students with the most in-demand skills and prepare them for job success.
            </p>
            <div className="mt-7 flex items-center gap-4">
              <Link
                href="/contact"
                className="inline-flex h-11 items-center justify-center rounded bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
              >
                Contact us
              </Link>
              <Link href="/why-coursera" className="text-sm font-semibold text-[#0056D2] hover:underline">
                Learn more
              </Link>
            </div>

            <div className="mt-10 grid gap-4 rounded bg-zinc-900 px-6 py-6 text-white md:grid-cols-3">
              <div>
                <div className="text-2xl font-semibold">76%</div>
                <div className="mt-1 text-xs leading-5 text-zinc-200">
                  of learners report career benefits after completing courses.
                </div>
              </div>
              <div>
                <div className="text-2xl font-semibold">85%</div>
                <div className="mt-1 text-xs leading-5 text-zinc-200">
                  say the platform helped them develop job-relevant skills.
                </div>
              </div>
              <div>
                <div className="text-2xl font-semibold">90%</div>
                <div className="mt-1 text-xs leading-5 text-zinc-200">
                  feel more confident applying what they learned.
                </div>
              </div>
            </div>
          </div>

          <div className="relative h-[320px] w-full overflow-hidden rounded md:h-[420px]">
            <Image
              src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1600&q=80"
              alt="Students collaborating"
              fill
              priority
              className="object-cover"
            />
          </div>
        </section>

        {/* Partners */}
        <section className="grid gap-10 border-t border-zinc-200 py-12 md:grid-cols-[1.25fr_1fr]">
          <div>
            <h2 className="text-2xl font-semibold leading-snug text-zinc-900">
              Offer students 5,400 courses from 275+ leading universities and industry partners
            </h2>
          </div>
          <div className="grid grid-cols-4 gap-3">
            {partners.slice(0, 24).map((p) => (
              <div
                key={p.id}
                className="flex h-14 items-center justify-center rounded border border-zinc-200 bg-white p-2"
                title={p.name}
              >
                <Image
                  src={p.logo_url}
                  alt={p.name}
                  width={120}
                  height={48}
                  className="max-h-10 w-auto object-contain"
                />
              </div>
            ))}
          </div>
        </section>

        {/* Course catalog feature */}
        <section className="grid items-center gap-10 border-t border-zinc-200 py-14 md:grid-cols-2">
          <div className="relative h-[280px] w-full overflow-hidden rounded md:h-[360px]">
            <Image
              src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1600&q=80"
              alt="Learning in a classroom"
              fill
              className="object-cover"
            />
          </div>
          <div>
            <div className="text-xs font-semibold tracking-wide text-zinc-500">COURSE CATALOG</div>
            <h3 className="mt-3 text-3xl font-semibold leading-tight text-zinc-900">
              Prepare your students for in-demand jobs
            </h3>
            <ul className="mt-5 space-y-3 text-sm leading-6 text-zinc-600">
              <li>Build career readiness with professional certificates and skill-based learning.</li>
              <li>Offer high-quality content from top universities and industry partners.</li>
              <li>Track learning outcomes with insights that help you support student success.</li>
            </ul>
            <div className="mt-5">
              <Link href="/courses" className="text-sm font-semibold text-[#0056D2] hover:underline">
                Explore course catalog and credentials
              </Link>
            </div>
          </div>
        </section>
      </div>

      {/* Blue band */}
      <section className="bg-[#0B4DB8]">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <div className="grid gap-10 md:grid-cols-[1.2fr_1fr]">
            <div>
              <h3 className="text-3xl font-semibold leading-tight text-white">
                Expand your curriculum and empower your faculty
              </h3>
              <p className="mt-4 max-w-xl text-sm leading-6 text-blue-100">
                Provide flexible learning pathways with hands-on content, analytics, and tools that support teaching and
                learning across disciplines.
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {[
                { title: "Hands-on content and tools", desc: "Projects, labs, and assessments to reinforce learning." },
                { title: "Enable insights", desc: "Track engagement and progress with reporting." },
                { title: "Global insights", desc: "Benchmark skills and outcomes across programs." },
              ].map((c) => (
                <div key={c.title} className="rounded bg-white/10 p-4">
                  <div className="text-sm font-semibold text-white">{c.title}</div>
                  <div className="mt-2 text-xs leading-5 text-blue-100">{c.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4">
        {/* Trust strip */}
        <section className="py-8">
          <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-600">
            <span className="font-medium text-zinc-700">
              Join colleges and universities worldwide that choose Coursera for Campus
            </span>
            <span className="h-5 w-px bg-zinc-300" aria-hidden="true" />
            <span className="text-zinc-500">Trusted by institutions globally</span>
          </div>
        </section>

        {/* Proof */}
        <section className="border-t border-zinc-200 py-14">
          <h3 className="text-2xl font-semibold text-zinc-900">
            Here’s how innovative universities are using Coursera for Campus
          </h3>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-600">
            Institutions can offer students flexible, high-quality education that teaches the career-ready skills needed
            today—while improving outcomes and supporting retention.
          </p>
          <div className="mt-8 rounded border border-zinc-200 bg-white p-6">
            <div className="text-sm leading-7 text-zinc-700">
              “Coursera for Campus helped us expand access to in-demand skills and align learning pathways with employer
              needs.”
            </div>
            <div className="mt-3 text-xs font-semibold text-zinc-500">Academic Program Director</div>
          </div>
        </section>
      </div>

      {/* Dark CTA */}
      <section className="bg-zinc-900">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <div className="grid items-center gap-8 md:grid-cols-[1.4fr_1fr]">
            <div>
              <h3 className="text-3xl font-semibold text-white">Help prepare career-ready graduates</h3>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-200">
                Whatever your goals, we’ll help you build a curriculum and empower students and faculty with Coursera for
                Campus.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              <Link
                href="/contact"
                className="inline-flex h-11 items-center justify-center rounded bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
              >
                Contact us
              </Link>
              <Link
                href="/compare-plans"
                className="inline-flex h-11 items-center justify-center rounded border border-zinc-300 bg-transparent px-6 text-sm font-semibold text-white hover:bg-white/10"
              >
                Compare plans
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Resources */}
      <div className="mx-auto max-w-6xl px-4">
        <section className="py-14">
          <div className="grid gap-6 md:grid-cols-2">
            {resources.items.slice(0, 2).map((r) => (
              <Link
                key={r.id}
                href={`/resources/${r.slug}`}
                className="group relative overflow-hidden rounded border border-zinc-200 bg-white"
              >
                <div className="relative h-40 w-full">
                  <Image src={r.hero_image_url} alt={r.title} fill className="object-cover transition group-hover:scale-[1.02]" />
                </div>
                <div className="p-6">
                  <div className="text-sm font-semibold text-zinc-900">{r.title}</div>
                  <div className="mt-2 text-sm leading-6 text-zinc-600 line-clamp-2">{r.summary}</div>
                  <div className="mt-4 text-sm font-semibold text-[#0056D2]">{r.cta_label}</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
