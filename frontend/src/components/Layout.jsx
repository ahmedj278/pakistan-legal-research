import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { checkHealth } from "../api/client";

// Reuses the original App.jsx's backend-health-check logic (the
// first real frontend-backend wiring in this project) as a small
// persistent status badge in the nav, rather than dropping it now
// that the homepage becomes the actual Search page.
function BackendStatus() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    checkHealth()
      .then(() => setStatus("connected"))
      .catch(() => setStatus("unreachable"));
  }, []);

  const color = status === "connected" ? "#1a7f37" : status === "unreachable" ? "#c62828" : "#666";

  return (
    <span className="backend-status">
      Backend: <strong style={{ color }}>{status}</strong>
    </span>
  );
}

function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <span className="app-title">Pakistan Legal Research</span>
          <nav className="app-nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
              Search
            </NavLink>
            <NavLink to="/research" className={({ isActive }) => (isActive ? "active" : "")}>
              Research
            </NavLink>
          </nav>
          <BackendStatus />
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        AI-generated research aid — not legal advice.
      </footer>
    </div>
  );
}

export default Layout;
