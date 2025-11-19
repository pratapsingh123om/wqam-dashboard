import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";

export default function App() {
  const [route, setRoute] = useState<string>(window.location.hash.replace("#","") || "/");
  window.onhashchange = () => setRoute(window.location.hash.replace("#","") || "/");

  const renderRoute = () => {
    switch(route) {
      case "/upload": return <Upload />;
      case "/alerts": return <Alerts />;
      case "/reports": return <Reports />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="h-screen app-bg text-gray-900 dark:text-gray-100">
      <div className="flex h-full">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="p-6 overflow-auto">{renderRoute()}</main>
        </div>
      </div>
    </div>
  );
}
