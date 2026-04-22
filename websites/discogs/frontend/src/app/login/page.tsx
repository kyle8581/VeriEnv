import { Suspense } from "react";

import { LoginClient } from "./LoginClient";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <main className="page">
      <Suspense
        fallback={
          <div className="mx-auto max-w-[520px] px-3 py-10">
            <div className="rounded-sm border border-neutral-200 bg-white p-5 text-sm text-neutral-600">
              Loading…
            </div>
          </div>
        }
      >
        <LoginClient />
      </Suspense>
    </main>
  );
}

