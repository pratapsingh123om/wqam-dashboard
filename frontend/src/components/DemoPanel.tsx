interface DemoPanelProps {
  demoMode: boolean;
  onToggle: () => void;
  role?: string | null;
}

export default function DemoPanel({ demoMode, onToggle, role }: DemoPanelProps) {
  return (
    <div className="flex flex-wrap items-center gap-6 text-sm text-slate-200">
      <label className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-1.5">
        <input
          type="checkbox"
          checked={demoMode}
          onChange={onToggle}
          className="accent-blue-500"
        />
        Demo mode
      </label>
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500">Role</p>
        <p className="text-lg font-semibold text-white">{(role || "guest").toUpperCase()}</p>
      </div>
    </div>
  );
}
