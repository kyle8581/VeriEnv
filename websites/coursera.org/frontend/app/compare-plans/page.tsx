import Link from "next/link";

export default function ComparePlansPage() {
  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Compare Plans</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">
          Compare plan features to find the right fit for your institution.
        </p>

        <div className="mt-10 overflow-hidden rounded border border-zinc-200">
          <div className="grid grid-cols-3 bg-zinc-50 text-sm font-semibold text-zinc-900">
            <div className="p-4">Feature</div>
            <div className="p-4">Essentials</div>
            <div className="p-4">Enterprise</div>
          </div>
          {[
            ["Course catalog access", "✓", "✓"],
            ["Professional certificates", "✓", "✓"],
            ["Analytics & reporting", "—", "✓"],
            ["SSO / advanced security", "—", "✓"],
            ["Dedicated support", "—", "✓"],
          ].map((row) => (
            <div key={row[0]} className="grid grid-cols-3 border-t border-zinc-200 text-sm">
              <div className="p-4 text-zinc-700">{row[0]}</div>
              <div className="p-4 text-zinc-700">{row[1]}</div>
              <div className="p-4 text-zinc-700">{row[2]}</div>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/contact"
            className="inline-flex h-11 items-center justify-center rounded bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
          >
            Contact us
          </Link>
          <Link href="/courses" className="inline-flex h-11 items-center justify-center rounded border border-zinc-300 px-6 text-sm font-semibold text-zinc-900 hover:bg-zinc-50">
            Explore catalog
          </Link>
        </div>
      </div>
    </div>
  );
}

