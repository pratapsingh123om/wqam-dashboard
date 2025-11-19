import ThemeToggle from "./ThemeToggle";

export default function NavBar(){
  return (
    <header className="flex items-center justify-between py-4 px-6 glass">
      <div className="flex items-center gap-4">
        <div className="font-bold text-xl">WQAM Dashboard</div>
        <div className="hidden md:block text-sm text-gray-600">Water Quality Analytics & Monitoring</div>
      </div>
      <div className="flex items-center gap-3">
        <input placeholder="Search metrics, uploads..." className="hidden md:block bg-transparent border rounded-full px-3 py-1 outline-none" />
        <ThemeToggle />
      </div>
    </header>
  );
}
