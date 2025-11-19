
export default function Dashboard() {
  const cards = [
    { name: "pH", value: "7.2", trend: "+0.1" },
    { name: "Turbidity", value: "1.1 NTU", trend: "-0.2" },
    { name: "Temperature", value: "22.4°C", trend: "+1.2" },
    { name: "TDS", value: "320 ppm", trend: "+10" },
  ];

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold mb-4">Water Parameters</h1>

      <div className="grid grid-cols-4 gap-6">
        {cards.map((c) => (
          <div key={c.name} className="glass p-6 rounded-2xl">
            <div className="text-gray-300 text-sm">{c.name}</div>
            <div className="text-3xl font-bold mt-2">{c.value}</div>
            <div className="text-green-400 text-sm mt-1">{c.trend}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
