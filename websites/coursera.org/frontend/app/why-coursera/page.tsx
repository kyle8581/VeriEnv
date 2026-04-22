import Link from "next/link";

export default function WhyCourseraPage() {
  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Why Coursera</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">
          Learn how Coursera for Campus helps institutions build career-ready programs with world-class content,
          credentials, and insights.
        </p>
        <div className="mt-8 flex gap-3">
          <Link href="/contact" className="text-sm font-semibold text-[#0056D2] hover:underline">
            Contact us
          </Link>
          <Link href="/courses" className="text-sm font-semibold text-[#0056D2] hover:underline">
            Explore catalog
          </Link>
        </div>
      </div>
    </div>
  );
}

