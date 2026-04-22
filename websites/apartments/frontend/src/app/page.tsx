import Link from "next/link";

import { Header } from "@/components/Header";
import { HeroSearch } from "@/components/HeroSearch";
import { ListingPreviewCard } from "@/components/ListingPreviewCard";
import { searchListings } from "@/lib/api";

export default async function Home() {
  const city = "Columbus, OH";
  const featured = await searchListings({ q: city, limit: 4 }).catch(() => ({
    total: 0,
    items: [],
  }));

  const heroImage =
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=2200&q=60";

  const marketLinks = [
    "Atlanta, GA",
    "Austin, TX",
    "Baltimore, MD",
    "Boston, MA",
    "Chicago, IL",
    "Cincinnati, OH",
    "Columbus, OH",
    "Dallas, TX",
    "Denver, CO",
    "Detroit, MI",
    "Houston, TX",
    "Los Angeles, CA",
    "Miami, FL",
    "New York, NY",
    "Phoenix, AZ",
    "Portland, OR",
    "San Diego, CA",
    "San Francisco, CA",
    "Seattle, WA",
    "Washington, DC",
  ];

  return (
    <div className="min-h-screen">
      <Header />

      <section
        className="relative overflow-hidden"
        style={{
          backgroundImage: `url(${heroImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="absolute inset-0 bg-black/35" />
        <div className="relative mx-auto flex min-h-[310px] max-w-[1200px] flex-col items-center justify-center px-4 py-10 text-center text-white">
          <h1 className="text-[44px] font-bold leading-[1.05] tracking-tight sm:text-[56px]">
            Discover Your New Home
          </h1>
          <p className="mt-2 text-[18px] text-white/90 sm:text-[20px]">
            Helping 100 million renters find their perfect fit.
          </p>
          <HeroSearch defaultQuery={city} />
        </div>
      </section>

      <section className="mx-auto max-w-[1200px] px-4 py-10">
        <h2 className="text-center text-[28px] font-semibold text-[#2b2b2b]">
          Explore Rentals in {city}
        </h2>
        <div className="mt-7 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featured.items.map((l) => (
            <ListingPreviewCard key={l.id} listing={l} />
          ))}
        </div>
        <div className="mt-8 flex justify-center">
          <Link
            href={`/apartments?q=${encodeURIComponent(city)}`}
            className="inline-flex h-10 items-center justify-center rounded-sm bg-apts-green px-10 text-[14px] font-semibold text-white"
          >
            View More
          </Link>
        </div>
      </section>

      <section className="border-t border-black/10 bg-white">
        <div className="mx-auto max-w-[1200px] px-4 py-14">
          <h3 className="text-center text-[30px] font-semibold text-[#2b2b2b]">
            The Most Rental Listings
          </h3>
          <p className="mt-2 text-center text-[14px] text-[#6b6b6b]">
            Choose from over 1 million apartments, houses, condos, and townhomes
            for rent.
          </p>

          <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[20px] font-semibold text-[#2b2b2b]">
                Renting Made Simple
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Browse the highest quality listings, apply online, sign your
                lease, and even pay your rent from any device.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/learn/renting-made-simple"
              >
                Find Out More
              </Link>
            </div>
            <div
              className="min-h-[220px] rounded-sm bg-cover bg-center"
              style={{
                backgroundImage:
                  "url(https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1400&q=60)",
              }}
            />
            <div
              className="min-h-[220px] rounded-sm bg-cover bg-center"
              style={{
                backgroundImage:
                  "url(https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1400&q=60)",
              }}
            />
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[20px] font-semibold text-[#2b2b2b]">
                Tips for Renters
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Find answers to all of your renting questions with the best
                renter’s guide in the galaxy.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/articles"
              >
                Browse Articles
              </Link>
            </div>
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[20px] font-semibold text-[#2b2b2b]">
                Take Us With You
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Keep <span className="text-[#0b6fbf]">Apartments.com</span> in
                the palm of your hand throughout your rental journey.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/mobile"
              >
                Get the App
              </Link>
            </div>
            <div className="rounded-sm bg-[#f2f2f2] p-8" />
          </div>
        </div>
      </section>

      <section className="bg-white">
        <div className="mx-auto max-w-[1200px] px-4 py-14">
          <h3 className="text-center text-[30px] font-semibold text-[#2b2b2b]">
            The Perfect Place to Manage Your Property
          </h3>
          <p className="mt-2 text-center text-[14px] text-[#6b6b6b]">
            Work with the best suite of property management tools on the market.
          </p>
          <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[18px] font-semibold text-[#2b2b2b]">
                Advertise Your Rental
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Connect with renters looking for their next home using our
                comprehensive marketing platform.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/add-a-property"
              >
                List Your Property
              </Link>
            </div>
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[18px] font-semibold text-[#2b2b2b]">
                Lease 100% Online
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Accept applications, process rent payments online, and sign
                digital leases all powered on a single platform.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/manage"
              >
                Manage Your Property
              </Link>
            </div>
            <div className="rounded-sm bg-[#f2f2f2] p-8">
              <h4 className="text-[18px] font-semibold text-[#2b2b2b]">
                Property Manager Resources
              </h4>
              <p className="mt-3 text-[13px] leading-6 text-[#6b6b6b]">
                Stay up-to-date using our tips and guides on rent payments,
                leasing, and management solutions.
              </p>
              <Link
                className="mt-5 inline-block text-[13px] font-semibold text-[#0b6fbf]"
                href="/resources"
              >
                Stay Informed
              </Link>
            </div>
            <div className="rounded-sm bg-[#f2f2f2] p-8" />
          </div>
        </div>
      </section>

      <section className="border-t border-black/10 bg-white">
        <div className="mx-auto max-w-[1200px] px-4 py-10 text-center text-[13px] text-[#555]">
          Search over 1 million listings including{" "}
          <Link className="text-[#0b6fbf]" href="/apartments?q=Boston%2C%20MA">
            apartments
          </Link>
          ,{" "}
          <Link className="text-[#0b6fbf]" href="/apartments?q=Columbus%2C%20OH">
            houses
          </Link>
          ,{" "}
          <Link className="text-[#0b6fbf]" href="/apartments?q=Chicago%2C%20IL">
            condos
          </Link>{" "}
          and{" "}
          <Link className="text-[#0b6fbf]" href="/apartments?q=Seattle%2C%20WA">
            townhomes
          </Link>{" "}
          available for rent. You’ll find your next home, in any style you
          prefer.
        </div>
        <div className="mx-auto max-w-[1200px] px-4 pb-12">
          <div className="grid grid-cols-1 gap-10 border-t border-black/10 pt-10 sm:grid-cols-3">
            <div>
              <div className="text-[11px] font-semibold tracking-wide text-[#777]">
                TOP MARKETS
              </div>
              <ul className="mt-4 space-y-2 text-[12px]">
                {marketLinks.slice(0, 10).map((m) => (
                  <li key={m}>
                    <Link
                      className="text-[#0b6fbf] hover:underline"
                      href={`/apartments?q=${encodeURIComponent(m)}`}
                    >
                      {m}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-[11px] font-semibold tracking-wide text-[#777]">
                POPULAR SEARCHES
              </div>
              <ul className="mt-4 space-y-2 text-[12px]">
                {marketLinks.slice(10).map((m) => (
                  <li key={m}>
                    <Link
                      className="text-[#0b6fbf] hover:underline"
                      href={`/apartments?q=${encodeURIComponent(m)}`}
                    >
                      {m} Apartments
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-[11px] font-semibold tracking-wide text-[#777]">
                RENTAL MANAGER SERVICES
              </div>
              <ul className="mt-4 space-y-2 text-[12px]">
                <li>
                  <Link className="text-[#0b6fbf] hover:underline" href="/manage">
                    Rental Manager
                  </Link>
                </li>
                <li>
                  <Link
                    className="text-[#0b6fbf] hover:underline"
                    href="/add-a-property"
                  >
                    List Your Property for Rent
                  </Link>
                </li>
                <li>
                  <Link
                    className="text-[#0b6fbf] hover:underline"
                    href="/resources"
                  >
                    Rental Manager Resources
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-black/10 pt-8 text-[12px] text-[#777] sm:flex-row">
            <div className="flex items-center gap-2">
              <span className="text-apts-green font-semibold">Apartments.com</span>
              <span>© 2026 Clone</span>
            </div>
            <div className="flex items-center gap-4">
              <Link className="hover:underline" href="/about">
                About Us
              </Link>
              <Link className="hover:underline" href="/contact">
                Contact Us
              </Link>
              <Link className="hover:underline" href="/privacy">
                Privacy Notice
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
