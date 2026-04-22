"use client";

import { useEffect, useState } from "react";

import { Header } from "@/components/Header";

const KEY = "apartments_language";

export default function LanguagePage() {
  const [lang, setLang] = useState("English");

  useEffect(() => {
    const saved = window.localStorage.getItem(KEY);
    if (saved) setLang(saved);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main className="mx-auto max-w-[900px] px-4 py-10">
        <h1 className="text-[28px] font-semibold text-[#2b2b2b]">Language</h1>
        <p className="mt-3 text-[14px] leading-7 text-[#555]">
          Choose a display language for this clone (saved locally in your
          browser).
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          {["English", "Español", "Français"].map((l) => (
            <button
              key={l}
              type="button"
              className={`h-10 rounded-sm border px-4 text-[14px] ${
                lang === l
                  ? "border-apts-green bg-[#e9f2ea] text-[#1b1b1b]"
                  : "border-black/15 bg-white text-[#333]"
              }`}
              onClick={() => {
                setLang(l);
                window.localStorage.setItem(KEY, l);
              }}
            >
              {l}
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}

