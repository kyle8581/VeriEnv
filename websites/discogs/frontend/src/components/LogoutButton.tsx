"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  return (
    <button
      disabled={busy}
      className="block w-full rounded-sm px-2 py-1 text-left text-sm text-white/90 hover:bg-white/10 disabled:opacity-60"
      onClick={async () => {
        setBusy(true);
        try {
          await fetch("/api/auth/logout", { method: "POST" });
          router.refresh();
          router.push("/");
        } finally {
          setBusy(false);
        }
      }}
    >
      Sign out
    </button>
  );
}

