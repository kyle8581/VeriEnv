"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiGet } from "@/lib/api";
import { saveTokens } from "@/lib/auth";

type AuthResponse = {
  access_token: string;
  access_expires_at: string;
  refresh_token: string;
  refresh_expires_at: string;
  token_type: string;
};

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiGet<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name: name || null }),
      });
      saveTokens(res);
      router.push("/account/saved-locations");
    } catch (err) {
      setError(
        typeof err === "object" && err && "message" in err
          ? String((err as { message: unknown }).message)
          : "Sign up failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="twc-card mx-auto max-w-[520px] p-5">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">Create Account</h1>
      <div className="mt-2 text-sm text-black/60">
        Create an account to save locations and personalize your experience.
      </div>

      <form onSubmit={onSubmit} className="mt-5 space-y-3">
        <label className="block">
          <div className="text-xs font-semibold text-black/60">Name</div>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-black/10 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#0b5672]/30"
            placeholder="Your name"
          />
        </label>

        <label className="block">
          <div className="text-xs font-semibold text-black/60">Email</div>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-black/10 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#0b5672]/30"
            placeholder="you@example.com"
            required
          />
        </label>

        <label className="block">
          <div className="text-xs font-semibold text-black/60">Password</div>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            className="mt-1 w-full rounded-md border border-black/10 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#0b5672]/30"
            placeholder="At least 8 characters"
            required
          />
        </label>

        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex w-full items-center justify-center rounded-full bg-[#0b5672] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0a4f67] disabled:opacity-60"
        >
          {loading ? "Creating…" : "Create Account"}
        </button>
      </form>

      <div className="mt-4 text-center text-xs text-black/60">
        Already have an account?{" "}
        <Link href="/account/sign-in" className="font-semibold text-[#0b5672]">
          Sign in
        </Link>
      </div>
    </div>
  );
}

