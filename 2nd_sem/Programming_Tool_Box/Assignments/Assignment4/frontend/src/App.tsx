import { Navigate, Route, Routes } from "react-router-dom";
import { useMemo, useState } from "react";

import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";

type Session = {
  token: string;
  username: string;
  email: string;
};

const SESSION_KEY = "happiness_session";

function loadSession(): Session | null {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as Session;
  } catch {
    localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export default function App() {
  const [session, setSession] = useState<Session | null>(() => loadSession());

  const authContext = useMemo(
    () => ({
      session,
      onAuth: (next: Session) => {
        localStorage.setItem(SESSION_KEY, JSON.stringify(next));
        setSession(next);
      },
      onLogout: () => {
        localStorage.removeItem(SESSION_KEY);
        setSession(null);
      },
    }),
    [session],
  );

  return (
    <Routes>
      <Route
        path="/"
        element={session ? <Navigate to="/dashboard" replace /> : <AuthPage onAuth={authContext.onAuth} />}
      />
      <Route
        path="/dashboard"
        element={
          session ? (
            <DashboardPage session={session} onLogout={authContext.onLogout} />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
