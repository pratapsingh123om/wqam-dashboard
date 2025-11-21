import type {
  DashboardMobileStatus,
  DashboardMobileTimeline,
  DashboardMobileAnalysis,
} from "../types/dashboard";

interface MobilePreviewProps {
  status?: DashboardMobileStatus;
  timeline?: DashboardMobileTimeline;
  analysis?: DashboardMobileAnalysis[];
}

const toneClass: Record<
  NonNullable<MobilePreviewProps["analysis"]>[number]["tone"],
  string
> = {
  rose: "bg-rose-100 text-rose-600 border-rose-200",
  amber: "bg-amber-100 text-amber-600 border-amber-200",
  emerald: "bg-emerald-100 text-emerald-600 border-emerald-200",
  sky: "bg-sky-100 text-sky-600 border-sky-200",
  violet: "bg-violet-100 text-violet-600 border-violet-200",
};

export default function MobilePreview({
  status = {
    nickname: "Effortless Pool",
    owner: "Operator",
    waterTemp: 25,
    airTemp: 18,
    automation: true,
  },
  timeline = {
    day: "Tue 25",
    filtrationHours: 17,
    cleaningMinutes: 0,
    disinfectionHours: 12,
  },
  analysis = [
    { label: "Free chlorine", value: 0.27, unit: "ppm", tone: "rose" },
    { label: "Combined chlorine", value: 0, unit: "ppm", tone: "emerald" },
    { label: "pH", value: 7.5, unit: "", tone: "amber" },
    { label: "Total chlorine", value: 2.1, unit: "ppm", tone: "violet" },
  ],
}: MobilePreviewProps) {
  return (
    <div className="mx-auto w-full max-w-[360px] rounded-[32px] bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-900/80 p-4 text-slate-100 shadow-2xl">
      <div className="rounded-[28px] bg-white/10 backdrop-blur-xl">
        <section className="rounded-t-[28px] bg-[radial-gradient(circle_at_top,_#34b3ff,_#0f172a)] p-5 text-white">
          <div className="flex items-center justify-between text-xs uppercase tracking-wide opacity-80">
            <span>{status.nickname}</span>
            <span>{status.owner}</span>
          </div>
          <div className="mt-6 flex flex-col items-center gap-4">
            <div className="flex flex-col items-center gap-2">
              <span className="text-sm font-medium">Water · {status.waterTemp}°C</span>
              <div className="relative flex h-36 w-36 items-center justify-center rounded-full border border-white/30 bg-white/5">
                <div className="text-center">
                  <div className="text-4xl font-semibold">{status.waterTemp}°C</div>
                  <p className="text-xs uppercase tracking-wide opacity-80">
                    Live Temp
                  </p>
                </div>
                <div className="absolute inset-2 rounded-full border border-white/40" />
              </div>
            </div>
            <div className="flex w-full items-center justify-between text-xs">
              <div className="flex flex-col">
                <span className="opacity-70">Air Temp</span>
                <span className="text-lg font-semibold">{status.airTemp}°C</span>
              </div>
              <div className="flex flex-col text-right">
                <span className="opacity-70">Automation</span>
                <span className="text-lg font-semibold">
                  {status.automation ? "ON" : "OFF"}
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4 p-5">
          <div>
            <div className="text-sm font-semibold text-slate-200">Report</div>
            <div className="mt-1 text-xs text-slate-400">My Lovely Pool · {timeline.day}</div>
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
                <span>Filtration time</span>
                <span>{timeline.filtrationHours}h</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-sky-400"
                  style={{ width: `${Math.min(timeline.filtrationHours, 24) / 24 * 100}%` }}
                />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-center text-xs">
                <div className="rounded-xl bg-slate-900/40 p-3">
                  <p className="text-slate-400">Cleaning</p>
                  <p className="text-lg font-semibold text-white">{timeline.cleaningMinutes} min</p>
                </div>
                <div className="rounded-xl bg-slate-900/40 p-3">
                  <p className="text-slate-400">Disinfection</p>
                  <p className="text-lg font-semibold text-white">
                    {timeline.disinfectionHours} hrs
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-slate-200">Analysis</div>
            <div className="mt-1 text-xs text-slate-400">Realtime chemistry checks</div>
            <div className="mt-4 space-y-3">
              {analysis.map((item) => (
                <div
                  key={item.label}
                  className={`rounded-2xl border px-4 py-3 ${toneClass[item.tone]}`}
                >
                  <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wide">
                    <span>{item.label}</span>
                    <span>{new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {item.value}
                    {item.unit ? (
                      <span className="text-base font-medium text-slate-500"> {item.unit}</span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

