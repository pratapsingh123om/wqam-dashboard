import type { DashboardAlert } from "../types/dashboard";

interface AlertsProps {
  alerts: DashboardAlert[];
  loading: boolean;
  onRefresh: () => Promise<void> | void;
}

const severityBadge: Record<string, string> = {
  info: "bg-sky-500/20 text-sky-200 border-sky-400/40",
  warning: "bg-amber-500/20 text-amber-200 border-amber-400/40",
  critical: "bg-rose-500/20 text-rose-200 border-rose-400/40",
};

export default function Alerts({ alerts, loading, onRefresh }: AlertsProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-white/5 p-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">Alert center</p>
          <h2 className="text-2xl font-semibold text-white">Water quality incidents</h2>
        </div>
        <button
          onClick={() => onRefresh()}
          className="rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-white transition hover:border-white/60"
        >
          {loading ? "Syncing…" : "Refresh"}
        </button>
      </div>

      {alerts.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-slate-400">
          No active alerts. All parameters are within target thresholds.
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-2xl border border-white/5 bg-white/5 p-4 shadow-inner shadow-black/30"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-lg font-semibold text-white">{alert.title}</p>
                  <p className="text-sm text-slate-300">{alert.message}</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${severityBadge[alert.severity]}`}>
                  {alert.severity}
                </span>
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Logged {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
