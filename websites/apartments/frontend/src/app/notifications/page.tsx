import Link from "next/link";

import { SimplePage } from "@/components/SimplePage";

export default function NotificationsPage() {
  return (
    <SimplePage title="Notifications">
      Sign in to enable notifications and saved searches. In this clone, the
      bell icon serves as a shortcut to your account tools.
      <div className="mt-4">
        <Link className="text-[#0b6fbf] hover:underline" href="/auth">
          Go to Sign In
        </Link>
      </div>
    </SimplePage>
  );
}

