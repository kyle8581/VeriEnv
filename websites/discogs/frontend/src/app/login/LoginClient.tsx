"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

export function LoginClient() {
  const router = useRouter();
  const sp = useSearchParams();
  const nextUrl = useMemo(() => sp.get("next") || "/", [sp]);

  const [usernameOrEmail, setUsernameOrEmail] = useState("demo");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="mx-auto max-w-[520px] px-3 py-10">
      <div className="rounded-sm border border-neutral-200 bg-white p-5">
        <div className="text-lg font-bold text-neutral-900">Sign in</div>
        <div className="mt-1 text-sm text-neutral-600">
          Use the seeded demo account:{" "}
          <span className="font-semibold">demo</span> /{" "}
          <span className="font-semibold">password123</span>
        </div>

        <form
          className="mt-5 space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            setError(null);
            setLoading(true);
            try {
              const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  username_or_email: usernameOrEmail,
                  password,
                }),
              });
              if (!res.ok) {
                const t = await res.text();
                throw new Error(t || `Login failed (${res.status})`);
              }
              router.replace(nextUrl);
            } catch (err: unknown) {
              setError(err instanceof Error ? err.message : "Login failed");
            } finally {
              setLoading(false);
            }
          }}
        >
          <div>
            <div className="mb-1 text-xs font-semibold text-neutral-700">
              Username or Email
            </div>
            <input
              value={usernameOrEmail}
              onChange={(e) => setUsernameOrEmail(e.target.value)}
              className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
            />
          </div>
          <div>
            <div className="mb-1 text-xs font-semibold text-neutral-700">
              Password
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10 w-full rounded-sm border border-neutral-300 px-3 text-sm"
            />
          </div>
          {error ? (
            <div className="rounded-sm border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </div>
          ) : null}
          <button
            disabled={loading}
            className="h-10 w-full rounded-sm bg-neutral-900 px-3 text-sm font-semibold text-white hover:bg-neutral-800 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

