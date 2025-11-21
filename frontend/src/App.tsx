import {
  Routes,
  Route,
  useNavigate,
  Navigate,
  Outlet,
} from "react-router-dom";
import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import RoleLoginPage from "./pages/RoleLoginPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import DashboardHeader from "./components/DashboardHeader"; // Import the new header
import { setAuthToken } from "./services/api";
import {
  login as loginRequest,
  register as registerRequest,
} from "./services/auth";


export default function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );
  const [role, setRole] = useState<string | null>(localStorage.getItem("role"));
  // dashboardData, reports and other states will be managed within Dashboard.tsx
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      // No need to load dashboardData or reports here, Dashboard component will handle it
    }
  }, [token]);

  async function handleLogin(credentials: {
    username: string;
    password: string;
  }) {
    try {
      setIsLoggingIn(true);
      setLoginError(null);
      const result = await loginRequest(credentials.username, credentials.password);
      setToken(result.access_token);
      setRole(result.role);
      localStorage.setItem("token", result.access_token);
      localStorage.setItem("role", result.role);
      navigate("/"); // Redirect to dashboard after login, regardless of role
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to login";
      setLoginError(message);
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function handleRegister(credentials: {
    username: string;
    password: string;
    role: string;
  }) {
    try {
      setIsRegistering(true);
      setRegisterError(null);
      await registerRequest(
        credentials.username,
        credentials.password,
        credentials.role
      );
      alert("Registration successful! Please wait for admin approval to log in.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to register";
      setRegisterError(message);
    } finally {
      setIsRegistering(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setRole(null);
    setAuthToken(null);
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    navigate("/login");
  }

  // Placeholder for modelPath from gui.html (will be static for this demo)
  const modelPath = 'file:///C:/Users/gsr33/wqam-dashboard/data/row/model.pkl';
  const handleDownloadSampleReport = () => {
    // Implement download logic here (mock for now)
    alert('Downloading sample report (mock)...');
  };

  const ProtectedRoute = () => {
    if (!token) {
      return <Navigate to="/login" />;
    }
    return <Outlet />;
  };

  const AdminRoute = () => {
    if (!token || role !== "admin") {
      return <Navigate to="/admin/login" />;
    }
    return <Outlet />;
  };

  return (
    <>
      <DashboardHeader modelPath={modelPath} onDownloadSampleReport={handleDownloadSampleReport} />
      <div className="app"> {/* This is the .app from gui.html */}
        <Routes>
          <Route
            path="/login"
            element={
              <RoleLoginPage
                onLogin={handleLogin}
                loading={isLoggingIn}
                loginError={loginError}
                onRegister={handleRegister}
                registerLoading={isRegistering}
                registerError={registerError}
              />
            }
          />
          <Route
            path="/admin/login"
            element={
              <AdminLoginPage
                onLogin={handleLogin}
                loading={isLoggingIn}
                error={loginError}
              />
            }
          />

          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Dashboard role={role} onLogout={handleLogout} />} />
          </Route>

          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<Dashboard role={role} onLogout={handleLogout} />} /> {/* Admin route to main dashboard */}
          </Route>
        </Routes>
      </div>
      <footer style={{ padding: '14px 22px', color: 'var(--muted)', textAlign: 'center' }}>
        WQAM Dashboard — demo UI — replace endpoints with your backend/model & wire auth.
      </footer>
    </>
  );
}