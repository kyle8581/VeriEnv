"use client";

import { useState } from "react";

import { Header } from "@/components/Header";

export default function ContactPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-[900px] px-4 py-10">
        <h1 className="text-[28px] font-semibold text-[#2b2b2b]">Contact Us</h1>
        <p className="mt-3 text-[14px] leading-7 text-[#555]">
          Send feedback about this clone. The message is saved locally so you
          can verify the flow immediately.
        </p>

        <form
          className="mt-8 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            window.localStorage.setItem(
              "apartments_contact",
              JSON.stringify({ email, message, createdAt: new Date().toISOString() }),
            );
            setSent(true);
          }}
        >
          <label className="block">
            <div className="text-[12px] font-semibold text-[#555]">Email</div>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
            />
          </label>
          <label className="block">
            <div className="text-[12px] font-semibold text-[#555]">Message</div>
            <textarea
              required
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="mt-1 min-h-[120px] w-full rounded-sm border border-black/15 px-3 py-2 text-[14px] outline-none focus:ring-2 ring-apts-green"
            />
          </label>
          <button
            type="submit"
            className="inline-flex h-10 items-center justify-center rounded-sm bg-apts-green px-6 text-[14px] font-semibold text-white"
          >
            Send
          </button>
        </form>

        {sent ? (
          <div className="mt-8 rounded-sm border border-black/10 bg-[#f7f7f7] p-5 text-[13px] text-[#333]">
            Message saved. Thanks!
          </div>
        ) : null}
      </main>
    </div>
  );
}

