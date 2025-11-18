import React, { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Alerts from "./pages/Alerts";
import Upload from "./pages/Upload";
import Reports from "./pages/Reports";
import Login from "./pages/Login";
import NavBar from "./components/NavBar";
import Sidebar from "./components/Sidebar";
import DemoPanel from "./components/DemoPanel";
import "./index.css";

export default function App() {
  const [route, setRoute] = useState<string>("/");
  const [role, setRole] = useState<"user"|"validator"|"admin">("user");
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const navigate = (r:string) => { setRoute(r); window.scrollTo(0,0); };

  return (
    <div>
      <NavBar />
      <div className="container-app flex gap-6">
        <Sidebar onNavigate={navigate} role={role} />
        <main className="flex-1">
          <div className="flex justify-end gap-4 mb-4">
            <DemoPanel demoMode={demoMode} onToggle={() => setDemoMode(!demoMode)} role={role} setRole={setRole} />
          </div>

          {route === "/" && <Dashboard demoMode={demoMode} role={role} />}
          {route === "/alerts" && <Alerts />}
          {route === "/upload" && <Upload />}
          {route === "/reports" && <Reports />}
          {route === "/login" && <Login onLogin={(r)=>setRole(r)} />}
        </main>
      </div>
    </div>
  );
}
