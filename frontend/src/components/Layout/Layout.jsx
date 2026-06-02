import { NavLink, useNavigate } from "react-router-dom";
import { useConnection } from "../../context/ConnectionContext";
import { useTheme } from "../../context/ThemeContext";
import { useState, useEffect } from "react";
import { listAlerts, dismissAlert } from "../../services/api";

const navItems = [
  { path: "/dashboard", label: "Dashboard", shortcut: "D",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg> },
  { path: "/tables", label: "Tables", shortcut: "T",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h18M3 12h18M3 18h18M9 6v12M15 6v12"/></svg> },
  { path: "/quality", label: "Quality", shortcut: "Q",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg> },
  { path: "/chat", label: "Assistant", shortcut: "A",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg> },
  { path: "/export", label: "Export", shortcut: "E",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3M6 20h12a2 2 0 002-2V8l-5-5H6a2 2 0 00-2 2v13a2 2 0 002 2z"/></svg> },
  { path: "/lineage", label: "Lineage", shortcut: "L",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> },
];

export default function Layout({ children }) {
  const { activeConnection, connections, setActiveConnection } = useConnection();
  const { isDark, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAlerts = async () => {
      try { const data = await listAlerts(); setAlerts(data); } catch (e) {}
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = async (id) => {
    try { await dismissAlert(id); setAlerts(prev => prev.filter(a => a.id !== id)); } catch (e) {}
  };

  return (
    <div className="flex h-screen w-full" style={{ background: "var(--bg-base)" }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col transition-all duration-300"
        style={{
          width: collapsed ? 60 : 220,
          minWidth: collapsed ? 60 : 220,
          background: "var(--bg-raised)",
          borderRight: "1px solid var(--border)",
        }}
      >
        {/* Top: Logo + collapse */}
        <div className="flex items-center justify-between px-4 h-14" style={{ borderBottom: "1px solid var(--border)" }}>
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md flex items-center justify-center" style={{ background: "var(--accent)" }}>
                <span className="text-xs font-bold" style={{ color: "#0d0d0f" }}>J</span>
              </div>
              <div>
                <span className="text-sm font-bold" style={{ color: "var(--text-bright)" }}>JARVIS</span>
                <span className="text-[9px] ml-1.5 font-medium" style={{ color: "var(--text-muted)" }}>v2.0</span>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="w-7 h-7 rounded-md flex items-center justify-center mx-auto" style={{ background: "var(--accent)" }}>
              <span className="text-xs font-bold" style={{ color: "#0d0d0f" }}>J</span>
            </div>
          )}
          {!collapsed && (
            <button onClick={() => setCollapsed(true)} className="opacity-40 hover:opacity-100 transition-opacity" style={{ color: "var(--text-secondary)" }}>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M11 19l-7-7 7-7M18 19l-7-7 7-7"/></svg>
            </button>
          )}
        </div>

        {collapsed && (
          <button onClick={() => setCollapsed(false)} className="mx-auto mt-3 opacity-40 hover:opacity-100 transition-opacity" style={{ color: "var(--text-secondary)" }}>
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M13 5l7 7-7 7M6 5l7 7-7 7"/></svg>
          </button>
        )}

        {/* Connection Selector */}
        {!collapsed && activeConnection && (
          <div className="mx-3 mt-3 px-3 py-2 rounded-lg" style={{ background: "var(--teal-dim)", border: "1px solid rgba(45,212,168,0.15)" }}>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--teal)", boxShadow: "0 0 6px var(--teal)" }}></div>
              <span className="text-[10px] font-semibold" style={{ color: "var(--teal)" }}>CONNECTED</span>
            </div>
            <p className="text-[11px] mt-1 truncate" style={{ color: "var(--text-secondary)" }}>{activeConnection.name}</p>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 mt-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ path, label, icon, shortcut }) => (
            <NavLink
              key={path} to={path}
              title={collapsed ? label : undefined}
              className="flex items-center rounded-lg transition-all duration-150"
              style={({ isActive }) => ({
                padding: collapsed ? "10px" : "8px 10px",
                justifyContent: collapsed ? "center" : "flex-start",
                gap: "10px",
                background: isActive ? "var(--accent-glow)" : "transparent",
                color: isActive ? "var(--accent)" : "var(--text-muted)",
                borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
              })}
            >
              {icon}
              {!collapsed && <span className="text-[13px] font-medium flex-1">{label}</span>}
              {!collapsed && <span className="text-[9px] px-1.5 py-0.5 rounded mono" style={{ background: "var(--bg-hover)", color: "var(--text-muted)" }}>{shortcut}</span>}
            </NavLink>
          ))}

          <hr className="divider my-3" />

          <NavLink
            to="/connections"
            className="flex items-center rounded-lg transition-all duration-150"
            style={({ isActive }) => ({
              padding: collapsed ? "10px" : "8px 10px",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: "10px",
              background: isActive ? "var(--accent-glow)" : "transparent",
              color: isActive ? "var(--accent)" : "var(--text-muted)",
              borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
            })}
            title={collapsed ? "Connections" : undefined}
          >
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4M4 12c0 2.21 3.582 4 8 4s8-1.79 8-4"/></svg>
            {!collapsed && <span className="text-[13px] font-medium flex-1">Connections</span>}
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="px-2 pb-3 pt-2" style={{ borderTop: "1px solid var(--border)" }}>
          {!collapsed && connections.length > 1 && (
            <select
              className="w-full text-[12px] rounded-lg px-2.5 py-2 mb-2 border-none focus:outline-none mono"
              style={{ background: "var(--bg-surface)", color: "var(--text-secondary)" }}
              value={activeConnection?.id || ""}
              onChange={(e) => { const c = connections.find(c => c.id === Number(e.target.value)); if (c) setActiveConnection(c); }}
            >
              {connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}
          <div className="flex items-center gap-1.5" style={{ justifyContent: collapsed ? "center" : "flex-start" }}>
            {/* Theme toggle */}
            <button onClick={toggleTheme} className="theme-toggle" title={isDark ? "Switch to light mode" : "Switch to dark mode"}>
              {isDark ? (
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
              ) : (
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
              )}
            </button>
            {/* Sign out */}
            <button onClick={() => { localStorage.removeItem("token"); navigate("/login"); }}
              className="flex items-center gap-2 flex-1 rounded-lg transition-all duration-150"
              style={{ padding: "8px 10px", justifyContent: collapsed ? "center" : "flex-start", color: "var(--text-muted)" }}
              onMouseEnter={e => e.currentTarget.style.color = "var(--coral)"}
              onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
              {!collapsed && <span className="text-[13px]">Sign out</span>}
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto" style={{ background: "var(--bg-base)" }}>
        {/* Alert banner */}
        {alerts.length > 0 && (
          <div className="px-6 pt-4 space-y-2">
            {alerts.slice(0, 3).map(alert => (
              <div key={alert.id} className="flex items-center justify-between px-4 py-2.5 rounded-xl text-sm"
                style={{
                  background: alert.severity === 'critical' ? 'var(--coral-dim)' : 'rgba(245,158,11,0.1)',
                  border: `1px solid ${alert.severity === 'critical' ? 'rgba(232,105,90,0.3)' : 'rgba(245,158,11,0.2)'}`,
                  color: alert.severity === 'critical' ? 'var(--coral)' : '#f59e0b',
                }}>
                <span>⚠️ <strong>{alert.table_name}.{alert.column_name}:</strong> {alert.message}</span>
                <button onClick={() => handleDismiss(alert.id)} className="text-xs px-2 py-0.5 rounded"
                  style={{ background: 'var(--bg-hover)', color: 'var(--text-muted)' }}>Dismiss</button>
              </div>
            ))}
          </div>
        )}
        <div className="p-6 max-w-[1400px] mx-auto">{children}</div>
      </main>
    </div>
  );
}
