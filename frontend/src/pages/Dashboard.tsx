import { useMemo } from "react";
import ChartCard from "../components/ChartCard";
import MapView from "../components/MapView";
import type { DashboardData } from "../types/dashboard";

interface DashboardProps {
  data: DashboardData | null;
  loading: boolean;
  error?: string | null;
  onRefresh: () => Promise<void> | void;
}

const severityStyles: Record<string, string> = {
  info: "border-slate-700 bg-slate-900/60 text-slate-300",
  warning: "border-amber-500/50 bg-amber-500/10 text-amber-200",
  critical: "border-rose-500/50 bg-rose-500/10 text-rose-100",
};

export default function Dashboard({ data, error, onRefresh }: DashboardProps) {
  const currentTime = useMemo(() => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }, []);

  const emptyState = (
    <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-slate-400">
      <p>No telemetry yet. Connect to the backend and refresh.</p>
      <button
        onClick={onRefresh}
        className="mt-4 rounded-full bg-white/10 px-6 py-2 text-sm text-white transition hover:bg-white/20"
      >
        Retry fetch
      </button>
    </div>
  );

  if (!data) {
    return emptyState;
  }

  const waterTemp = data.kpis.temp;
  const airTemp = data.mobile?.status?.airTemp || 18;
  const automation = data.mobile?.status?.automation || true;

  return (
    <div className="space-y-6">
      {/* Header Section - Pool Care Style */}
      <div className="rounded-3xl bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-sm opacity-90">{currentTime}</p>
            <h1 className="text-2xl font-bold mt-1">Good Morning, Operator</h1>
          </div>
          <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
            <span className="text-xl">👤</span>
          </div>
        </div>
        
        <div className="text-center mb-4">
          <p className="text-lg font-semibold mb-2">Effortless Water Quality Management</p>
        </div>

        {/* Large Temperature Gauge */}
        <div className="flex flex-col items-center justify-center my-8">
          <div className="relative w-48 h-48 rounded-full border-4 border-white/30 bg-white/10 flex items-center justify-center">
            <div className="text-center">
              <div className="text-5xl font-bold">{waterTemp.toFixed(1)}°C</div>
              <p className="text-sm uppercase tracking-wide opacity-80 mt-2">Water Temperature</p>
            </div>
            <div className="absolute inset-4 rounded-full border-2 border-white/40"></div>
          </div>
          <p className="text-sm mt-4 opacity-90">Air: {airTemp}°C</p>
        </div>

        {/* Control Cards - Pool Care Style */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="rounded-2xl bg-pink-500/20 backdrop-blur-sm border border-pink-400/30 p-4 text-center">
            <div className="text-2xl mb-2">🏠</div>
            <p className="text-xs font-semibold">Auto 24h</p>
            <p className="text-sm font-bold mt-1">{automation ? "ON" : "OFF"}</p>
          </div>
          <div className="rounded-2xl bg-green-500/20 backdrop-blur-sm border border-green-400/30 p-4 text-center">
            <div className="text-2xl mb-2">🌡️</div>
            <p className="text-xs font-semibold">Air Temp</p>
            <p className="text-sm font-bold mt-1">{airTemp}°C</p>
          </div>
          <div className="rounded-2xl bg-blue-500/20 backdrop-blur-sm border border-blue-400/30 p-4 text-center">
            <div className="text-2xl mb-2">💧</div>
            <p className="text-xs font-semibold">Water Temp</p>
            <p className="text-sm font-bold mt-1">{waterTemp.toFixed(1)}°C</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {error}
        </div>
      )}

      {/* KPI Cards - Modern Style */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 border border-purple-400/30 p-5 backdrop-blur-sm">
          <p className="text-xs uppercase tracking-wide text-purple-200 mb-2">pH Level</p>
          <p className="text-3xl font-bold text-white">{data.kpis.ph.toFixed(2)}</p>
          <p className="text-xs text-purple-300 mt-1">Average reading</p>
        </div>
        <div className="rounded-2xl bg-gradient-to-br from-cyan-500/20 to-cyan-600/20 border border-cyan-400/30 p-5 backdrop-blur-sm">
          <p className="text-xs uppercase tracking-wide text-cyan-200 mb-2">Dissolved Oxygen</p>
          <p className="text-3xl font-bold text-white">{data.kpis.do.toFixed(1)} mg/L</p>
          <p className="text-xs text-cyan-300 mt-1">Average reading</p>
        </div>
        <div className="rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-600/20 border border-orange-400/30 p-5 backdrop-blur-sm">
          <p className="text-xs uppercase tracking-wide text-orange-200 mb-2">Temperature</p>
          <p className="text-3xl font-bold text-white">{data.kpis.temp.toFixed(1)}°C</p>
          <p className="text-xs text-orange-300 mt-1">Current</p>
        </div>
        <div className="rounded-2xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 border border-emerald-400/30 p-5 backdrop-blur-sm">
          <p className="text-xs uppercase tracking-wide text-emerald-200 mb-2">Turbidity</p>
          <p className="text-3xl font-bold text-white">{data.kpis.turbidity.toFixed(1)} NTU</p>
          <p className="text-xs text-emerald-300 mt-1">Average reading</p>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ChartCard title="Water quality variance" data={data.timeseries} />

          {/* Operations Cards - Pool Care Style */}
          <div className="rounded-2xl border border-white/5 bg-white/5 p-5">
            <p className="text-sm uppercase tracking-wide text-slate-400 mb-4">Operations Status</p>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-400/30 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🔧</span>
                  <p className="text-xs uppercase tracking-wide text-blue-200">Filtration</p>
                </div>
                <p className="text-2xl font-semibold text-white">{data.operations.filtrationHours} h</p>
                <p className="text-xs text-blue-300 mt-1">Last 24h runtime</p>
              </div>
              <div className="rounded-2xl bg-gradient-to-br from-pink-500/20 to-pink-600/20 border border-pink-400/30 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🧹</span>
                  <p className="text-xs uppercase tracking-wide text-pink-200">Cleaning</p>
                </div>
                <p className="text-2xl font-semibold text-white">{data.operations.cleaningMinutes} min</p>
                <p className="text-xs text-pink-300 mt-1">Settling & backwash</p>
              </div>
              <div className="rounded-2xl bg-gradient-to-br from-green-500/20 to-green-600/20 border border-green-400/30 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🧪</span>
                  <p className="text-xs uppercase tracking-wide text-green-200">Disinfection</p>
                </div>
                <p className="text-2xl font-semibold text-white">{data.operations.disinfectionHours} h</p>
                <p className="text-xs text-green-300 mt-1">Chlorine contact</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <p className="mb-3 text-sm font-semibold text-white">Network map</p>
            <MapView sites={data.sites} />
          </div>

          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-white">Live alerts</p>
              <span className="text-xs text-slate-400">{data.alerts.length} open</span>
            </div>
            <div className="space-y-3">
              {data.alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`rounded-xl border px-4 py-3 text-sm ${severityStyles[alert.severity]}`}
                >
                  <p className="font-semibold">{alert.title}</p>
                  <p className="text-xs opacity-70">{alert.message}</p>
                  <p className="mt-1 text-[10px] uppercase tracking-wide opacity-60">
                    {new Date(alert.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
