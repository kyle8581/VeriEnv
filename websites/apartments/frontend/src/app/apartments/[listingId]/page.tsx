import Image from "next/image";
import Link from "next/link";

import { Header } from "@/components/Header";
import { EmailPropertyButton } from "@/components/EmailPropertyButton";
import { getListing } from "@/lib/api";

export default async function ListingDetailPage({
  params,
}: {
  params: Promise<{ listingId: string }>;
}) {
  const { listingId } = await params;
  const id = Number(listingId);
  if (isNaN(id)) {
    throw new Error(`Invalid listing ID: ${listingId}`);
  }
  const listing = await getListing(id);
  const cover = listing.images?.[0]?.url ?? "";

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-[1200px] px-4 py-6">
        <div className="text-[12px] text-[#0b6fbf]">
          <Link className="hover:underline" href={`/apartments?q=${encodeURIComponent(`${listing.city}, ${listing.state}`)}`}>
            ← Back to results
          </Link>
        </div>

        <div className="mt-4 flex flex-col gap-6 lg:flex-row">
          <div className="flex-1">
            <h1 className="text-[28px] font-semibold text-[#2b2b2b]">
              {listing.name}
            </h1>
            <div className="mt-1 text-[13px] text-[#666]">
              {listing.street}, {listing.city}, {listing.state}{" "}
              {listing.postal_code}
            </div>

            <div className="mt-4 overflow-hidden rounded-sm border border-black/10">
              <div className="relative h-[320px] w-full bg-black/5">
                {cover ? (
                  <Image
                    src={cover}
                    alt={listing.name}
                    fill
                    sizes="(max-width: 1200px) 100vw, 70vw"
                    className="object-cover"
                  />
                ) : null}
              </div>
              <div className="grid grid-cols-3 gap-2 bg-white p-2">
                {listing.images?.slice(0, 6).map((img) => (
                  <div key={img.id} className="relative h-[90px] bg-black/5">
                    <Image
                      src={img.url}
                      alt=""
                      fill
                      sizes="(max-width: 1200px) 33vw, 200px"
                      className="object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 rounded-sm border border-black/10 p-5">
              <div className="text-[18px] font-semibold text-[#2b2b2b]">
                ${listing.min_price.toLocaleString()} -{" "}
                {listing.max_price.toLocaleString()}
              </div>
              <div className="mt-1 text-[14px] text-[#333]">
                {listing.min_beds === 0 && listing.max_beds === 0
                  ? "Studio"
                  : `${listing.min_beds}-${listing.max_beds} Beds`}
              </div>
              <div className="mt-4 text-[13px] leading-7 text-[#555]">
                {listing.description}
              </div>
            </div>
          </div>

          <aside className="w-full max-w-[360px] rounded-sm border border-black/10 p-5">
            <div className="text-[12px] text-[#666]">Managed by</div>
            <div className="text-[14px] font-semibold text-[#2b2b2b]">
              {listing.management_name}
            </div>
            <div className="mt-4 text-[12px] text-[#666]">Phone</div>
            <div className="text-[14px] text-[#333]">{listing.phone}</div>
            <div className="mt-6">
              <EmailPropertyButton
                listingId={listing.id}
                listingName={listing.name}
                addressLine={`${listing.street}, ${listing.city}, ${listing.state} ${listing.postal_code}`}
              />
            </div>
            <div className="mt-3 text-[12px] text-[#0b6fbf]">
              <Link
                className="hover:underline"
                href={`/apartments?q=${encodeURIComponent(`${listing.city}, ${listing.state}`)}`}
              >
                Back to Search
              </Link>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}

