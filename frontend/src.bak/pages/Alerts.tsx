export default function Alerts() {
  const alerts = [
    { id:1, level: "critical", text: "Postgres connection delays" },
    { id:2, level: "warning", text: "Validator timeouts rising" },
  ];
  return (
    <div className="space-y-4">
      {alerts.map(a => (
        <div key={a.id} className="p-4 rounded-2xl glass">
          <div className="font-medium">{a.level.toUpperCase()}</div>
          <div className="text-sm text-gray-400">{a.text}</div>
        </div>
      ))}
    </div>
  );
}
