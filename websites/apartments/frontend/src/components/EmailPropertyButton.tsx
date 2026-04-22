"use client";

import { useState } from "react";

import { createContactRequest } from "@/lib/api";
import { getToken } from "@/lib/auth_client";

export function EmailPropertyButton({
  listingId,
  listingName,
  addressLine,
}: {
  listingId: number;
  listingName: string;
  addressLine: string;
}) {
  const [open, setOpen] = useState(false);
  const [contactEmail, setContactEmail] = useState("");
  const [contactName, setContactName] = useState("");
  const [message, setMessage] = useState(
    "Hi, I’m interested in availability and pricing. Please contact me.",
  );
  const [status, setStatus] = useState<string | null>(null);

  return (
    <>
      <button
        type="button"
        className="inline-flex h-10 w-full items-center justify-center rounded-sm bg-apts-green text-[14px] font-semibold text-white"
        onClick={() => setOpen(true)}
      >
        Email
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-[520px] rounded-sm bg-white p-5 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[16px] font-semibold text-[#2b2b2b]">
                  Email {listingName}
                </div>
                <div className="mt-1 text-[12px] text-[#666]">{addressLine}</div>
              </div>
              <button
                type="button"
                className="text-[18px] leading-none text-[#666]"
                aria-label="Close"
                onClick={() => {
                  setOpen(false);
                  setStatus(null);
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
                  setStatus(null);
                  try {
                    const token = getToken() ?? undefined;
                    await createContactRequest({
                      listing_id: listingId,
                      contact_email: contactEmail,
                      contact_name: contactName || undefined,
                      message,
                      token,
                    });
                    setStatus("Sent! (Contact request saved.)");
                  } catch (e) {
                    setStatus(e instanceof Error ? e.message : "Failed to send");
                  }
                }}
              >
                Send Email
              </button>
              {status ? (
                <div className="text-[12px] text-[#333]">{status}</div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

