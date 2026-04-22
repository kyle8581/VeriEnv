"use client";

import { useState } from "react";

import { Header } from "@/components/Header";

type Submission = {
  name: string;
  email: string;
  city: string;
  state: string;
  message: string;
  createdAt: string;
};

export default function AddAPropertyPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState<Submission | null>(null);

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-[900px] px-4 py-10">
        <h1 className="text-[28px] font-semibold text-[#2b2b2b]">
          Add a Property
        </h1>
        <p className="mt-3 text-[14px] leading-7 text-[#555]">
          Submit a request to add your property to this clone’s demo catalog.
          The request is saved locally in your browser so you can verify the
          flow end-to-end.
        </p>

        <form
          className="mt-8 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            const s: Submission = {
              name: name.trim(),
              email: email.trim(),
              city: city.trim(),
              state: state.trim().toUpperCase(),
              message: message.trim(),
              createdAt: new Date().toISOString(),
            };
            window.localStorage.setItem(
              "apartments_property_submission",
              JSON.stringify(s),
            );
            setSubmitted(s);
          }}
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block">
              <div className="text-[12px] font-semibold text-[#555]">Name</div>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
              />
            </label>
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
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block">
              <div className="text-[12px] font-semibold text-[#555]">City</div>
              <input
                required
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] outline-none focus:ring-2 ring-apts-green"
              />
            </label>
            <label className="block">
              <div className="text-[12px] font-semibold text-[#555]">State</div>
              <input
                required
                value={state}
                onChange={(e) => setState(e.target.value)}
                maxLength={2}
                className="mt-1 h-10 w-full rounded-sm border border-black/15 px-3 text-[14px] uppercase outline-none focus:ring-2 ring-apts-green"
              />
            </label>
          </div>

          <label className="block">
            <div className="text-[12px] font-semibold text-[#555]">
              Property details
            </div>
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
            Submit Request
          </button>
        </form>

        {submitted ? (
          <div className="mt-8 rounded-sm border border-black/10 bg-[#f7f7f7] p-5 text-[13px] text-[#333]">
            <div className="font-semibold">Request saved</div>
            <div className="mt-2">
              {submitted.city}, {submitted.state} — {submitted.email}
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}

