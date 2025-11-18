import { ArrowUpRight, Users } from "lucide-react";

export default function MetricCard({ title, value, delta, accent }: { title:string; value:string; delta?:string; accent?:string }) {
  return (
    <div className="p-4 rounded-2xl glass transition-smooth card-hover">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-gray-400">{title}</div>
          <div className="flex items-center gap-3">
            <div className="text-2xl font-semibold">{value}</div>
            {delta && <div className="text-sm text-green-400">{delta} <ArrowUpRight size={12} /></div>}
          </div>
        </div>
        <div className="p-2 rounded-md bg-white/6">
          <Users size={20} />
        </div>
      </div>
      <div className="mt-3 text-xs text-gray-500">Compared to last 30d</div>
    </div>
  );
}
