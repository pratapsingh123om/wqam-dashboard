
interface NavItem {
  name: string;
  path: string;
  icon: React.ReactElement;
}

interface SidebarProps {
  current: string;
  onNavigate: (path: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ current, onNavigate }) => {
  const links: NavItem[] = [
    { name: "Dashboard", path: "/", icon: <span>📊</span> },
    { name: "Uploads", path: "/uploads", icon: <span>📁</span> },
    { name: "Alerts", path: "/alerts", icon: <span>⚠️</span> },
    { name: "Reports", path: "/reports", icon: <span>📄</span> },
  ];

  return (
    <aside className="w-60 min-h-screen bg-[#111] text-white flex flex-col p-4 border-r border-neutral-800">
      <h1 className="text-lg font-bold mb-6 text-center">🚰 WQAM</h1>

      <nav className="flex flex-col gap-2">
        {links.map((item) => (
          <button
            key={item.path}
            onClick={() => onNavigate(item.path)}
            className={`flex gap-3 items-center px-4 py-3 rounded-xl transition
              ${current === item.path ? "bg-blue-600" : "hover:bg-neutral-800"}`}
          >
            {item.icon}
            <span>{item.name}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
