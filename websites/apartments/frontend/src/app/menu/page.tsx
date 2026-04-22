import Link from "next/link";

import { SimplePage } from "@/components/SimplePage";

export default function MenuPage() {
  return (
    <SimplePage title="Menu">
      <p>Quick links for this clone:</p>
      <ul className="mt-4 list-disc space-y-2 pl-5">
        <li>
          <Link className="text-[#0b6fbf] hover:underline" href="/">
            Home
          </Link>
        </li>
        <li>
          <Link
            className="text-[#0b6fbf] hover:underline"
            href="/apartments?q=Boston%2C%20MA"
          >
            Search (Boston, MA)
          </Link>
        </li>
        <li>
          <Link
            className="text-[#0b6fbf] hover:underline"
            href="/apartments?q=Columbus%2C%20OH"
          >
            Search (Columbus, OH)
          </Link>
        </li>
        <li>
          <Link className="text-[#0b6fbf] hover:underline" href="/auth">
            Sign In / Sign Up
          </Link>
        </li>
      </ul>
    </SimplePage>
  );
}

