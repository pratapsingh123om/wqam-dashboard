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
import { downloadLatestReportPdf } from "../services/api";

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
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const latestReport = useMemo(() => {
    const report = reports[0] ?? null;
    if (report) {
      console.log("[DEBUG] Latest report:", {
        id: report.id,
        timeseriesCount: report.timeseries?.length || 0,
        timeseries: report.timeseries?.map(s => ({
          parameter: s.parameter,
          pointsCount: s.points?.length || 0
        }))
      });
    }
    return report;
  }, [reports]);
  
  async function handleDownloadPdf() {
    if (!latestReport) {
      console.error("[ERROR] No latest report available");
      setError("No report available to download");
      return;
    }
    if (downloadingPdf) {
      console.log("[DEBUG] Download already in progress, skipping");
      return; // Prevent double download
    }
    console.log("[DEBUG] Attempting to download PDF for report:", latestReport.id);
    setDownloadingPdf(true);
    setError(null);
    try {
      const blob = await downloadLatestReportPdf();
      console.log("[DEBUG] PDF downloaded successfully, size:", blob.size);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `water_quality_report_${latestReport.id.slice(0, 8)}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      // Small delay before cleanup to ensure download starts
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
    } catch (err) {
      console.error("[ERROR] PDF download failed:", err);
      setError(err instanceof Error ? err.message : "Failed to download PDF");
    } finally {
      setDownloadingPdf(false);
    }
  }

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
                <div className="flex items-center gap-3">
                  <p className="text-xs text-slate-400">
                    Generated {new Date(latestReport.created_at).toLocaleString()}
                  </p>
                  <button
                    onClick={handleDownloadPdf}
                    disabled={downloadingPdf}
                    className="rounded-full border border-emerald-500/40 bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-200 transition hover:border-emerald-500/60 hover:bg-emerald-500/30 disabled:opacity-50"
                  >
                    {downloadingPdf ? "Generating..." : "Download PDF Report"}
                  </button>
                </div>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                {latestReport.timeseries && latestReport.timeseries.length > 0 ? (
                  latestReport.timeseries.map((series, idx) => {
                    console.log(`[DEBUG] Rendering chart ${idx} for ${series.parameter}:`, {
                      parameter: series.parameter,
                      pointsCount: series.points?.length || 0,
                      firstPoint: series.points?.[0],
                    });
                    
                    if (!series.points || series.points.length === 0) {
                      return (
                        <div key={series.parameter || idx} className="rounded-2xl bg-slate-900/40 p-4">
                          <p className="text-sm font-semibold text-white mb-2">{series.parameter || "Unknown"}</p>
                          <p className="text-xs text-slate-400">No data points available</p>
                        </div>
                      );
                    }
                    
                    // Transform points for Recharts - ensure proper format with error handling
                    const chartData = series.points
                      .filter(p => p && p.timestamp && (p.value != null && !isNaN(Number(p.value))))
                      .map((point) => {
                        try {
                          const timestamp = point.timestamp;
                          const value = Number(point.value);
                          if (isNaN(value)) {
                            console.warn(`[WARN] Invalid value for point:`, point);
                            return null;
                          }
                          return {
                            timestamp: timestamp,
                            value: value,
                            date: new Date(timestamp).toLocaleDateString(),
                            time: new Date(timestamp).toLocaleTimeString(),
                          };
                        } catch (e) {
                          console.error("[ERROR] Failed to parse point:", point, e);
                          return null;
                        }
                      })
                      .filter(p => p !== null);
                    
                    if (chartData.length === 0) {
                      return (
                        <div key={series.parameter || idx} className="rounded-2xl bg-slate-900/40 p-4">
                          <p className="text-sm font-semibold text-white mb-2">{series.parameter || "Unknown"}</p>
                          <p className="text-xs text-slate-400">No valid data points after filtering</p>
                        </div>
                      );
                    }
                    
                    return (
                      <div key={series.parameter || idx} className="rounded-2xl bg-slate-900/40 p-4">
                        <p className="text-sm font-semibold text-white mb-2">{series.parameter || "Unknown"}</p>
                        <div className="mt-3 h-48 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                              <XAxis
                                dataKey="timestamp"
                                tickFormatter={(value) => {
                                  try {
                                    return new Date(value).toLocaleDateString();
                                  } catch {
                                    return String(value);
                                  }
                                }}
                                minTickGap={24}
                                stroke="#94a3b8"
                                fontSize={12}
                              />
                              <YAxis stroke="#94a3b8" fontSize={12} />
                              <Tooltip
                                contentStyle={{ background: "#0f172a", borderRadius: 12, border: "1px solid #1e293b", color: "#fff" }}
                                labelFormatter={(value) => {
                                  try {
                                    return new Date(value).toLocaleString();
                                  } catch {
                                    return String(value);
                                  }
                                }}
                                formatter={(value: number) => [value?.toFixed(2) || "N/A", "Value"]}
                              />
                              <Line 
                                type="monotone" 
                                dataKey="value" 
                                stroke="#38bdf8" 
                                strokeWidth={2} 
                                dot={{ r: 3 }} 
                                activeDot={{ r: 5 }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="col-span-2 rounded-2xl border border-dashed border-white/10 p-10 text-center text-slate-400">
                    <p>No timeseries data available for plotting</p>
                    <p className="text-xs mt-2">
                      {latestReport.timeseries ? 
                        `Report has ${latestReport.timeseries.length} timeseries but they may be empty` :
                        "Report has no timeseries property"}
                    </p>
                    <p className="text-xs mt-1">Check browser console (F12) for debug information</p>
                  </div>
                )}
              </div>
            </div>

          {latestReport.ml_insights && latestReport.ml_insights.model_available && (
            <div className="rounded-3xl border border-violet-500/30 bg-violet-500/10 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-wide text-violet-300">AI-Powered Analysis</p>
                  <h3 className="text-xl font-semibold text-white">ML Predictions & Forecasts</h3>
                </div>
                <span className="rounded-full border border-violet-500/40 bg-violet-500/20 px-3 py-1 text-xs font-semibold text-violet-200">
                  ML Enabled
                </span>
              </div>
              
              <div className="mt-6 grid gap-4 md:grid-cols-3">
                {latestReport.ml_insights.pollution_prediction !== null && latestReport.ml_insights.pollution_prediction !== undefined && (
                  <div className="rounded-2xl border border-violet-500/30 bg-slate-900/60 px-4 py-4">
                    <p className="text-xs uppercase tracking-wide text-violet-300">Predicted Pollution</p>
                    <p className="mt-2 text-3xl font-semibold text-white">
                      {latestReport.ml_insights.pollution_prediction.toFixed(2)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">ML Model Prediction</p>
                  </div>
                )}
                
                {latestReport.ml_insights.pollution_score !== null && latestReport.ml_insights.pollution_score !== undefined && (
                  <div className="rounded-2xl border border-violet-500/30 bg-slate-900/60 px-4 py-4">
                    <p className="text-xs uppercase tracking-wide text-violet-300">Pollution Score</p>
                    <p className="mt-2 text-3xl font-semibold text-white">
                      {latestReport.ml_insights.pollution_score.toFixed(1)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      Status: {latestReport.ml_insights.pollution_label ?? "N/A"}
                    </p>
                  </div>
                )}
                
                {latestReport.ml_insights.forecasts && Object.keys(latestReport.ml_insights.forecasts).length > 0 && (
                  <div className="rounded-2xl border border-violet-500/30 bg-slate-900/60 px-4 py-4">
                    <p className="text-xs uppercase tracking-wide text-violet-300">Forecasts Available</p>
                    <p className="mt-2 text-3xl font-semibold text-white">
                      {Object.keys(latestReport.ml_insights.forecasts).length}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">Parameters with forecasts</p>
                  </div>
                )}
              </div>

              {latestReport.ml_insights.forecasts && Object.keys(latestReport.ml_insights.forecasts).length > 0 && (
                <div className="mt-6 space-y-4">
                  <p className="text-sm font-semibold text-white">Parameter Forecasts (Next 3 Steps)</p>
                  <div className="grid gap-3 md:grid-cols-2">
                    {Object.entries(latestReport.ml_insights.forecasts).map(([param, values]) => (
                      <div key={param} className="rounded-xl border border-violet-500/20 bg-slate-900/40 px-4 py-3">
                        <p className="text-sm font-semibold text-violet-200">{param.toUpperCase()}</p>
                        <div className="mt-2 flex gap-2">
                          {values.map((val, idx) => (
                            <div key={idx} className="flex-1 rounded-lg border border-violet-500/30 bg-violet-500/10 px-2 py-1 text-center">
                              <p className="text-xs text-violet-300">Step {idx + 1}</p>
                              <p className="text-sm font-semibold text-white">{val.toFixed(2)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

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
