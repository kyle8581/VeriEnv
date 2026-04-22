import Image from "next/image";
import Link from "next/link";

import type { Listing } from "@/lib/types";

function formatPriceRange(min: number, max: number) {
  return `$${min.toLocaleString()} - ${max.toLocaleString()}`;
}

function formatBeds(min: number, max: number) {
  if (min === 0 && max === 0) return "Studio";
  if (min === max) return `${min} Beds`;
  return `${min}-${max} Beds`;
}

export function ListingPreviewCard({ listing }: { listing: Listing }) {
  const img = listing.images?.[0]?.url ?? "";
  return (
    <Link
      href={`/apartments/${listing.id}`}
      className="block overflow-hidden rounded-sm border border-black/10 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_18px_rgba(0,0,0,0.12)]"
    >
      <div className="relative h-[120px] w-full bg-black/5">
        {img ? (
          <Image
            src={img}
            alt={listing.name}
            fill
            sizes="(max-width: 900px) 100vw, 25vw"
            className="object-cover"
          />
        ) : null}
      </div>
      <div className="px-3 py-3 text-[13px] text-[#333]">
        <div className="truncate text-[13px] font-semibold">{listing.name}</div>
        <div className="mt-1 line-clamp-2 text-[12px] text-[#666]">
          {listing.street}, {listing.city}, {listing.state} {listing.postal_code}
        </div>
        <div className="mt-2 text-[12px] text-[#666]">
          {formatBeds(listing.min_beds, listing.max_beds)} |{" "}
          {formatPriceRange(listing.min_price, listing.max_price)}
        </div>
      </div>
    </Link>
  );
}

