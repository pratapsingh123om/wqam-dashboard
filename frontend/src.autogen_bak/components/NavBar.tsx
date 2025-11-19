import ThemeToggle from "./ThemeToggle";

export default function NavBar(){
  return (
    <header className="flex items-center justify-between py-4 px-6 glass">
      <div className="flex items-center gap-4">
        <div className="font-bold text-lg">WQAM Dashboard</div>
        <div className="text-sm text-gray-500 hidden md:block">Water Quality Analytics Platform</div>
      </div>
      <div className="flex items-center gap-3">
        <input placeholder="Search metrics..." className="hidden md:block bg-transparent border rounded-full px-3 py-1 outline-none" />
        <ThemeToggle />
      </div>
    </header>
  );
}
