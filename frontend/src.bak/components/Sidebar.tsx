import { Grid, Upload, Bell, PieChart } from "lucide-react";

const links = [
  { name: "Dashboard", hash: "/", icon: Grid },
  { name: "Uploads", hash: "/Upload", icon: Upload },
  { name: "Alerts", hash: "/alerts", icon: Bell },
  { name: "Reports", hash: "/reports", icon: PieChart },
];

export default function Sidebar() {
  return (
    <aside className="w-64 p-4 flex flex-col gap-4 bg-transparent">
      <nav className="space-y-2">
        {links.map((l) => {
          const Icon = l.icon;
          return (
            <a key={l.hash} href={"#"+l.hash} className="flex items-center gap-3 p-3 rounded-lg glass transition-smooth hover:translate-x-2">
              <div className="p-2 bg-white/6 rounded-md"><Icon size={18} /></div>
              <div className="font-medium">{l.name}</div>
            </a>
          );
        })}
      </nav>
      <div className="mt-auto text-xs text-gray-500 dark:text-gray-400"> WQAM</div>
    </aside>
  );
}
