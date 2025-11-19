import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function ChartCard({title,data}:any){
  return (
    <div className="glass p-4 rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-gray-800">{title}</h3>
        <div className="text-sm text-gray-400">Last 30d</div>
      </div>
      <div style={{width:"100%", height:220}}>
        <ResponsiveContainer>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="g1" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#7c3aed" stopOpacity={0.18}/>
                <stop offset="100%" stopColor="#7c3aed" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={false}/>
            <YAxis tick={false}/>
            <Tooltip />
            <Area dataKey="value" stroke="#7c3aed" fill="url(#g1)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
