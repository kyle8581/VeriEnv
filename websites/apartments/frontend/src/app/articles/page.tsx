import Link from "next/link";

import { SimplePage } from "@/components/SimplePage";

export default function ArticlesPage() {
  return (
    <SimplePage title="Tips for Renters">
      <p>Popular guides:</p>
      <ul className="mt-4 list-disc space-y-2 pl-5">
        <li>
          <Link className="text-[#0b6fbf] hover:underline" href="/learn/renting-made-simple">
            Renting Made Simple
          </Link>
        </li>
        <li>
          <Link
            className="text-[#0b6fbf] hover:underline"
            href="/apartments?q=Boston%2C%20MA"
          >
            How to evaluate a neighborhood (try the map)
          </Link>
        </li>
      </ul>
    </SimplePage>
  );
}

