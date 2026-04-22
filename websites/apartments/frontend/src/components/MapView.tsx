"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useMemo, useRef } from "react";

import type { Listing } from "@/lib/types";

export function MapView({
  listings,
  center,
}: {
  listings: Listing[];
  center: { lat: number; lon: number };
}) {
  const mapRef = useRef<MapLibreMap | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const pins = useMemo(
    () =>
      listings
        .filter((l) => Number.isFinite(l.latitude) && Number.isFinite(l.longitude))
        .map((l) => ({ id: l.id, lat: l.latitude, lon: l.longitude })),
    [listings],
  );

  useEffect(() => {
    if (!containerRef.current) return;
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [center.lon, center.lat],
      zoom: 11,
      attributionControl: false,
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [center.lat, center.lon]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing markers by clearing the container’s marker nodes.
    // (Simple approach; good enough for this clone.)
    const existing = containerRef.current?.querySelectorAll("[data-pin='1']");
    existing?.forEach((n) => n.remove());

    pins.forEach((p) => {
      const el = document.createElement("div");
      el.dataset.pin = "1";
      el.style.width = "18px";
      el.style.height = "18px";
      el.style.background = "var(--apts-green)";
      el.style.borderRadius = "3px";
      el.style.transform = "rotate(45deg)";
      el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.35)";
      el.style.border = "2px solid rgba(255,255,255,0.85)";

      new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([p.lon, p.lat])
        .addTo(map);
    });
  }, [pins]);

  return <div ref={containerRef} className="h-full w-full" />;
}

