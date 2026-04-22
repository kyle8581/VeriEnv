"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet } from "@/lib/api";
import { loadTokens } from "@/lib/auth";

type Plan = {
  id: string;
  name: string;
  price_monthly_usd: number;
  description: string;
  features: string[];
};

type Subscription = {
  id: string;
  status: string;
  started_at: string;
  ends_at: string | null;
  plan: Plan;
};

export default function SubscribePage() {
  const tokens = typeof window !== "undefined" ? loadTokens() : null;
  const [plans, setPlans] = useState<Plan[]>([]);
  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(false);
  const authed = useMemo(() => !!tokens?.access_token, [tokens?.access_token]);

  async function load() {
    const p = await apiGet<Plan[]>("/subscriptions/plans");
    setPlans(p);
    if (tokens) {
      try {
        const s = await apiGet<Subscription | null>("/me/subscription", {
          headers: { Authorization: `Bearer ${tokens.access_token}` },
        });
        setSub(s);
      } catch {
        setSub(null);
      }
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function subscribe(planId: string) {
    if (!tokens) return;
    setLoading(true);
    try {
      const s = await apiGet<Subscription>("/me/subscription/subscribe", {
        method: "POST",
        headers: { Authorization: `Bearer ${tokens.access_token}` },
        body: JSON.stringify({ plan_id: planId }),
      });
      setSub(s);
    } finally {
      setLoading(false);
    }
  }

  async function cancel() {
    if (!tokens) return;
    setLoading(true);
    try {
      await apiGet<{ status: string }>("/me/subscription/cancel", {
        method: "POST",
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setSub(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="twc-card p-5">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Subscribe</h1>
      <div className="mt-2 text-sm text-black/60">
        Choose a plan to personalize your experience.
      </div>

      {!authed ? (
        <div className="mt-4 rounded-lg border border-black/10 bg-white p-4 text-sm text-black/60">
          You&apos;re not signed in.{" "}
          <Link href="/account/sign-in" className="font-semibold text-[#0b5672]">
            Sign in
          </Link>{" "}
          to subscribe, or{" "}
          <Link href="/account/sign-up" className="font-semibold text-[#0b5672]">
            create an account
          </Link>
          .
        </div>
      ) : sub ? (
        <div className="mt-4 rounded-lg border border-black/10 bg-white p-4">
          <div className="text-sm font-semibold text-[#0b1f2a]">
            Current plan: {sub.plan.name}
          </div>
          <div className="mt-1 text-xs text-black/60">
            Status: {sub.status}
          </div>
          <button
            disabled={loading}
            onClick={() => void cancel()}
            className="mt-3 inline-flex rounded-full border border-black/10 bg-white px-3 py-1.5 text-xs font-semibold text-black/70 hover:bg-black/[0.03] disabled:opacity-60"
          >
            Cancel subscription
          </button>
        </div>
      ) : null}

      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        {plans.map((p) => (
          <div key={p.id} className="rounded-lg border border-black/10 bg-white p-4">
            <div className="text-sm font-semibold">{p.name}</div>
            <div className="mt-1 text-xs text-black/60">
              ${p.price_monthly_usd.toFixed(2)} / month
            </div>
            <div className="mt-2 text-xs text-black/60">{p.description}</div>
            <ul className="mt-3 space-y-2 text-xs text-black/70">
              {p.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>

            {authed ? (
              <button
                disabled={loading}
                onClick={() => void subscribe(p.id)}
                className="mt-4 inline-flex rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#0a4f67] disabled:opacity-60"
              >
                Choose {p.name}
              </button>
            ) : (
              <Link
                href="/account/sign-in"
                className="mt-4 inline-flex rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#0a4f67]"
              >
                Sign in to choose
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

