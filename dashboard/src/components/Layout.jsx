import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Package, Bell, Play, ChevronRight, LogOut
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { path: "/",         label: "Overview",   icon: LayoutDashboard },
  { path: "/products", label: "Products",   icon: Package },
  { path: "/alerts",   label: "Alerts",     icon: Bell },
  { path: "/pipeline", label: "Pipeline",   icon: Play },
];

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const { logout } = useAuth();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>

      {/* Sidebar */}
      <aside style={{
        width: 220, background: "#1e293b", color: "#94a3b8",
        padding: "24px 0", flexShrink: 0,
        display: "flex", flexDirection: "column",
      }}>
        <div style={{ padding: "0 20px 24px", borderBottom: "1px solid #334155" }}>
          <p style={{ color: "#fff", fontWeight: 700, fontSize: 16 }}>
            🤖 Repricer
          </p>
          <p style={{ fontSize: 12, marginTop: 2 }}>Agent Dashboard</p>
        </div>

        <nav style={{ padding: "16px 12px", flex: 1 }}>
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = pathname === path;
            return (
              <Link key={path} to={path} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px", borderRadius: 8, marginBottom: 4,
                background: active ? "#334155" : "transparent",
                color: active ? "#fff" : "#94a3b8",
                fontWeight: active ? 600 : 400,
                transition: "all 0.15s",
              }}>
                <Icon size={16} />
                {label}
                {active && <ChevronRight size={14} style={{ marginLeft: "auto" }} />}
              </Link>
            );
          })}
        </nav>

        {/* Logout button replaces the old static footer text */}
        <div style={{ padding: "16px 20px", borderTop: "1px solid #334155" }}>
          <button onClick={logout} style={{
            background: "transparent", color: "#94a3b8",
            display: "flex", alignItems: "center", gap: 8,
            width: "100%", padding: "8px 0", fontSize: 13,
          }}>
            <LogOut size={14} /> Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
        {children}
      </main>
    </div>
  );
}