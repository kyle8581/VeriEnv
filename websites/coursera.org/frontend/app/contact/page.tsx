"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";

type Status = "idle" | "submitting" | "success" | "error";

export default function ContactPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(formData: FormData) {
    setStatus("submitting");
    setError(null);
    const payload = {
      full_name: String(formData.get("full_name") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim(),
      institution: String(formData.get("institution") ?? "").trim(),
      message: String(formData.get("message") ?? "").trim(),
    };
    if (!payload.full_name || !payload.email) {
      setStatus("error");
      setError("Please provide your name and email.");
      return;
    }
    try {
      await apiPost<{ message: string }>("/api/leads/contact", payload);
      setStatus("success");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Submission failed");
    }
  }

  return (
    <div className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Contact Us</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          Tell us about your institution and goals. We’ll follow up shortly.
        </p>

        <form
          action={async (fd) => onSubmit(fd)}
          className="mt-8 max-w-xl rounded border border-zinc-200 bg-white p-6"
        >
          <div className="space-y-4">
            <div>
              <div className="text-xs font-semibold text-zinc-800">Full name</div>
              <input
                name="full_name"
                required
                className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
              />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-800">Work email</div>
              <input
                name="email"
                type="email"
                required
                className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
              />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-800">Institution</div>
              <input
                name="institution"
                className="mt-1 h-10 w-full rounded border border-zinc-300 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
              />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-800">Message</div>
              <textarea
                name="message"
                rows={5}
                className="mt-1 w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0056D2]/30"
              />
            </div>

            <button
              type="submit"
              disabled={status === "submitting" || status === "success"}
              className="inline-flex h-11 w-full items-center justify-center rounded bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8] disabled:opacity-60"
            >
              {status === "submitting" ? "Submitting..." : "Submit"}
            </button>

            {status === "success" ? (
              <div className="rounded bg-green-50 p-3 text-sm text-green-900">
                Submitted. We’ll be in touch soon.
              </div>
            ) : null}
            {status === "error" && error ? (
              <div className="rounded bg-red-50 p-3 text-sm text-red-900">{error}</div>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}

