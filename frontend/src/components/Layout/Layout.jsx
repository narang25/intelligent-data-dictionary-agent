import { NavLink, useNavigate } from "react-router-dom";
import { useConnection } from "../../context/ConnectionContext";
import { useTheme } from "../../context/ThemeContext";
import { useState, useEffect, useRef } from "react";
import { listAlerts, dismissAlert } from "../../services/api";

const DB_ICONS = { postgresql: "🐘", mysql: "🐬", snowflake: "❄️", mongodb: "🍃" };

const navItems = [
  { path: "/quick-start", label: "Quick Start", shortcut: "S",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> },
  { path: "/dashboard", label: "Dashboard", shortcut: "D",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg> },
  { path: "/tables", label: "Tables", shortcut: "T",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h18M3 12h18M3 18h18M9 6v12M15 6v12"/></svg> },
  { path: "/quality", label: "Quality", shortcut: "Q", hasBadge: true,
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg> },
  { path: "/chat", label: "Assistant", shortcut: "A",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg> },
  { path: "/export", label: "Export", shortcut: "E",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3M6 20h12a2 2 0 002-2V8l-5-5H6a2 2 0 00-2 2v13a2 2 0 002 2z"/></svg> },
  { path: "/lineage", label: "Lineage", shortcut: "L",
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> },
];

// Animated JARVIS Logo SVG
function JarvisLogo({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="logo-animated">
      <circle cx="12" cy="12" r="10" stroke="var(--accent)" strokeWidth="1.5" opacity="0.3"/>
      <circle cx="12" cy="12" r="6" stroke="var(--accent)" strokeWidth="1.5"/>
      <circle cx="12" cy="12" r="2" fill="var(--accent)"/>
      <line x1="12" y1="2" x2="12" y2="6" stroke="var(--accent)" strokeWidth="1.5"/>
      <line x1="12" y1="18" x2="12" y2="22" stroke="var(--accent)" strokeWidth="1.5"/>
      <line x1="2" y1="12" x2="6" y2="12" stroke="var(--accent)" strokeWidth="1.5"/>
      <line x1="18" y1="12" x2="22" y2="12" stroke="var(--accent)" strokeWidth="1.5"/>
    </svg>
  );
}

// Custom Connection Dropdown
function ConnectionDropdown({ connections, activeConnection, setActiveConnection }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (connections.length <= 1) return null;

  const activeIcon = DB_ICONS[activeConnection?.db_type] || "🐘";

  return (
    <div className="custom-dropdown" ref={ref}>
      <button type="button" className="custom-dropdown-trigger" onClick={() => setOpen(!open)}>
        <span>{activeIcon}</span>
        <span className="flex-1 text-left truncate">{activeConnection?.name || "Select..."}</span>
        <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" style={{ transform: open ? "rotate(180deg)" : "", transition: "transform 0.2s" }}>
          <path d="M6 9l6 6 6-6"/>
        </svg>
      </button>
      {open && (
        <div className="custom-dropdown-menu rise">
          {connections.map(c => (
            <div key={c.id}
              className={`custom-dropdown-item ${activeConnection?.id === c.id ? "active" : ""}`}
              onClick={() => { setActiveConnection(c); setOpen(false); }}>
              <span>{DB_ICONS[c.db_type] || "🐘"}</span>
              <span className="truncate">{c.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Layout({ children }) {
  const { activeConnection, connections, setActiveConnection } = useConnection();
  const { isDark, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAlerts = async () => {
      try { const data = await listAlerts(); setAlerts(data); } catch (e) { console.error(e); }
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = async (id) => {
    try { await dismissAlert(id); setAlerts(prev => prev.filter(a => a.id !== id)); } catch (e) { console.error(e); }
  };

  const alertCount = alerts.length;

  return (
    <div className="flex h-screen w-full" style={{ background: "var(--bg-base)" }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col transition-all duration-300 relative"
        style={{
          width: collapsed ? 60 : 220,
          minWidth: collapsed ? 60 : 220,
          background: "var(--bg-raised)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <div className="sidebar-glow"></div>

        {/* Top: Logo */}
        <div className="flex items-center justify-between px-4 h-14" style={{ borderBottom: "1px solid var(--border)" }}>
          {!collapsed && (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
                <JarvisLogo size={18} />
              </div>
              <div>
                <span className="text-sm font-bold" style={{ color: "var(--text-bright)" }}>JARVIS</span>
                <span className="text-[9px] ml-1.5 font-medium" style={{ color: "var(--text-muted)" }}>v2.0</span>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 rounded-lg flex items-center justify-center mx-auto" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
              <JarvisLogo size={16} />
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

        {/* Connection status */}
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
          {navItems.map(({ path, label, icon, shortcut, hasBadge }) => (
            <NavLink
              key={path} to={path}
              title={collapsed ? label : undefined}
              className="flex items-center rounded-lg transition-all duration-150 relative"
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
              {hasBadge && alertCount > 0 && <div className="nav-badge"></div>}
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
          {!collapsed && (
            <div className="mb-2">
              <ConnectionDropdown connections={connections} activeConnection={activeConnection} setActiveConnection={setActiveConnection} />
            </div>
          )}
          <div className="flex items-center gap-1.5" style={{ justifyContent: collapsed ? "center" : "flex-start" }}>
            <button onClick={toggleTheme} className="theme-toggle" title={isDark ? "Switch to light mode" : "Switch to dark mode"}>
              {isDark ? (
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
              ) : (
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
              )}
            </button>
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
        <div className="p-6 max-w-[1400px] mx-auto page-transition">{children}</div>
      </main>
    </div>
  );
}
