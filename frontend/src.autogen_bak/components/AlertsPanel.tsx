import api from "../services/api";

export default function AlertsPanel({ orgId=1 }: { orgId?: number }) {
  const [alerts, setAlerts] = useState<any[]>([]);
  useEffect(() => {
    api.get(`/org/${orgId}/alerts`).then(r => setAlerts(r.data.alerts || []));
  }, []);
  return (
    <div className="bg-white/5 rounded-lg p-4 shadow">
      <div className="text-sm text-slate-400">Recent Alerts</div>
      <ul className="mt-2 space-y-2">
        {alerts.map((a:any) => (
          <li key={a.id} className="border-l-4 border-red-500 pl-3">
            <div className="text-sm font-medium">{a.parameter} breached</div>
            <div className="text-xs text-slate-400">{a.value}</div>
          </li>
        ))}
        {alerts.length===0 && <li className="text-sm text-slate-400">No alerts</li>}
      </ul>
    </div>
  );
}
