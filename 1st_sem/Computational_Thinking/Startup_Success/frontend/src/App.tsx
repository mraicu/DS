import { Routes, Route, Navigate } from "react-router-dom";
import { useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import DataOverview from "./pages/DataOverview";
import Prediction from "./pages/Prediction";
import Simulation from "./pages/Simulation";
import Login from "./pages/Login";
import Account from "./pages/Account";
import { AuthSession } from "./types/auth";

const App = () => {
  const [session, setSession] = useState<AuthSession | null>(() => {
    const stored = localStorage.getItem("startup-auth");
    if (!stored) return null;
    try {
      return JSON.parse(stored) as AuthSession;
    } catch {
      return null;
    }
  });

  const navItems = useMemo(() => {
    if (!session) {
      return [{ label: "Login", path: "/login" }];
    }
    return [
      { label: "Data Overview", path: "/" },
      { label: "Prediction", path: "/predict" },
      { label: "Simulation", path: "/simulation" },
      { label: "Account", path: "/account" },
    ];
  }, [session]);

  const handleLogout = () => {
    setSession(null);
    localStorage.removeItem("startup-auth");
  };

  const handleAuth = (payload: AuthSession) => {
    setSession(payload);
    localStorage.setItem("startup-auth", JSON.stringify(payload));
  };

  const RequireAuth = ({ children }: { children: JSX.Element }) => {
    if (!session) return <Navigate to="/login" replace />;
    return children;
  };

  return (
    <div className="app-shell">
      <Sidebar items={navItems} session={session} onLogout={handleLogout} />
      <main className="content-area">
        <Routes>
          <Route
            path="/"
            element={
              <RequireAuth>
                <DataOverview />
              </RequireAuth>
            }
          />
          <Route
            path="/predict"
            element={
              <RequireAuth>
                <Prediction />
              </RequireAuth>
            }
          />
          <Route
            path="/simulation"
            element={
              <RequireAuth>
                <Simulation />
              </RequireAuth>
            }
          />
          <Route
            path="/account"
            element={
              <RequireAuth>
                <Account
                  session={session as AuthSession}
                  onAuth={handleAuth}
                  onLogout={handleLogout}
                />
              </RequireAuth>
            }
          />
          <Route
            path="/login"
            element={<Login onAuth={handleAuth} session={session} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
