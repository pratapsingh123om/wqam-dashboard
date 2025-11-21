import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { DashboardSite } from "../types/dashboard";

interface MapViewProps {
  sites?: DashboardSite[];
}

const statusColor: Record<string, string> = {
  good: "#34d399",
  warning: "#f59e0b",
  poor: "#ef4444",
};

export default function MapView({ sites = [] }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    mapRef.current = L.map(containerRef.current, {
      zoomControl: false,
    }).setView([20.0, 78.0], 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(mapRef.current);

    sites.forEach((site) => {
      const tone = statusColor[site.status] ?? "#60a5fa";
      L.circleMarker([site.latitude, site.longitude], {
        radius: 8,
        color: tone,
        fillColor: tone,
        fillOpacity: 0.85,
      })
        .addTo(mapRef.current as L.Map)
        .bindPopup(
          `<strong>${site.name}</strong><br/>${site.county}<br/>Status: ${site.status}`
        );
    });

    if (sites.length > 0) {
      const bounds = L.latLngBounds(sites.map((s) => [s.latitude, s.longitude])) as L.LatLngBounds;
      mapRef.current.fitBounds(bounds.pad(0.3));
    }

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [sites]);

  return <div ref={containerRef} className="h-[360px] w-full rounded-2xl border border-white/5" />;
}
