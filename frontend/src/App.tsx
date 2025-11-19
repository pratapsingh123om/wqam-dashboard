import { useCallback, useEffect, useMemo, useState } from "react";
import Sidebar from "./layout/Sidebar";
import NavBar from "./components/NavBar";
import DemoPanel from "./components/DemoPanel";
import Dashboard from "./pages/Dashboard";
import Uploads from "./pages/Uploads";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import MobilePreview from "./components/MobilePreview";
import MobilePage from "./pages/Mobile";
import MobileView from "./pages/MobileView";
import Login from "./pages/Login";
import { fetchDemo, fetchReports, setAuthToken, uploadWaterData } from "./services/api";
import { login as loginRequest } from "./services/auth";
import type { DashboardData, UploadReport } from "./types/dashboard";

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [route, setRoute] = useState("/");
  const [role, setRole] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [reports, setReports] = useState<UploadReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [uploadingReport, setUploadingReport] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!token) return;
    setLoadingDashboard(true);
    setDashboardError(null);
    try {
      const payload = await fetchDemo();
      setDashboardData(payload);
    } catch (err) {
      setDashboardError(err instanceof Error ? err.message : "Unable to fetch dashboard data");
    } finally {
      setLoadingDashboard(false);
    }
  }, [token]);

  const loadReports = useCallback(async () => {
    if (!token) return;
    setReportsLoading(true);
    try {
      const payload = await fetchReports();
      setReports(payload);
    } catch (err) {
      console.error(err);
    } finally {
      setReportsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setDashboardData(null);
      setReports([]);
      return;
    }
    loadDashboard();
    loadReports();
  }, [token, loadDashboard, loadReports]);

  async function handleLogin(credentials: { username: string; password: string }) {
    try {
      setIsLoggingIn(true);
      setLoginError(null);
      const result = await loginRequest(credentials.username, credentials.password);
      setToken(result.access_token);
      setRole(result.role);
      setAuthToken(result.access_token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to login";
      setLoginError(message);
    } finally {
      setIsLoggingIn(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setRole(null);
    setAuthToken(null);
    setDashboardData(null);
    setReports([]);
    setRoute("/");
  }

  const handleUpload = useCallback(async (file: File) => {
    setUploadingReport(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const report = await uploadWaterData(formData);
      setReports((prev) => [report, ...prev]);
      return report;
    } finally {
      setUploadingReport(false);
    }
  }, []);

  const currentPage = useMemo(() => {
    switch (route) {
      case "/uploads":
        return <Uploads onUpload={handleUpload} uploading={uploadingReport} reports={reports} />;
      case "/alerts":
        return (
          <Alerts
            alerts={dashboardData?.alerts ?? []}
            loading={loadingDashboard}
            onRefresh={loadDashboard}
          />
        );
      case "/reports":
        return <Reports reports={reports} loading={reportsLoading} onRefresh={loadReports} />;
      case "/mobile":
        // Check if on mobile device or small screen
        const isMobile = window.innerWidth < 768;
        if (isMobile) {
          return <MobileView reports={reports} onRefresh={loadReports} />;
        }
        return (
          <MobilePage
            data={dashboardData}
            report={reports[0] ?? null}
            loading={loadingDashboard}
            onRefresh={loadDashboard}
          />
        );
      default:
        return (
          <Dashboard
            data={dashboardData}
            loading={loadingDashboard}
            error={dashboardError}
            onRefresh={loadDashboard}
          />
        );
    }
  }, [
    route,
    dashboardData,
    loadingDashboard,
    dashboardError,
    loadDashboard,
    handleUpload,
    reports,
    uploadingReport,
    reportsLoading,
    loadReports,
  ]);

  if (!token) {
    return <Login onLogin={handleLogin} loading={isLoggingIn} error={loginError} />;
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-white">
      <Sidebar route={route} role={role || "user"} onLogout={handleLogout} onNavigate={setRoute} />

      <main className="flex flex-1 flex-col overflow-hidden">
        <NavBar />
        <div className="flex flex-1 flex-col gap-6 p-6 xl:flex-row">
          <section className="flex-1 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-white/5 p-4">
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-400">Monitoring hub</p>
                <h1 className="text-2xl font-semibold text-white">Central dashboard</h1>
              </div>
              <DemoPanel demoMode={demoMode} onToggle={() => setDemoMode((prev) => !prev)} role={role} />
            </div>
            <div className="rounded-3xl bg-white/5 p-2 shadow-inner">
              <div className="rounded-[28px] border border-white/5 bg-slate-900/40 p-6">
                {currentPage}
              </div>
            </div>
          </section>

          <aside className="w-full xl:w-[360px] 2xl:w-[420px]">
            <div className="rounded-3xl border border-white/5 bg-white/5 p-4 backdrop-blur-xl">
              <div className="mb-4">
                <p className="text-sm uppercase tracking-wide text-slate-400">Mobile companion</p>
                <h2 className="text-xl font-semibold text-white">Real-time snapshot</h2>
                <p className="text-xs text-slate-400">
                  Give operators and residents a lightweight view of reports, chemistry and controls.
                </p>
              </div>
              <MobilePreview
                status={reports[0] ? {
                  nickname: "Water Quality Monitor",
                  owner: reports[0].uploaded_by || dashboardData?.mobile.status?.owner || "Operator",
                  waterTemp: reports[0].parameters.find(p => p.parameter.toLowerCase().includes('temp'))?.average || dashboardData?.mobile.status?.waterTemp || 25,
                  airTemp: dashboardData?.mobile.status?.airTemp || 18,
                  automation: dashboardData?.mobile.status?.automation || true,
                } : dashboardData?.mobile.status}
                timeline={reports[0] ? {
                  day: new Date(reports[0].created_at).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' }),
                  filtrationHours: dashboardData?.mobile.timeline?.filtrationHours || 17,
                  cleaningMinutes: dashboardData?.mobile.timeline?.cleaningMinutes || 0,
                  disinfectionHours: dashboardData?.mobile.timeline?.disinfectionHours || 12,
                } : dashboardData?.mobile.timeline}
                analysis={reports[0] ? reports[0].parameters.slice(0, 4).map((param, idx) => {
                  const tones: Array<"rose" | "amber" | "emerald" | "sky" | "violet"> = ["rose", "amber", "emerald", "sky", "violet"];
                  return {
                    label: param.parameter,
                    value: param.average,
                    unit: param.unit,
                    tone: tones[idx % tones.length] as "rose" | "amber" | "emerald" | "sky" | "violet",
                  };
                }) : dashboardData?.mobile.analysis}
              />
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
