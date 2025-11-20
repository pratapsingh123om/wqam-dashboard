import { useEffect, useState } from "react";
import { fetchDemo, downloadLatestReportPdf } from "../services/api";
import type { DashboardData, UploadReport } from "../types/dashboard";
import MobilePreview from "../components/MobilePreview";

interface MobileViewProps {
  reports: UploadReport[];
  onRefresh: () => Promise<void>;
}

export default function MobileView({ reports, onRefresh }: MobileViewProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const latestReport = reports[0] ?? null;

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const dashboardData = await fetchDemo();
      setData(dashboardData);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }

  // Transform latest report data for mobile preview - dynamic based on latest upload
  const mobileData = latestReport ? {
    status: {
      nickname: latestReport.location?.location || latestReport.location?.state || "Water Quality Monitor",
      owner: latestReport.uploaded_by || "Operator",
      waterTemp: latestReport.parameters.find(p => p.parameter.toLowerCase().includes('temp') || p.parameter.toLowerCase().includes('temperature'))?.average || 
                 data?.mobile?.status?.waterTemp || 25,
      airTemp: data?.mobile?.status?.airTemp || 18,
      automation: true,
    },
    timeline: {
      day: new Date(latestReport.created_at).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' }),
      // Calculate operations based on report data
      filtrationHours: Math.round((latestReport.parameters.length * 2.5) % 24),
      cleaningMinutes: latestReport.alerts.length * 5, // More alerts = more cleaning needed
      disinfectionHours: Math.round((latestReport.parameters.filter(p => p.status !== 'ok').length * 1.5) % 24),
    },
    analysis: latestReport.parameters.slice(0, 4).map((param, idx) => {
      const tones: Array<"rose" | "amber" | "emerald" | "sky" | "violet"> = ["rose", "amber", "emerald", "sky", "violet"];
      return {
        label: param.parameter,
        value: param.average,
        unit: param.unit,
        tone: tones[idx % tones.length] as "rose" | "amber" | "emerald" | "sky" | "violet",
      };
    }),
  } : data?.mobile;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-blue-100 p-4 md:p-8">
      <div className="mx-auto max-w-md">
        {/* Mobile Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Water Quality</h1>
            <p className="text-sm text-gray-600">Monitoring Dashboard</p>
          </div>
          <button
            onClick={() => {
              loadData();
              onRefresh();
            }}
            disabled={loading}
            className="rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {/* Mobile Preview Component */}
        <div className="mb-6">
          <MobilePreview
            status={mobileData?.status}
            timeline={mobileData?.timeline}
            analysis={mobileData?.analysis}
          />
        </div>

        {/* Quick Actions */}
        {latestReport && (
          <div className="space-y-4">
            <div className="rounded-2xl bg-white p-4 shadow-lg">
              <h3 className="mb-3 text-lg font-semibold text-gray-900">Latest Analysis</h3>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  Source: <span className="font-medium">{latestReport.source_filename || "Unknown"}</span>
                </p>
                <p className="text-sm text-gray-600">
                  Date: <span className="font-medium">{new Date(latestReport.created_at).toLocaleString()}</span>
                </p>
                <p className="text-sm text-gray-600">
                  Parameters: <span className="font-medium">{latestReport.parameters.length} detected</span>
                </p>
              </div>
              <button
                onClick={async () => {
                  try {
                    const blob = await downloadLatestReportPdf();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `water_quality_report_${new Date().toISOString().split('T')[0]}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                  } catch (err) {
                    alert("Failed to download PDF");
                  }
                }}
                className="mt-4 w-full rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700"
              >
                Download PDF Report
              </button>
            </div>
          </div>
        )}

        {/* Instructions for Mobile Access */}
        <div className="mt-6 rounded-2xl bg-blue-50 p-4 text-sm text-gray-700">
          <p className="font-semibold mb-2">📱 Mobile Access:</p>
          <p className="mb-2">To access this on your phone:</p>
          <ol className="list-decimal list-inside space-y-1 mb-3">
            <li>Make sure your phone is on the same WiFi network</li>
            <li>Open your phone's browser</li>
            <li>Go to: <code className="bg-white px-2 py-1 rounded text-xs">http://10.14.20.186:5173/mobile</code></li>
          </ol>
          <p className="text-xs text-gray-600 mt-2">
            Current URL: <code className="bg-white px-1 rounded">{window.location.origin}/mobile</code>
          </p>
        </div>
      </div>
    </div>
  );
}

