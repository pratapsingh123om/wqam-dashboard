import ThemeToggle from "./ThemeToggle";
import { Search } from "lucide-react";

export default function Header() {
  return (
    <header className="flex items-center justify-between p-4 bg-transparent">
      <div className="flex items-center gap-4">
        <div className="p-2 rounded-xl glass flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-600 to-cyan-400 flex items-center justify-center text-white font-bold">WQ</div>
          <div>
            <div className="text-lg font-semibold">WQAM Dashboard</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Org: Example  Env: dev</div>
          </div>
        </div>

        <div className="relative ml-2">
          <input placeholder='Search metrics, uploads, alerts...' className="pl-10 pr-4 py-2 rounded-xl bg-white/5 glass border border-transparent focus:border-white/20 transition-smooth w-72" />
          <div className="absolute left-3 top-2 text-gray-400"><Search size={16} /></div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="py-2 px-4 rounded-xl glass transition-smooth hover:scale-105">Demo</button>
        <ThemeToggle />
      </div>
    </header>
  );
}
