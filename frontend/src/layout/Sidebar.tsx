// frontend/src/layout/Sidebar.tsx

interface SidebarProps {
  route: string;
  onNavigate: (path: string) => void;
  role?: string | null;
  onLogout: () => void;
}

const links = [
  { name: "Dashboard", path: "/", roles: ["user", "validator", "admin"] },
  { name: "Uploads", path: "/uploads", roles: ["user", "admin"] },
  { name: "Alerts", path: "/alerts", roles: ["admin", "validator", "user"] },
  { name: "Reports", path: "/reports", roles: ["admin", "validator", "user"] },
  { name: "Mobile view", path: "/mobile", roles: ["admin", "validator", "user"] },
];

export default function Sidebar({ route, onNavigate, role, onLogout }: SidebarProps) {

  return (
    <aside className="w-64 p-6 glass flex flex-col gap-6">
      <div className="p-4 glass text-center">
        <div className="text-lg font-bold tracking-widest">WQAM</div>
        <div className="text-xs text-gray-300">Water Quality Analytics</div>
      </div>

      <nav className="space-y-2 flex-1">
        {links.filter(l => l.roles.includes(role || "user")).map((l) => {
          const active = route === l.path;
          return (
            <button
              key={l.path}
              onClick={() => onNavigate(l.path)}
              className={`w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl transition ${active ? "bg-white/20" : "hover:bg-white/10"}`}
            >
              {l.name}
            </button>
          );
        })}
      </nav>

      <div>
        <div className="text-xs text-gray-400">Role</div>
        <div className="text-sm font-semibold mt-1">{(role || "guest").toUpperCase()}</div>
        <button onClick={onLogout} className="mt-3 w-full py-2 rounded-md bg-red-600 hover:bg-red-700">Logout</button>
      </div>
    </aside>
  );
}
