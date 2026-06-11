import { useState } from "react";
import { useConnection } from "../context/ConnectionContext";
import { createConnection, deleteConnection, testConnection, syncConnection } from "../services/api";

const DB_TYPES = [
  { value: "postgresql", label: "PostgreSQL", icon: "🐘", color: "var(--accent)" },
  { value: "mysql", label: "MySQL", icon: "🐬", color: "var(--teal)" },
  { value: "snowflake", label: "Snowflake", icon: "❄️", color: "var(--ice)" },
  { value: "mongodb", label: "MongoDB", icon: "🍃", color: "var(--teal)" },
];

const DEFAULT_PORTS = { postgresql: 5432, mysql: 3306, snowflake: 443, mongodb: 27017 };

function getFieldsForType(dbType) {
  const common = [{ name: "name", label: "Connection Name", placeholder: "Production DB" }];

  if (dbType === "postgresql" || dbType === "mysql") {
    return [...common,
      { name: "host", label: "Host", placeholder: "db.example.com" },
      { name: "port", label: "Port", placeholder: String(DEFAULT_PORTS[dbType]), type: "number" },
      { name: "database", label: "Database", placeholder: "mydb" },
      { name: "username", label: "Username", placeholder: dbType === "mysql" ? "root" : "postgres" },
      { name: "password", label: "Password", placeholder: "••••••••", type: "password" },
    ];
  }

  if (dbType === "snowflake") {
    return [...common,
      { name: "account", label: "Account Identifier", placeholder: "abc12345.us-east-1" },
      { name: "database", label: "Database", placeholder: "MY_DB" },
      { name: "warehouse", label: "Warehouse", placeholder: "COMPUTE_WH" },
      { name: "role", label: "Role", placeholder: "ACCOUNTADMIN" },
      { name: "username", label: "Username", placeholder: "my_user" },
      { name: "password", label: "Password", placeholder: "••••••••", type: "password" },
    ];
  }

  if (dbType === "mongodb") {
    return [...common,
      { name: "host", label: "Host", placeholder: "mongodb.example.com" },
      { name: "port", label: "Port", placeholder: "27017", type: "number" },
      { name: "database", label: "Database", placeholder: "mydb" },
      { name: "username", label: "Username", placeholder: "admin" },
      { name: "password", label: "Password", placeholder: "••••••••", type: "password" },
      { name: "connection_string", label: "Connection String (Optional)", placeholder: "mongodb+srv://..." },
    ];
  }

  return common;
}

