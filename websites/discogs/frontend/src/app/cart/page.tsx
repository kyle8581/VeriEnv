import { Suspense } from "react";

import { CartClient } from "./CartClient";

export const dynamic = "force-dynamic";

export default function CartPage() {
  return (
    <main className="page">
      <Suspense
        fallback={
          <div className="mx-auto max-w-[1040px] px-3 py-5">
            <div className="rounded-sm border border-neutral-200 bg-white p-4 text-sm text-neutral-600">
              Loading…
            </div>
          </div>
        }
      >
        <CartClient />
      </Suspense>
    </main>
  );
}

