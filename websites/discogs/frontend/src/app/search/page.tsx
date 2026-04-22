import { ReleaseCard } from "@/components/ReleaseCard";
import { apiGet } from "@/lib/api";
import type { ReleaseCard as ReleaseCardType } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q : "";

  const results: ReleaseCardType[] = q
    ? await apiGet<ReleaseCardType[]>(`/search?q=${encodeURIComponent(q)}`)
    : [];

  return (
    <main className="page">
      <div className="mx-auto max-w-[1040px] px-3 py-5">
        <div className="text-lg font-bold text-neutral-900">Search</div>
        <div className="mt-1 text-sm text-neutral-600">
          {q ? (
            <>
              Results for <span className="font-semibold">{q}</span>
            </>
          ) : (
            "Enter a query in the search bar."
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
          {results.map((r) => (
            <ReleaseCard key={r.id} release={r} />
          ))}
        </div>
      </div>
    </main>
  );
}

