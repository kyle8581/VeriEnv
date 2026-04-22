"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

type NavItem = {
  label: string;
  href?: string;
  children?: { label: string; href: string }[];
};

function NavDropdown({ item, openMenu, setOpenMenu }: { item: NavItem; openMenu: string | null; setOpenMenu: (v: string | null) => void }) {
  const isOpen = openMenu === item.label;

  if (item.href) {
    return (
      <Link
        href={item.href}
        className="text-sm font-medium text-zinc-700 hover:text-zinc-900"
        onClick={() => setOpenMenu(null)}
      >
        {item.label}
      </Link>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        className="flex items-center gap-1 text-sm font-medium text-zinc-700 hover:text-zinc-900"
        onClick={() => setOpenMenu(isOpen ? null : item.label)}
      >
        {item.label}
        <span className={`text-xs text-zinc-500 transition-transform ${isOpen ? "rotate-180" : ""}`}>▾</span>
      </button>

      {item.children && isOpen && (
        <div className="absolute left-0 top-full pt-2 w-56 z-50">
          <div className="rounded-md border border-zinc-200 bg-white shadow-lg p-2">
            {item.children.map((c) => (
              <Link
                key={c.href}
                href={c.href}
                className="block rounded px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 hover:text-zinc-900"
                onClick={() => setOpenMenu(null)}
              >
                {c.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const navRef = useRef<HTMLElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const items: NavItem[] = useMemo(
    () => [
      {
        label: "Why Coursera",
        children: [
          { label: "Overview", href: "/why-coursera" },
          { label: "Outcomes", href: "/why-coursera/outcomes" },
          { label: "Learner Experience", href: "/why-coursera/learner-experience" },
        ],
      },
      {
        label: "Solutions",
        children: [
          { label: "For Higher Education", href: "/solutions/higher-ed" },
          { label: "For Government", href: "/solutions/government" },
          { label: "For Community Colleges", href: "/solutions/community-colleges" },
        ],
      },
      {
        label: "Resources",
        children: [
          { label: "All Resources", href: "/resources" },
          { label: "Ebooks", href: "/resources?kind=ebook" },
          { label: "Events", href: "/resources?kind=event" },
        ],
      },
      { label: "Compare Plans", href: "/compare-plans" },
    ],
    [],
  );

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-zinc-200">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-baseline gap-1">
            <span className="text-xl font-semibold tracking-tight text-[#0056D2]">
              coursera
            </span>
            <span className="text-sm font-medium text-zinc-500">for campus</span>
          </Link>
        </div>

        <nav ref={navRef} className="hidden items-center gap-8 md:flex">
          {items.map((item) => (
            <NavDropdown key={item.label} item={item} openMenu={openMenu} setOpenMenu={setOpenMenu} />
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/contact"
            className="hidden md:inline-flex h-9 items-center justify-center rounded bg-[#0056D2] px-4 text-sm font-semibold text-white hover:bg-[#004bb8]"
          >
            Contact Us
          </Link>
          <button
            type="button"
            aria-label="Toggle menu"
            className="md:hidden inline-flex h-9 w-9 items-center justify-center rounded border border-zinc-200 text-zinc-700 hover:bg-zinc-50"
            onClick={() => setMobileOpen((v) => !v)}
          >
            ☰
          </button>
        </div>
      </div>

      {mobileOpen ? (
        <div className="md:hidden border-t border-zinc-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-3 space-y-2">
            {items.map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="text-sm font-semibold text-zinc-900">{item.label}</div>
                {item.href ? (
                  <Link
                    href={item.href}
                    className="block rounded px-2 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                    onClick={() => setMobileOpen(false)}
                  >
                    {item.label}
                  </Link>
                ) : null}
                {item.children?.map((c) => (
                  <Link
                    key={c.href}
                    href={c.href}
                    className="block rounded px-2 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                    onClick={() => setMobileOpen(false)}
                  >
                    {c.label}
                  </Link>
                ))}
              </div>
            ))}

            <Link
              href="/contact"
              className="mt-2 inline-flex h-10 w-full items-center justify-center rounded bg-[#0056D2] px-4 text-sm font-semibold text-white"
              onClick={() => setMobileOpen(false)}
            >
              Contact Us
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}

