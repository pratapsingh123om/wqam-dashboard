import type { UploadReport } from "../types/dashboard";

interface ReportsProps {
  reports: UploadReport[];
  loading: boolean;
  onRefresh: () => Promise<void> | void;
}

export default function Reports({ reports, loading, onRefresh }: ReportsProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-white/5 p-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">Reports library</p>
          <h2 className="text-2xl font-semibold text-white">Generated lab bundles</h2>
        </div>
        <button
          onClick={() => onRefresh()}
          className="rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-white transition hover:border-white/60"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-slate-400">
          Upload a CSV/PDF in the Uploads tab to populate this view.
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-white/5">
          <table className="min-w-full divide-y divide-white/5 text-sm text-slate-200">
            <thead className="bg-white/5 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3 text-left">Report</th>
                <th className="px-4 py-3 text-left">Uploaded By</th>
                <th className="px-4 py-3 text-left">Alerts</th>
                <th className="px-4 py-3 text-left">Recommendations</th>
                <th className="px-4 py-3 text-left">Generated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {reports.map((report) => (
                <tr key={report.id} className="bg-slate-900/40">
                  <td className="px-4 py-3 font-semibold text-white">
                    {report.source_filename ?? "upload"}{" "}
                    <span className="text-xs text-slate-400">
                      ({report.parameters.length} parameters)
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{report.uploaded_by}</td>
                  <td className="px-4 py-3">
                    {report.alerts.length === 0 ? (
                      <span className="text-emerald-300">0 issues</span>
                    ) : (
                      <span className="text-amber-300">{report.alerts.length} open</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    <ul className="list-disc space-y-1 pl-4 text-xs">
                      {report.recommendations.map((rec) => (
                        <li key={rec}>{rec}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(report.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