export default function ConnectionsPage() {
  const { connections, refreshConnections, setActiveConnection } = useConnection();
  const [form, setForm] = useState({
    name: "", host: "", port: 5432, database: "", username: "", password: "",
    db_type: "postgresql", account: "", warehouse: "", role: "", connection_string: "",
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [creating, setCreating] = useState(false);
  const [syncing, setSyncing] = useState({});
  const [error, setError] = useState("");

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleDbTypeChange = (newType) => {
    setForm({
      ...form,
      db_type: newType,
      port: DEFAULT_PORTS[newType] || 0,
      host: "", username: "", password: "", database: "",
      account: "", warehouse: "", role: "", connection_string: "",
    });
    setTestResult(null);
    setError("");
  };

  const handleTest = async () => {
    setTesting(true); setTestResult(null);
    try { setTestResult(await testConnection(form)); }
    catch (err) { setTestResult({ status: "error", detail: err.message }); }
    finally { setTesting(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault(); setCreating(true); setError("");
    try {
      const conn = await createConnection(form);
      await refreshConnections();
      setActiveConnection(conn);
      setForm({
        name: "", host: "", port: DEFAULT_PORTS[form.db_type], database: "", username: "", password: "",
        db_type: form.db_type, account: "", warehouse: "", role: "", connection_string: "",
      });
      setTestResult(null);
    } catch (err) { setError(err.message); }
    finally { setCreating(false); }
  };

  const handleSync = async (id) => {
    setSyncing(s => ({ ...s, [id]: true }));
    try { await syncConnection(id); await refreshConnections(); }
    catch (err) { alert("Sync failed: " + err.message); }
    finally { setSyncing(s => ({ ...s, [id]: false })); }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this connection?")) return;
    try { await deleteConnection(id); await refreshConnections(); }
    catch (err) { alert("Delete failed: " + err.message); }
  };

  const fields = getFieldsForType(form.db_type);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>Connections</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Add and manage database connections</p>
      </div>

      {/* New Connection Form */}
      <div className="card p-5 rise">
        <h2 className="text-sm font-bold uppercase tracking-wider mb-4" style={{ color: "var(--accent)" }}>New Connection</h2>

        {/* Database Type Selector */}
        <div className="mb-5">
          <label className="block text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>Database Type</label>
          <div className="grid grid-cols-4 gap-3">
            {DB_TYPES.map(t => (
              <button key={t.value} type="button" onClick={() => handleDbTypeChange(t.value)}
                className={`radio-card ${form.db_type === t.value ? 'selected' : ''}`}>
                <div className="check-icon">
                  <svg width="10" height="10" fill="none" stroke="#0d0d0f" strokeWidth="3" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
                <span className="text-2xl">{t.icon}</span>
                <span className="text-[11px] font-semibold" style={{ color: form.db_type === t.value ? "var(--accent)" : "var(--text-secondary)" }}>{t.label}</span>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleCreate} className="space-y-3">
          {form.db_type === "snowflake" ? (
            <div className="card p-8 flex flex-col items-center justify-center text-center rise" style={{ background: "var(--bg-raised)", border: "1px dashed var(--border-active)" }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ background: "var(--ice-dim)", border: "1px solid rgba(96, 165, 250, 0.3)" }}>
                <span className="text-2xl">❄️</span>
              </div>
              <h3 className="text-base font-bold mb-1" style={{ color: "var(--text-bright)" }}>Snowflake Support Coming Soon</h3>
              <p className="text-xs max-w-sm" style={{ color: "var(--text-muted)" }}>We are currently building native integration with Snowflake data warehouses. Stay tuned for updates!</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                {fields.map(({ name, label, placeholder, type, multiline }) => (
                  <div key={name} className={multiline ? "col-span-2" : ""}>
                    <label className="block text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: "var(--text-muted)" }}>{label}</label>
                    {multiline ? (
                      <textarea name={name} value={form[name]} onChange={handleChange} placeholder={placeholder} rows={4}
                        className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none transition-all mono resize-none"
                        style={{ background: "var(--bg-surface)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
                        onFocus={e => e.target.style.borderColor = "var(--border-active)"} onBlur={e => e.target.style.borderColor = "var(--border)"} />
                    ) : (
                      <input name={name} type={type || "text"} value={form[name]} onChange={handleChange} placeholder={placeholder}
                        required={name === "name" || name === "database"}
                        className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none transition-all mono"
                        style={{ background: "var(--bg-surface)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
                        onFocus={e => e.target.style.borderColor = "var(--border-active)"} onBlur={e => e.target.style.borderColor = "var(--border)"} />
                    )}
                  </div>
                ))}
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={handleTest} disabled={testing} className="btn-ghost">
                  {testing ? <><div className="spinner"></div> Testing...</> : "Test Connection"}
                </button>
                <button type="submit" disabled={creating} className="btn-accent">
                  {creating ? <><div className="spinner"></div> Creating...</> : "Create Connection"}
                </button>
              </div>
            </>
          )}

          {testResult && (
            <div className="p-3 rounded-lg text-xs rise mono"
              style={testResult.status === "ok"
                ? { background: "var(--teal-dim)", border: "1px solid rgba(45,212,168,0.2)", color: "var(--teal)" }
                : { background: "var(--coral-dim)", border: "1px solid rgba(232,105,90,0.2)", color: "var(--coral)" }}>
              {testResult.status === "ok" ? `✓ Connected · ${testResult.version}` : `✗ ${testResult.detail}`}
            </div>
          )}
          {error && (
            <div className="p-3 rounded-lg text-xs rise" style={{ background: "var(--coral-dim)", border: "1px solid rgba(232,105,90,0.2)", color: "var(--coral)" }}>{error}</div>
          )}
        </form>
      </div>

      {/* Saved Connections */}
      {connections.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Saved</h2>
          {connections.map(c => {
            const dbInfo = DB_TYPES.find(t => t.value === c.db_type) || DB_TYPES[0];
            // Sync freshness indicator
            const syncAge = c.last_synced ? Math.round((Date.now() - new Date(c.last_synced).getTime()) / 60000) : null;
            const syncColor = syncAge === null ? "var(--text-muted)" : syncAge < 60 ? "var(--teal)" : syncAge < 1440 ? "var(--accent)" : "var(--coral)";
            const syncLabel = syncAge === null ? "Never synced" : syncAge < 1 ? "Just now" : syncAge < 60 ? `${syncAge}m ago` : syncAge < 1440 ? `${Math.round(syncAge / 60)}h ago` : `${Math.round(syncAge / 1440)}d ago`;
            return (
              <div key={c.id} className="card px-4 py-3 flex items-center justify-between rise">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                    {dbInfo.icon}
                  </div>
                  <div>
                    <p className="text-xs font-semibold" style={{ color: "var(--text-bright)" }}>{c.name}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded" style={{ background: "var(--bg-hover)", color: dbInfo.color }}>{dbInfo.label}</span>
                      <span className="text-[10px] mono" style={{ color: "var(--text-muted)" }}>
                        {c.db_type === "mongodb" ? (c.host || c.database) : `${c.host}${c.port ? ':' + c.port : ''}/${c.database}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: syncColor }}></div>
                      <span className="text-[9px]" style={{ color: syncColor }}>{syncLabel}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  <button onClick={() => handleSync(c.id)} disabled={syncing[c.id]} className="btn-ghost" style={{ padding: "4px 10px", fontSize: 10 }}>
                    {syncing[c.id] ? "Syncing..." : "Sync"}
                  </button>
                  <button onClick={() => setActiveConnection(c)} className="btn-ghost" style={{ padding: "4px 10px", fontSize: 10, borderColor: "rgba(45,212,168,0.2)", color: "var(--teal)" }}>Use</button>
                  <button onClick={() => handleDelete(c.id)} className="btn-ghost" style={{ padding: "4px 10px", fontSize: 10, borderColor: "rgba(232,105,90,0.15)", color: "var(--coral)" }}>✕</button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
