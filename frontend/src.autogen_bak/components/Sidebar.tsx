
function IconHome(){ return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 10.5L12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V10.5z"/></svg>; }
function IconUpload(){ return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5-5 5 5"/><path d="M12 5v12"/></svg>; }
function IconBell(){ return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0 1 18 14V11a6 6 0 0 0-5-5.917V4a1 1 0 0 0-2 0v1.083A6 6 0 0 0 6 11v3c0 .538-.214 1.055-.595 1.595L4 17h11z"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>; }
function IconFile(){ return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>; }

export default function Sidebar({ onNavigate, role }: any) {
  const links = [
    { name: "Dashboard", path: "/", icon: IconHome },
    { name: "Uploads", path: "/upload", icon: IconUpload },
    { name: "Alerts", path: "/alerts", icon: IconBell },
    { name: "Reports", path: "/reports", icon: IconFile },
  ];
  return (
    <aside className="w-64 p-4">
      <div className="p-3 rounded-lg glass mb-4">
        <div className="text-sm font-semibold">WQAM</div>
        <div className="text-xs text-gray-500">Water Quality Analytics</div>
      </div>
      <nav className="space-y-2">
        {links.map(l => {
          const Icon = l.icon;
          return <button key={l.path} onClick={()=>onNavigate(l.path)} className="w-full text-left flex items-center gap-3 p-3 rounded-lg hover:bg-white/5"><Icon/> {l.name}</button>;
        })}
      </nav>
      <div className="mt-6 glass p-3">
        <div className="text-xs text-gray-400">Role</div>
        <div className="text-sm font-semibold mt-1">{role?.toUpperCase()}</div>
      </div>
    </aside>
  );
}
