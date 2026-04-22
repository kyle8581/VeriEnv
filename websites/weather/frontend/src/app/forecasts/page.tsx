import Link from "next/link";

export default function ForecastsPage() {
  return (
    <div className="twc-card p-5">
      <h1 className="text-lg font-semibold text-[#0b1f2a]">More Forecasts</h1>
      <div className="mt-2 text-sm text-black/60">
        Explore additional forecast views.
      </div>
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {[
          { label: "Today highlights", href: "/today" },
          { label: "Hourly forecasts", href: "/hourly" },
          { label: "10 day outlook", href: "/tenday" },
          { label: "Radar", href: "/radar" },
          { label: "Video", href: "/video" },
          { label: "News", href: "/news" },
          { label: "Photos", href: "/photos" },
          { label: "Subscribe", href: "/subscribe" },
        ].map((x) => (
          <Link
            key={x.href}
            href={x.href}
            className="rounded-lg border border-black/10 bg-white p-4 text-sm font-semibold text-[#0b1f2a] hover:bg-black/[0.02]"
          >
            {x.label}
          </Link>
        ))}
      </div>
    </div>
  );
}

