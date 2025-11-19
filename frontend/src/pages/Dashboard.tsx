import KpiCard from "../components/KpiCard";
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

export default function Dashboard({ data, loading, error, onRefresh }: DashboardProps) {
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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/5 bg-white/5 p-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">Realtime Monitoring</p>
          <h2 className="text-2xl font-semibold text-white">Distribution network overview</h2>
        </div>
        <div className="flex items-center gap-3">
          {loading && <span className="text-xs uppercase tracking-wide text-slate-400">Syncing…</span>}
          <button
            onClick={onRefresh}
            className="rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-white transition hover:border-white/60"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {error}
        </div>
      )}

      {!data ? (
        emptyState
      ) : (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard title="pH (avg)" value={data.kpis.ph.toFixed(2)} trend="+0.1" accent />
            <KpiCard title="Dissolved O (mg/L)" value={data.kpis.do.toFixed(1)} trend="+0.6" />
            <KpiCard title="Temperature (°C)" value={data.kpis.temp.toFixed(1)} trend="-0.4" />
            <KpiCard title="Turbidity (NTU)" value={data.kpis.turbidity.toFixed(1)} trend="-0.2" />
          </section>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <ChartCard title="Water quality variance" data={data.timeseries} />

              <div className="rounded-2xl border border-white/5 bg-white/5 p-5">
                <p className="text-sm uppercase tracking-wide text-slate-400">Operations</p>
                <div className="mt-4 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl bg-slate-900/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Filtration</p>
                    <p className="mt-2 text-2xl font-semibold text-white">{data.operations.filtrationHours} h</p>
                    <p className="text-xs text-slate-500">Last 24h runtime</p>
                  </div>
                  <div className="rounded-2xl bg-slate-900/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Cleaning</p>
                    <p className="mt-2 text-2xl font-semibold text-white">{data.operations.cleaningMinutes} min</p>
                    <p className="text-xs text-slate-500">Settling & backwash</p>
                  </div>
                  <div className="rounded-2xl bg-slate-900/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500">Disinfection</p>
                    <p className="mt-2 text-2xl font-semibold text-white">{data.operations.disinfectionHours} h</p>
                    <p className="text-xs text-slate-500">Chlorine contact</p>
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
        </>
      )}
    </div>
  );
}
