import Link from "next/link";

import { Logo } from "@/components/Logo";

function IconMenu() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M4 6h16v2H4V6Zm0 5h16v2H4v-2Zm0 5h16v2H4v-2Z"
      />
    </svg>
  );
}

function IconGlobe() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm7.9 9h-3.2a15 15 0 0 0-1.1-5 8.03 8.03 0 0 1 4.3 5Zm-5.3 0H9.4A13.3 13.3 0 0 1 12 4.1 13.3 13.3 0 0 1 14.6 11ZM4.1 11a8.03 8.03 0 0 1 4.3-5 15 15 0 0 0-1.1 5H4.1Zm0 2h3.2a15 15 0 0 0 1.1 5 8.03 8.03 0 0 1-4.3-5Zm5.3 0h5.2A13.3 13.3 0 0 1 12 19.9 13.3 13.3 0 0 1 9.4 13Zm6.2 8a15 15 0 0 0 1.1-5h3.2a8.03 8.03 0 0 1-4.3 5Z"
      />
    </svg>
  );
}

export function Header({ variant }: { variant?: "light" | "dark" }) {
  const isDark = variant === "dark";
  const text = isDark ? "text-white" : "text-[#2b2b2b]";
  const subtle = isDark ? "text-white/90" : "text-[#6b6b6b]";
  const border = isDark ? "border-white/20" : "border-black/10";
  const bg = isDark ? "bg-transparent" : "bg-white";

  return (
    <header className={`${bg} ${text} border-b ${border}`}>
      <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between px-4">
        <div className={`flex items-center gap-5 text-sm ${subtle}`}>
          <Link
            href="/menu"
            className={`inline-flex items-center gap-2 ${subtle} hover:${text}`}
            aria-label="Menu"
          >
            <IconMenu />
            <span className="hidden sm:inline">Menu</span>
          </Link>
          <Link
            href="/language"
            className={`inline-flex items-center gap-2 ${subtle} hover:${text}`}
            aria-label="Language"
          >
            <IconGlobe />
            <span className="hidden sm:inline">English</span>
          </Link>
        </div>

        <div className="flex items-center">
          <Logo />
        </div>

        <nav className="flex items-center gap-5 text-sm">
          <Link className="hover:underline" href="/manage">
            Manage Rentals
          </Link>
          <Link className="hover:underline" href="/auth">
            Sign Up / Sign In
          </Link>
          <Link className="hover:underline" href="/add-a-property">
            Add a Property
          </Link>
        </nav>
      </div>
    </header>
  );
}

