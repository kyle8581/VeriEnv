"use client";

import { useEffect, useMemo, useState } from "react";

import { Header } from "@/components/Header";
import { login, me, register } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth_client";
import type { UserPublic } from "@/lib/types";

export default function AuthPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserPublic | null>(null);

  const token = useMemo(() => getToken(), []);

  useEffect(() => {
    const t = getToken();
    if (!t) return;
    me(t)
      .then(setUser)
      .catch(() => {
        clearToken();
        setUser(null);
      });
  }, []);

  async function onSubmit() {
    setError(null);
    try {
      if (mode === "signup") {
        await register({ email, password, full_name: fullName || undefined });
      }
      const tok = await login(email, password);
      setToken(tok.access_token);
      const u = await me(tok.access_token);
      setUser(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Authentication failed");
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-[900px] px-4 py-10">
        <h1 className="text-[28px] font-semibold text-[#2b2b2b]">
          Sign Up / Sign In
        </h1>

        {user ? (
          <div className="mt-6 rounded-sm border border-black/10 bg-[#f7f7f7] p-5">
            <div className="text-[14px] text-[#333]">
              Signed in as <span className="font-semibold">{user.email}</span>
            </div>
            <button
              type="button"
              className="mt-4 inline-flex h-10 items-center justify-center rounded-sm bg-apts-green px-6 text-[14px] font-semibold text-white"
              onClick={() => {
                clearToken();
                setUser(null);
              }}
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="mt-6 max-w-[420px] rounded-sm border border-black/10 bg-white p-5 shadow-[0_2px_10px_rgba(0,0,0,0.08)]">
            <div className="flex gap-2">
              <button
                type="button"
                className={`h-9 rounded-sm px-4 text-[13px] font-semibold ${
                  mode === "signin"
                    ? "bg-apts-green text-white"
                    : "border border-black/10 bg-white text-[#333]"
                }`}
                onClick={() => setMode("signin")}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`h-9 rounded-sm px-4 text-[13px] font-semibold ${
                  mode === "signup"
                    ? "bg-apts-green text-white"
                    : "border border-black/10 bg-white text-[#333]"
                }`}
                onClick={() => setMode("signup")}
              >
                Sign Up
              </button>
            </div>

            {mode === "signup" ? (
              <label className="mt-4 block">
                <div className="text-[12px] font-semibold text-[#555]">
                  Full name (optional)
                </div>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
                />
              </label>
            ) : null}

            <label className="mt-4 block">
              <div className="text-[12px] font-semibold text-[#555]">Email</div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
              />
            </label>
            <label className="mt-4 block">
              <div className="text-[12px] font-semibold text-[#555]">
                Password
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
              />
            </label>

            <button
              type="button"
              className="mt-5 inline-flex h-10 w-full items-center justify-center rounded-sm bg-apts-green text-[14px] font-semibold text-white"
              onClick={onSubmit}
            >
              {mode === "signup" ? "Create account" : "Sign in"}
            </button>

            {error ? (
              <div className="mt-4 text-[12px] text-red-600">{error}</div>
            ) : null}

            <div className="mt-4 text-[12px] text-[#777]">
              Token stored locally:{" "}
              <span className="font-mono">{token ? "yes" : "no"}</span>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

