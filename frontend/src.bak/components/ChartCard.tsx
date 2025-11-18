import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

export default function ChartCard({ title, data }: { title:string; data:any[] }) {
  return (
    <div className="p-4 rounded-2xl glass">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium">{title}</h3>
        <div className="text-xs text-gray-400">Last 30d</div>
      </div>
      <div style={{ width: "100%", height: 200 }}>
        <ResponsiveContainer>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#7c3aed" stopOpacity={0.18}/>
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.08}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{fontSize:11}}/>
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="value" stroke="#7c3aed" fill="url(#grad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
