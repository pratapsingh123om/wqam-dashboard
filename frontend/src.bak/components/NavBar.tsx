import ThemeToggle from "./ThemeToggle";

export default function NavBar() {
  return (
    <nav className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">WQAM Dashboard</h1>
      <ThemeToggle />
    </nav>
  );
}
