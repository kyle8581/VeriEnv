import Link from "next/link";

import { SimplePage } from "@/components/SimplePage";

export default function ManagePage() {
  return (
    <SimplePage title="Manage Rentals">
      <p>
        This clone includes renter-focused tools like saving searches and
        favoriting listings.
      </p>
      <ul className="mt-4 list-disc space-y-2 pl-5">
        <li>
          <Link className="text-[#0b6fbf] hover:underline" href="/auth">
            Sign in
          </Link>{" "}
          to save favorites and searches.
        </li>
        <li>
          Start browsing listings on{" "}
          <Link
            className="text-[#0b6fbf] hover:underline"
            href="/apartments?q=Boston%2C%20MA"
          >
            the map + list search page
          </Link>
          .
        </li>
      </ul>
    </SimplePage>
  );
}

