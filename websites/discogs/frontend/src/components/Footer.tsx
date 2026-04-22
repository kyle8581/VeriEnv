import Link from "next/link";

function Col({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-white/70">
        {title}
      </div>
      <div className="space-y-1 text-sm text-white/80">{children}</div>
    </div>
  );
}

export function Footer() {
  return (
    <footer className="mt-10 bg-[#111] text-white">
      <div className="mx-auto max-w-[1040px] px-3 py-10">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
          <Col title="Discogs">
            <Link className="block hover:underline" href="/about">
              About Us
            </Link>
            <Link className="block hover:underline" href="/careers">
              Careers
            </Link>
            <Link className="block hover:underline" href="/api">
              API
            </Link>
          </Col>
          <Col title="Help Is Here">
            <Link className="block hover:underline" href="/help">
              Help &amp; Support
            </Link>
            <Link className="block hover:underline" href="/shipping">
              Discogs Shipping
            </Link>
            <Link className="block hover:underline" href="/guides">
              Keyboard Shortcuts
            </Link>
          </Col>
          <Col title="Join In">
            <Link className="block hover:underline" href="/get-started">
              Get Started
            </Link>
            <Link className="block hover:underline" href="/sell">
              Start Selling
            </Link>
            <Link className="block hover:underline" href="/add-release">
              Add Release
            </Link>
          </Col>
          <Col title="Follow Us">
            <Link className="block hover:underline" href="#">
              Facebook
            </Link>
            <Link className="block hover:underline" href="#">
              X / Twitter
            </Link>
            <Link className="block hover:underline" href="#">
              Instagram
            </Link>
            <Link className="block hover:underline" href="#">
              YouTube
            </Link>
          </Col>
          <Col title="On The Go">
            <div className="flex flex-col gap-2">
              <div className="rounded bg-white/10 px-3 py-2 text-xs">
                App Store (placeholder)
              </div>
              <div className="rounded bg-white/10 px-3 py-2 text-xs">
                Google Play (placeholder)
              </div>
            </div>
          </Col>
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-white/10 pt-4 text-xs text-white/60 sm:flex-row sm:items-center sm:justify-between">
          <div>Discogs © {new Date().getFullYear()}</div>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            <Link className="hover:underline" href="/terms">
              Terms of Service
            </Link>
            <Link className="hover:underline" href="/privacy">
              Privacy Policy
            </Link>
            <Link className="hover:underline" href="/cookies">
              Cookies
            </Link>
            <span>English ▾</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

