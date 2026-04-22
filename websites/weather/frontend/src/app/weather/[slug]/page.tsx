import Link from "next/link";

import { serverGet } from "@/lib/serverApi";

type Location = {
  name: string;
  state: string | null;
  country: string;
  zip_code: string | null;
  latitude: number;
  longitude: number;
  timezone: string;
  slug: string;
};

type Current = {
  observed_at: string | null;
  temperature_c: number | null;
  apparent_temperature_c: number | null;
  humidity_percent: number | null;
  wind_speed_kmh: number | null;
  wind_direction_deg: number | null;
  weather: { code: number | null; label: string; icon: string };
};

type HourlyPoint = {
  time: string;
  temperature_c: number | null;
  precipitation_probability: number | null;
  wind_speed_kmh: number | null;
  weather: { code: number | null; label: string; icon: string };
};

type DailyPoint = {
  date: string;
  temp_max_c: number | null;
  temp_min_c: number | null;
  sunrise: string | null;
  sunset: string | null;
  uv_index_max: number | null;
  weather: { code: number | null; label: string; icon: string };
};

function cToF(c: number) {
  return (c * 9) / 5 + 32;
}

function fmtTempF(c: number | null) {
  if (c === null || Number.isNaN(c)) return "—";
  return `${Math.round(cToF(c))}°`;
}

function fmtTempC(c: number | null) {
  if (c === null || Number.isNaN(c)) return "—";
  return `${Math.round(c)}°C`;
}

function fmtTimeLabel(iso: string) {
  // iso like 2026-01-03T00:00
  const t = iso.split("T")[1];
  if (!t) return iso;
  const [hh, mm] = t.split(":");
  const h = Number(hh);
  const ampm = h >= 12 ? "PM" : "AM";
  const h12 = ((h + 11) % 12) + 1;
  return `${h12}${mm === "00" ? "" : `:${mm}`} ${ampm}`;
}

export default async function WeatherPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [loc, current, hourly, daily] = await Promise.all([
    serverGet<Location>(`/locations/${slug}`),
    serverGet<Current>(`/weather/${slug}/current`),
    serverGet<HourlyPoint[]>(`/weather/${slug}/hourly`),
    serverGet<DailyPoint[]>(`/weather/${slug}/daily`),
  ]);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_330px]">
      <div className="twc-card p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-lg font-semibold text-[#0b1f2a]">
              {loc.name}
              {loc.state ? `, ${loc.state}` : ""} Weather
            </div>
            <div className="mt-1 text-xs text-black/50">
              Updated: {current.observed_at ?? "—"} • {loc.timezone}
            </div>
          </div>
          <Link
            href="/account/saved-locations"
            className="rounded-full border border-black/10 bg-white px-3 py-1.5 text-xs font-semibold text-black/70 hover:bg-black/[0.03]"
          >
            My Locations
          </Link>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-[1fr_1fr]">
          <div className="rounded-lg border border-black/10 bg-white p-4">
            <div className="text-5xl font-semibold tracking-tight text-[#0b1f2a]">
              {fmtTempF(current.temperature_c)}
            </div>
            <div className="mt-1 text-sm font-semibold text-black/70">
              {current.weather?.label ?? "—"}
            </div>
            <div className="mt-2 text-xs text-black/55">
              Feels like {fmtTempF(current.apparent_temperature_c)} (
              {fmtTempC(current.apparent_temperature_c)})
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-black/60">
              <div>Humidity: {current.humidity_percent ?? "—"}%</div>
              <div>Wind: {current.wind_speed_kmh ?? "—"} km/h</div>
            </div>
          </div>

          <div className="rounded-lg border border-black/10 bg-white p-4">
            <div className="text-sm font-semibold text-[#0b1f2a]">
              Hourly forecast
            </div>
            <div className="mt-3 overflow-x-auto">
              <div className="flex gap-3">
                {hourly.slice(0, 12).map((h) => (
                  <div
                    key={h.time}
                    className="min-w-[92px] rounded-lg border border-black/10 bg-white p-3 text-center"
                  >
                    <div className="text-[11px] font-semibold text-black/55">
                      {fmtTimeLabel(h.time)}
                    </div>
                    <div className="mt-2 text-lg font-semibold text-[#0b1f2a]">
                      {fmtTempF(h.temperature_c)}
                    </div>
                    <div className="mt-1 text-[11px] text-black/50">
                      {h.precipitation_probability ?? "—"}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-3 text-xs text-black/55">
              Tip: Use <Link className="font-semibold text-[#0b5672]" href="/hourly">Hourly</Link> for location search.
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-black/10 bg-white p-4">
          <div className="mb-2 text-sm font-semibold text-[#0b1f2a]">
            10 Day Outlook
          </div>
          <div className="divide-y divide-black/10">
            {daily.map((d) => (
              <div
                key={d.date}
                className="flex items-center justify-between gap-3 py-3 text-sm"
              >
                <div className="w-[110px] text-xs font-semibold text-black/60">
                  {d.date}
                </div>
                <div className="flex-1 text-sm font-semibold text-[#0b1f2a]">
                  {d.weather.label}
                </div>
                <div className="w-[120px] text-right text-sm font-semibold text-[#0b1f2a]">
                  {fmtTempF(d.temp_max_c)} /{" "}
                  <span className="text-black/55">{fmtTempF(d.temp_min_c)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <aside className="space-y-4">
        <div className="twc-card p-4">
          <div className="text-sm font-semibold">Today&apos;s Weather</div>
          <div className="mt-2 text-xs text-black/60">
            Sunrise: {daily[0]?.sunrise ?? "—"}
            <br />
            Sunset: {daily[0]?.sunset ?? "—"}
            <br />
            UV index max: {daily[0]?.uv_index_max ?? "—"}
          </div>
        </div>

        <div className="twc-card p-4">
          <div className="text-sm font-semibold">Radar</div>
          <div className="mt-2 text-xs text-black/60">
            View radar for this location.
          </div>
          <Link
            href="/radar"
            className="mt-3 inline-flex rounded-full bg-[#0b5672] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#0a4f67]"
          >
            Open radar
          </Link>
        </div>
      </aside>
    </div>
  );
}

