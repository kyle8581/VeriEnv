import Link from "next/link";
import { cookies } from "next/headers";

import { LogoutButton } from "@/components/LogoutButton";

const menuItemClass =
  "px-2 py-1 text-sm text-white/90 hover:text-white focus:outline-none";

export async function Header() {
  const token = (await cookies()).get("discogs_token")?.value;
  const signedIn = Boolean(token);
  return (
    <header className="w-full bg-[#111] text-white">
      <div className="mx-auto flex max-w-[1040px] items-center gap-3 px-3 py-2">
        <Link
          href="/"
          className="mr-2 flex items-center gap-2 text-lg font-bold tracking-tight"
        >
          <span className="font-semibold">Discogs</span>
        </Link>

        <form action="/search" className="flex flex-1 items-center">
          <div className="flex w-full items-center overflow-hidden rounded-sm bg-white">
            <input
              name="q"
              placeholder="Search artists, albums and more..."
              className="w-full px-3 py-2 text-sm text-black placeholder:text-neutral-500 focus:outline-none"
            />
            <button
              type="submit"
              className="px-3 py-2 text-sm font-semibold text-neutral-700 hover:bg-neutral-100"
            >
              Search
            </button>
          </div>
        </form>

        <nav className="ml-2 hidden items-center gap-2 md:flex">
          <div className="group relative">
            <button className={menuItemClass}>Explore ▾</button>
            <div className="absolute left-0 top-full z-50 hidden w-[420px] border border-neutral-800 bg-[#111] p-3 group-hover:block">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase text-white/70">
                    Discover
                  </div>
                  <ul className="space-y-1">
                    <li>
                      <Link className="hover:underline" href="/genre/rock">
                        Genres
                      </Link>
                    </li>
                    <li>
                      <Link className="hover:underline" href="/search?q=new">
                        New Releases
                      </Link>
                    </li>
                    <li>
                      <Link className="hover:underline" href="/search?q=trending">
                        Trending
                      </Link>
                    </li>
                  </ul>
                </div>
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase text-white/70">
                    Guides
                  </div>
                  <ul className="space-y-1">
                    <li>
                      <Link className="hover:underline" href="/">
                        Editorial Picks
                      </Link>
                    </li>
                    <li>
                      <Link className="hover:underline" href="/">
                        Essentials Lists
                      </Link>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="group relative">
            <button className={menuItemClass}>Marketplace ▾</button>
            <div className="absolute left-0 top-full z-50 hidden w-[320px] border border-neutral-800 bg-[#111] p-3 group-hover:block">
              <ul className="space-y-1 text-sm">
                <li>
                  <Link className="hover:underline" href="/sell">
                    Sell Music
                  </Link>
                </li>
                <li>
                  <Link className="hover:underline" href="/cart">
                    Cart
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="group relative">
            <button className={menuItemClass}>Community ▾</button>
            <div className="absolute left-0 top-full z-50 hidden w-[280px] border border-neutral-800 bg-[#111] p-3 group-hover:block">
              <ul className="space-y-1 text-sm">
                <li>
                  <Link className="hover:underline" href="/forum">
                    Forum
                  </Link>
                </li>
                <li>
                  <Link className="hover:underline" href="/blog">
                    Blog
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/cart"
            className="rounded-sm p-2 hover:bg-white/10"
            aria-label="Cart"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M6 6h15l-2 9H7L6 6Z"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M6 6 5 3H2"
                stroke="currentColor"
                strokeWidth="2"
              />
              <circle cx="9" cy="20" r="1.5" fill="currentColor" />
              <circle cx="18" cy="20" r="1.5" fill="currentColor" />
            </svg>
          </Link>
          {signedIn ? (
            <div className="group relative">
              <button
                className="rounded-sm p-2 hover:bg-white/10"
                aria-label="Account"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <path
                    d="M4 21a8 8 0 0 1 16 0"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                </svg>
              </button>
              <div className="absolute right-0 top-full z-50 hidden w-[200px] border border-neutral-800 bg-[#111] p-2 group-hover:block">
                <Link className="block rounded-sm px-2 py-1 text-sm text-white/90 hover:bg-white/10" href="/me/collection">
                  Collection
                </Link>
                <Link className="block rounded-sm px-2 py-1 text-sm text-white/90 hover:bg-white/10" href="/me/wantlist">
                  Wantlist
                </Link>
                <div className="my-1 border-t border-white/10" />
                <LogoutButton />
              </div>
            </div>
          ) : (
            <Link
              href="/login"
              className="rounded-sm p-2 hover:bg-white/10"
              aria-label="Account"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <path
                  d="M4 21a8 8 0 0 1 16 0"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              </svg>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

