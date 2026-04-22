"use client";

import { useState } from "react";

const KEY = "discogs_clone_cookie_consent_v1";

export function CookieBanner() {
  const [visible, setVisible] = useState(() => {
    try {
      return localStorage.getItem(KEY) !== "accepted";
    } catch {
      return true;
    }
  });

  if (!visible) return null;

  return (
    <div className="border-b border-neutral-200 bg-white">
      <div className="mx-auto flex max-w-[1040px] flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-xs text-neutral-700">
          <span className="font-semibold">Let&apos;s manage your privacy</span>{" "}
          We use cookies to personalize content and ads, to provide social media
          features and to analyze our traffic.
        </div>
        <div className="flex gap-2">
          <button className="rounded border border-neutral-300 bg-white px-3 py-2 text-xs font-semibold text-neutral-800 hover:bg-neutral-50">
            Cookie Settings
          </button>
          <button
            className="rounded bg-neutral-900 px-3 py-2 text-xs font-semibold text-white hover:bg-neutral-800"
            onClick={() => {
              try {
                localStorage.setItem(KEY, "accepted");
              } catch {}
              setVisible(false);
            }}
          >
            Accept All Cookies
          </button>
        </div>
      </div>
    </div>
  );
}

