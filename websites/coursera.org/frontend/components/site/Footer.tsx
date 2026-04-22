import Link from "next/link";
import Image from "next/image";

export function Footer() {
  return (
    <footer className="border-t border-zinc-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <div className="grid gap-10 md:grid-cols-4">
          <div>
            <div className="text-sm font-semibold text-zinc-900">Coursera</div>
            <div className="mt-4 space-y-3 text-sm text-zinc-600">
              <Link href="/" className="block hover:text-zinc-900">
                Home
              </Link>
              <Link href="/courses" className="block hover:text-zinc-900">
                Course Catalog
              </Link>
              <Link href="/resources" className="block hover:text-zinc-900">
                Resources
              </Link>
              <Link href="/contact" className="block hover:text-zinc-900">
                Contact Us
              </Link>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-zinc-900">Community</div>
            <div className="mt-4 space-y-3 text-sm text-zinc-600">
              <Link href="/community" className="block hover:text-zinc-900">
                Community
              </Link>
              <Link href="/help" className="block hover:text-zinc-900">
                Help Center
              </Link>
              <Link href="/terms" className="block hover:text-zinc-900">
                Terms
              </Link>
              <Link href="/privacy" className="block hover:text-zinc-900">
                Privacy
              </Link>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-zinc-900">More</div>
            <div className="mt-4 space-y-3 text-sm text-zinc-600">
              <Link href="/why-coursera" className="block hover:text-zinc-900">
                Why Coursera
              </Link>
              <Link href="/compare-plans" className="block hover:text-zinc-900">
                Compare Plans
              </Link>
              <Link href="/solutions/higher-ed" className="block hover:text-zinc-900">
                Solutions
              </Link>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-zinc-900">Mobile App</div>
            <div className="mt-4 space-y-3">
              <div className="relative h-10 w-32 overflow-hidden rounded border border-zinc-200 bg-zinc-100">
                <Image
                  src="https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?auto=format&fit=crop&w=256&q=80"
                  alt="App Store"
                  fill
                  className="object-cover"
                />
              </div>
              <div className="relative h-10 w-32 overflow-hidden rounded border border-zinc-200 bg-zinc-100">
                <Image
                  src="https://images.unsplash.com/photo-1614680376739-414d95ff43df?auto=format&fit=crop&w=256&q=80"
                  alt="Google Play"
                  fill
                  className="object-cover"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-6 border-t border-zinc-200 pt-8 md:flex-row md:items-center md:justify-between">
          <div className="text-xs text-zinc-500">© 2023 Coursera Inc. All rights reserved.</div>
          <div className="flex items-center gap-3">
            {["", "", "", ""].map((_, idx) => (
              <div
                key={idx}
                className="h-7 w-7 rounded border border-zinc-300 bg-zinc-100"
                aria-hidden="true"
              />
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

