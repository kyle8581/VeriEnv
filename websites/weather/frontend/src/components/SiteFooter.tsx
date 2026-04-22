import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-10 bg-white/95">
      <div className="mx-auto w-full max-w-[1120px] px-4 py-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-sm font-semibold text-[#0b1f2a]">
              Connect With Us
            </div>
            <div className="mt-2 flex items-center gap-2">
              {[
                { name: "Facebook", href: "https://www.facebook.com" },
                { name: "X", href: "https://x.com" },
                { name: "Instagram", href: "https://www.instagram.com" },
                { name: "YouTube", href: "https://www.youtube.com" },
              ].map((n) => (
                <a
                  key={n.name}
                  href={n.href}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full border border-black/10 bg-white px-3 py-1 text-xs font-semibold text-black/60 hover:bg-black/[0.03]"
                >
                  {n.name}
                </a>
              ))}
            </div>
          </div>

          <div className="text-xs text-black/60">
            © {new Date().getFullYear()} Weather Portal. All rights reserved.
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 text-xs text-black/60 md:grid-cols-4">
          {[
            { label: "Terms of Use", href: "/terms" },
            { label: "Privacy Policy", href: "/privacy" },
            { label: "Cookie Policy", href: "/cookies" },
            { label: "Ad Choices", href: "/ad-choices" },
            { label: "Contact", href: "/contact" },
            { label: "Careers", href: "/careers" },
            { label: "Media Kit", href: "/media-kit" },
            { label: "Help", href: "/help" },
          ].map((t) => (
            <Link key={t.href} href={t.href} className="hover:text-black/80">
              {t.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}

