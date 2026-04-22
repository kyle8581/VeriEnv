import { SearchPageClient } from "@/components/SearchPageClient";
import { searchListings } from "@/lib/api";

export default async function ApartmentsPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const q =
    typeof searchParams.q === "string" && searchParams.q.trim()
      ? searchParams.q
      : "Boston, MA";
  const data = await searchListings({ q, limit: 25 }).catch(() => ({
    total: 0,
    items: [],
  }));
  return <SearchPageClient initialQuery={q} initialData={data} />;
}

