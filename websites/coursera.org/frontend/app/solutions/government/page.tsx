import Link from "next/link";

export default function GovernmentSolutionsPage() {
  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Solutions for Government</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">
          Build workforce-ready skills at scale with curated learning programs and actionable insights.
        </p>
        <div className="mt-8">
          <Link href="/contact" className="text-sm font-semibold text-[#0056D2] hover:underline">
            Contact us
          </Link>
        </div>
      </div>
    </div>
  );
}

