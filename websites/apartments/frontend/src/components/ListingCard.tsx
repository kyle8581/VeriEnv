"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import {
  addFavorite,
  createContactRequest,
  removeFavorite,
} from "@/lib/api";
import { getToken } from "@/lib/auth_client";
import type { Listing } from "@/lib/types";

function Heart({ filled }: { filled: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 21s-7.1-4.4-9.3-8.6C.9 8.5 3.2 5.5 6.5 5.2c1.7-.2 3.4.6 4.5 2 1.1-1.4 2.8-2.2 4.5-2 3.3.3 5.6 3.3 3.8 7.2C19.1 16.6 12 21 12 21Z"
        fill={filled ? "var(--apts-green)" : "none"}
        stroke={filled ? "var(--apts-green)" : "#6b6b6b"}
        strokeWidth="1.6"
      />
    </svg>
  );
}

function formatPriceRange(min: number, max: number) {
  return `$${min.toLocaleString()} - ${max.toLocaleString()}`;
}

function formatBeds(min: number, max: number) {
  if (min === 0 && max === 0) return "Studio";
  if (min === max) return `${min} Beds`;
  return `${min}-${max} Beds`;
}

export function ListingCard({
  listing,
  isFavoriteInitial,
  onFavoriteChange,
}: {
  listing: Listing;
  isFavoriteInitial: boolean;
  onFavoriteChange?: (next: boolean) => void;
}) {
  const images = listing.images ?? [];
  const [idx, setIdx] = useState(0);
  const [isFav, setIsFav] = useState(isFavoriteInitial);
  const [emailOpen, setEmailOpen] = useState(false);
  const [contactEmail, setContactEmail] = useState("");
  const [contactName, setContactName] = useState("");
  const [message, setMessage] = useState(
    "Hi, I’m interested in availability and pricing. Please contact me.",
  );
  const [emailStatus, setEmailStatus] = useState<string | null>(null);

  const cover = useMemo(() => images[idx]?.url ?? images[0]?.url ?? "", [images, idx]);

  return (
    <div className="border-b border-black/10 bg-white">
      <div className="flex items-start justify-between px-4 pt-4">
        <div className="min-w-0">
          <Link
            href={`/apartments/${listing.id}`}
            className="block truncate text-[18px] font-semibold text-[#2b2b2b] hover:underline"
          >
            {listing.name}
          </Link>
          <div className="mt-1 truncate text-[12px] text-[#666]">
            {listing.street}, {listing.city}, {listing.state} {listing.postal_code}
          </div>
        </div>
        <button
          type="button"
          className="ml-4 shrink-0"
          aria-label={isFav ? "Remove favorite" : "Add favorite"}
          onClick={async () => {
            const token = getToken();
            if (!token) {
              window.location.href = "/auth";
              return;
            }
            const next = !isFav;
            setIsFav(next);
            onFavoriteChange?.(next);
            try {
              if (next) await addFavorite(token, listing.id);
              else await removeFavorite(token, listing.id);
            } catch {
              // revert on error
              setIsFav(!next);
              onFavoriteChange?.(!next);
            }
          }}
        >
          <Heart filled={isFav} />
        </button>
      </div>

      <div className="relative mt-3 h-[168px] w-full bg-black/5">
        {cover ? (
          <Image
            src={cover}
            alt={listing.name}
            fill
            sizes="(max-width: 1100px) 100vw, 35vw"
            className="object-cover"
          />
        ) : null}

        {images.length > 1 ? (
          <>
            <button
              type="button"
              aria-label="Previous image"
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded-sm bg-black/35 px-2 py-1 text-white"
              onClick={() => setIdx((v) => (v - 1 + images.length) % images.length)}
            >
              ‹
            </button>
            <button
              type="button"
              aria-label="Next image"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-sm bg-black/35 px-2 py-1 text-white"
              onClick={() => setIdx((v) => (v + 1) % images.length)}
            >
              ›
            </button>
          </>
        ) : null}

        <div className="absolute bottom-2 left-2 flex gap-2 text-[11px] text-white">
          {listing.has_videos ? (
            <span className="rounded-sm bg-black/55 px-2 py-1">Videos</span>
          ) : null}
          {listing.has_virtual_tour ? (
            <span className="rounded-sm bg-black/55 px-2 py-1">Virtual Tour</span>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 px-4 py-4 sm:grid-cols-[1fr_auto] sm:items-start">
        <div>
          <div className="text-[18px] font-semibold text-[#2b2b2b]">
            {formatPriceRange(listing.min_price, listing.max_price)}
          </div>
          <div className="mt-1 text-[14px] text-[#333]">
            {formatBeds(listing.min_beds, listing.max_beds)}
          </div>
          {listing.specials ? (
            <div className="mt-1 text-[12px] text-[#666]">Specials</div>
          ) : null}
          <div className="mt-2 line-clamp-2 text-[12px] text-[#666]">
            {listing.amenities?.slice(0, 6).map((a) => a.name).join(", ")}
          </div>
          <div className="mt-2 text-[14px] text-[#333]">{listing.phone}</div>
        </div>

        <button
          type="button"
          className="h-10 rounded-sm bg-apts-green px-8 text-[14px] font-semibold text-white"
          onClick={() => setEmailOpen(true)}
        >
          Email
        </button>
      </div>

      {emailOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-[520px] rounded-sm bg-white p-5 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[16px] font-semibold text-[#2b2b2b]">
                  Email {listing.name}
                </div>
                <div className="mt-1 text-[12px] text-[#666]">
                  {listing.street}, {listing.city}, {listing.state}
                </div>
              </div>
              <button
                type="button"
                className="text-[18px] leading-none text-[#666]"
                aria-label="Close"
                onClick={() => {
                  setEmailOpen(false);
                  setEmailStatus(null);
                }}
              >
                ×
              </button>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="block">
                <div className="text-[12px] font-semibold text-[#555]">Name</div>
                <input
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
                />
              </label>
              <label className="block">
                <div className="text-[12px] font-semibold text-[#555]">
                  Email
                </div>
                <input
                  required
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
                />
              </label>
            </div>
            <label className="mt-3 block">
              <div className="text-[12px] font-semibold text-[#555]">
                Message
              </div>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="mt-1 min-h-[110px] w-full rounded-sm border border-black/15 px-3 py-2 text-[14px] outline-none focus:ring-2 ring-apts-green"
              />
            </label>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                className="h-10 rounded-sm bg-apts-green px-6 text-[14px] font-semibold text-white"
                onClick={async () => {
                  setEmailStatus(null);
                  try {
                    const token = getToken() ?? undefined;
                    await createContactRequest({
                      listing_id: listing.id,
                      contact_email: contactEmail,
                      contact_name: contactName || undefined,
                      message,
                      token,
                    });
                    setEmailStatus("Sent! (Contact request saved.)");
                  } catch (e) {
                    setEmailStatus(e instanceof Error ? e.message : "Failed to send");
                  }
                }}
              >
                Send Email
              </button>
              {emailStatus ? (
                <div className="text-[12px] text-[#333]">{emailStatus}</div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

