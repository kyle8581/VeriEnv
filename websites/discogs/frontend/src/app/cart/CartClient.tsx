"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type Cart = {
  items: {
    id: number;
    quantity: number;
    listing: {
      listing_id: number;
      release_id: number;
      release_title: string;
      seller_username: string;
      price_cents: number;
      currency: string;
    };
  }[];
  total_cents: number;
  currency: string;
};

function money(cents: number, currency: string) {
  return `${currency} ${(cents / 100).toFixed(2)}`;
}

export function CartClient() {
  const router = useRouter();
  const sp = useSearchParams();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const total = useMemo(() => cart?.total_cents ?? 0, [cart]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/cart");
      if (res.status === 401) {
        window.location.href = `/login?next=${encodeURIComponent("/cart")}`;
        return;
      }
      const data = (await res.json()) as Cart;
      if (!res.ok) throw new Error(JSON.stringify(data));
      setCart(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load cart");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      const add = sp.get("add");
      if (add) {
        try {
          setBusy(true);
          const res = await fetch("/api/cart/items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ listing_id: Number(add), quantity: 1 }),
          });
          if (res.status === 401) {
            window.location.href = `/login?next=${encodeURIComponent(`/cart?add=${add}`)}`;
            return;
          }
          router.replace("/cart");
        } finally {
          setBusy(false);
        }
      }
      await load();
    })();
  }, [router, sp]);

  return (
    <div className="mx-auto max-w-[1040px] px-3 py-5">
      <div className="text-lg font-bold text-neutral-900">Cart</div>
      <div className="mt-1 text-sm text-neutral-600">
        Items you&apos;ve added from the marketplace.
      </div>

      {loading ? (
        <div className="mt-6 rounded-sm border border-neutral-200 bg-white p-4 text-sm">
          Loading...
        </div>
      ) : error ? (
        <div className="mt-6 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_280px]">
          <section className="rounded-sm border border-neutral-200 bg-white">
            <div className="border-b border-neutral-200 px-3 py-2 text-xs font-semibold text-neutral-800">
              Items
            </div>
            <div className="divide-y divide-neutral-100">
              {(cart?.items || []).map((it) => (
                <div key={it.id} className="flex items-center gap-3 px-3 py-3">
                  <div className="min-w-0 flex-1">
                    <Link
                      className="text-sm font-semibold text-neutral-900 hover:underline"
                      href={`/release/${it.listing.release_id}`}
                    >
                      {it.listing.release_title}
                    </Link>
                    <div className="mt-0.5 text-xs text-neutral-600">
                      Seller: {it.listing.seller_username}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-neutral-900">
                      {money(it.listing.price_cents, it.listing.currency)}
                    </div>
                    <button
                      disabled={busy}
                      className="mt-1 text-xs text-neutral-600 hover:underline disabled:opacity-60"
                      onClick={async () => {
                        setBusy(true);
                        try {
                          const res = await fetch(`/api/cart/items/${it.id}`, {
                            method: "DELETE",
                          });
                          if (!res.ok) throw new Error(await res.text());
                          await load();
                        } catch (e: unknown) {
                          setError(
                            e instanceof Error ? e.message : "Failed to remove item",
                          );
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
              {(cart?.items || []).length === 0 ? (
                <div className="px-3 py-6 text-sm text-neutral-600">
                  Your cart is empty. Browse a release marketplace page and add a
                  listing.
                </div>
              ) : null}
            </div>
          </section>

          <aside className="rounded-sm border border-neutral-200 bg-white p-3">
            <div className="text-xs font-semibold text-neutral-800">Summary</div>
            <div className="mt-3 flex items-center justify-between text-sm">
              <div className="text-neutral-600">Total</div>
              <div className="font-semibold text-neutral-900">
                {money(total, cart?.currency || "USD")}
              </div>
            </div>
            <button
              disabled={busy || (cart?.items || []).length === 0}
              className="mt-4 h-10 w-full rounded-sm bg-neutral-900 px-3 text-sm font-semibold text-white hover:bg-neutral-800 disabled:opacity-60"
              onClick={async () => {
                setBusy(true);
                setError(null);
                try {
                  const res = await fetch("/api/checkout", { method: "POST" });
                  if (!res.ok) throw new Error(await res.text());
                  await load();
                  alert("Checkout complete (order created).");
                } catch (e: unknown) {
                  setError(e instanceof Error ? e.message : "Checkout failed");
                } finally {
                  setBusy(false);
                }
              }}
            >
              Checkout
            </button>
          </aside>
        </div>
      )}
    </div>
  );
}

