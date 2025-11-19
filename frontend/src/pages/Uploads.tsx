import { useMemo, useState, type ChangeEvent } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { UploadReport, ParameterSummary } from "../types/dashboard";

interface UploadsProps {
  onUpload: (file: File) => Promise<UploadReport>;
  uploading: boolean;
  reports: UploadReport[];
}

const statusTone: Record<string, string> = {
  ok: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-100",
  critical: "border-rose-500/30 bg-rose-500/10 text-rose-100",
};

export default function Uploads({ onUpload, uploading, reports }: UploadsProps) {
  const [error, setError] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState<string | null>(null);
  const latestReport = useMemo(() => reports[0] ?? null, [reports]);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(null);
    setPreviewName(file.name);
    try {
      await onUpload(file);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
    } finally {
      event.target.value = "";
    }
  }

  const summary = latestReport?.parameters ?? [];

  const renderCard = (param: ParameterSummary) => (
    <div
      key={param.parameter}
      className={`rounded-2xl border px-4 py-4 ${statusTone[param.status] ?? statusTone.ok}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">{param.parameter}</span>
        <span className="text-xs uppercase tracking-wide opacity-70">{param.status}</span>
      </div>
      <p className="mt-2 text-3xl font-semibold">
        {param.average.toFixed(2)}
        <span className="ml-1 text-base text-slate-200">{param.unit}</span>
      </p>
      <p className="text-xs opacity-70">
        Range {param.minimum.toFixed(2)} – {param.maximum.toFixed(2)} {param.unit}
      </p>
      {param.directive && (
        <p className="mt-2 text-xs text-white/80">
          <span className="font-semibold">Action:</span> {param.directive}
        </p>
      )}
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="rounded-3xl border border-dashed border-white/20 bg-white/5 p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-slate-400">Lab ingestion</p>
            <h2 className="text-3xl font-semibold text-white">Upload CSV/PDF reports</h2>
            <p className="text-sm text-slate-400">
              Drag and drop water quality data (pH, DO, Turbidity, TDS, Chlorine). We validate, chart and
              create a treatment summary automatically.
            </p>
          </div>
          <label className="flex cursor-pointer flex-col items-center rounded-2xl border border-white/20 px-8 py-5 text-center text-slate-200 transition hover:border-white/60">
            <span className="text-lg font-semibold">
              {uploading ? "Processing…" : "Select file"}
            </span>
            <span className="text-xs uppercase tracking-wide text-slate-400">CSV · PDF</span>
            <input
              type="file"
              accept=".csv,.pdf,.xlsx,.xls"
              className="hidden"
              onChange={handleFileChange}
              disabled={uploading}
            />
          </label>
        </div>
        {previewName && (
          <p className="mt-4 text-xs text-slate-500">
            Selected: <span className="font-semibold text-slate-200">{previewName}</span>
          </p>
        )}
        {error && (
          <div className="mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </div>
        )}
      </div>

      {!latestReport ? (
        <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-slate-400">
          <p>No uploads yet. Drop a CSV/PDF report to generate insights.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {summary.map(renderCard)}
          </div>

            <div className="rounded-3xl border border-white/5 bg-white/5 p-6 space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-wide text-slate-400">Trend plots</p>
                  <h3 className="text-xl font-semibold text-white">Realtime reconstruction</h3>
                </div>
                <p className="text-xs text-slate-400">
                  Generated {new Date(latestReport.created_at).toLocaleString()}
                </p>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                {latestReport.timeseries.map((series) => (
                  <div key={series.parameter} className="rounded-2xl bg-slate-900/40 p-4">
                    <p className="text-sm font-semibold text-white">{series.parameter}</p>
                    <div className="mt-3 h-48">
                      <ResponsiveContainer>
                        <LineChart data={series.points}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis
                            dataKey="timestamp"
                            tickFormatter={(value) => new Date(value).toLocaleDateString()}
                            minTickGap={24}
                            stroke="#94a3b8"
                          />
                          <YAxis stroke="#94a3b8" />
                          <Tooltip
                            contentStyle={{ background: "#0f172a", borderRadius: 12, border: "1px solid #1e293b" }}
                            labelFormatter={(value) => new Date(value).toLocaleString()}
                          />
                          <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          <div className="rounded-3xl border border-white/5 bg-white/5 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-400">Treatment guidance</p>
                <h3 className="text-xl font-semibold text-white">Recommendations</h3>
              </div>
              <span className="text-xs text-slate-400">
                {latestReport.source_filename ?? "upload"} · {new Date(latestReport.created_at).toLocaleString()}
              </span>
            </div>
            <ul className="mt-4 list-outside space-y-2 text-sm text-slate-200">
              {latestReport.recommendations.map((tip) => (
                <li key={tip} className="rounded-2xl bg-slate-900/40 px-4 py-3">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {reports.length > 1 && (
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-white">History</p>
            <p className="text-xs text-slate-400">{reports.length} generated</p>
          </div>
          <div className="divide-y divide-white/5">
            {reports.map((report) => (
              <div key={report.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm text-slate-300">
                <div>
                  <p className="font-medium text-white">
                    {report.source_filename ?? "upload"}
                  </p>
                  <p className="text-xs text-slate-400">
                    {new Date(report.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  {report.parameters.filter((p) => p.status !== "ok").length} alerts
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
