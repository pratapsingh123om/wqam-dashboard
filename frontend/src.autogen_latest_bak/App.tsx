import Sidebar from "./layout/Sidebar";
import Dashboard from "./pages/Dashboard";
import Uploads from "./pages/Uploads";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import Login from "./pages/Login";

export default function App() {
  const [route, setRoute] = useState("/login");

  if (route === "/login") return <Login onLogin={() => setRoute("/")} />;

  return (
    <div className="flex h-screen">
      <Sidebar route={route} onNavigate={setRoute} />

      <div className="flex-1 p-8 overflow-y-auto">
        {route === "/" && <Dashboard />}
        {route === "/uploads" && <Uploads />}
        {route === "/alerts" && <Alerts />}
        {route === "/reports" && <Reports />}
      </div>
    </div>
  );
}
