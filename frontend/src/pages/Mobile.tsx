import MobilePreview from "../components/MobilePreview";
import type { DashboardData, UploadReport } from "../types/dashboard";

interface MobilePageProps {
  data: DashboardData | null;
  report: UploadReport | null;
  loading: boolean;
  onRefresh: () => Promise<void> | void;
}

export default function MobilePage({ data, report, loading, onRefresh }: MobilePageProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-white/5 p-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">Companion mode</p>
          <h2 className="text-2xl font-semibold text-white">Phone-friendly snapshot</h2>
          <p className="text-sm text-slate-400">
            This view mirrors what inspectors/residents see inside the mobile shell.
          </p>
        </div>
        <button
          onClick={() => onRefresh()}
          className="rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-white transition hover:border-white/60"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      <div className="mx-auto max-w-md rounded-3xl border border-white/5 bg-white/5 p-4">
        <MobilePreview
          status={data?.mobile.status}
          timeline={data?.mobile.timeline}
          analysis={data?.mobile.analysis}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm uppercase tracking-wide text-slate-400">Realtime alerts</p>
          {(!data || data.alerts.length === 0) && (
            <p className="mt-3 text-sm text-slate-400">No active alerts.</p>
          )}
          <div className="mt-3 space-y-3">
            {data?.alerts.map((alert) => (
              <div key={alert.id} className="rounded-xl bg-slate-900/40 px-4 py-3 text-sm">
                <p className="font-semibold text-white">{alert.title}</p>
                <p className="text-slate-300">{alert.message}</p>
                <p className="text-xs text-slate-500">
                  {new Date(alert.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm uppercase tracking-wide text-slate-400">Latest treatment summary</p>
          {!report ? (
            <p className="mt-3 text-sm text-slate-400">
              Upload a report to publish a mobile-facing summary.
            </p>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-slate-500">
                {report.source_filename ?? "upload"} • {new Date(report.created_at).toLocaleString()}
              </p>
              <div className="grid grid-cols-2 gap-3 text-sm text-slate-200">
                {report.parameters.map((param) => (
                  <div key={param.parameter} className="rounded-xl bg-slate-900/40 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-500">{param.parameter}</p>
                    <p className="text-lg font-semibold text-white">
                      {param.average.toFixed(2)} {param.unit}
                    </p>
                    <p className="text-[10px] text-slate-500">
                      {param.status.toUpperCase()}
                    </p>
                  </div>
                ))}
              </div>
              <ul className="list-disc space-y-1 pl-4 text-xs text-slate-400">
                {report.recommendations.map((rec) => (
                  <li key={rec}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

