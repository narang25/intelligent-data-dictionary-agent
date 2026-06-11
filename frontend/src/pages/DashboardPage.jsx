import { useState, useEffect } from "react";
import { useConnection } from "../context/ConnectionContext";
import { getOverview, analyzeDatabase, listTables, triggerBatchDocs, getBatchDocsStatus } from "../services/api";

export default function DashboardPage() {
  const { activeConnection } = useConnection();
  const [overview, setOverview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [tables, setTables] = useState([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loading, setLoading] = useState(false);

  // Batch Docs State
  const [docsStatus, setDocsStatus] = useState(null);
  const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);

  useEffect(() => {
    if (activeConnection?.id) fetchData();
  }, [activeConnection?.id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ov, tb] = await Promise.all([
        getOverview(activeConnection.id),
        listTables(activeConnection.id).catch(() => ({ tables: [] })),
      ]);
      setOverview(ov);
      setTables(tb.tables || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const runAnalysis = async () => {
    setLoadingAnalysis(true);
    try { 
      setAnalysis(await analyzeDatabase(activeConnection.id, false, true)); 
    }
    catch (err) { console.error(err); }
    finally { setLoadingAnalysis(false); }
  };

  const handleGenerateDocs = async () => {
    try {
      setIsGeneratingDocs(true);
      await triggerBatchDocs(activeConnection.id);
      pollDocsStatus();
    } catch (err) {
      console.error(err);
      setIsGeneratingDocs(false);
    }
  };

  const pollDocsStatus = async () => {
    try {
      const status = await getBatchDocsStatus(activeConnection.id);
      setDocsStatus(status);
      
      // The API returns { total_tables, documented, remaining }
      // Polling continues if there are still tables remaining
      if (status.remaining > 0) {
        setTimeout(pollDocsStatus, 2000); 
      } else {
        setIsGeneratingDocs(false);
        fetchData(); 
      }
    } catch (err) {
      console.error(err);
      setIsGeneratingDocs(false);
    }
  };

  // ───── Welcome State (no connection) ─────
  if (!activeConnection) {
    return (
      <div className="flex flex-col items-center justify-center h-[85vh] text-center">
        <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-5" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
          <svg width="28" height="28" fill="none" stroke="var(--accent)" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/></svg>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-bright)" }}>JARVIS</h1>
        <p className="text-base mb-1" style={{ color: "var(--text-secondary)" }}>Intelligent Data Dictionary Agent</p>
        <p className="text-xs max-w-md mb-8" style={{ color: "var(--text-muted)" }}>
          Connect your database to unlock AI-powered schema analysis, automated documentation, and data quality scoring.
        </p>
        <a href="/connections" className="btn-accent text-sm">
          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          Get Started
        </a>
        <div className="grid grid-cols-3 gap-8 mt-14">
          {[
            { icon: "🛡️", title: "Read-Only Access", desc: "Zero mutations to your data" },
            { icon: "⚡", title: "AI Insights", desc: "Auto-generated documentation" },
            { icon: "📐", title: "Schema Intelligence", desc: "Relationships & patterns" },
          ].map(f => (
            <div key={f.title} className="text-center rise">
              <div className="text-xl mb-2">{f.icon}</div>
              <p className="text-xs font-semibold" style={{ color: "var(--text-bright)" }}>{f.title}</p>
              <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ───── Connected Dashboard ─────
  const metrics = [
    { label: "Tables", value: overview?.total_tables || 0, color: "var(--accent)", pct: Math.min((overview?.total_tables || 0) * 10, 100) },
    { label: "Columns", value: overview?.total_columns || 0, color: "var(--teal)", pct: Math.min((overview?.total_columns || 0) * 2, 100) },
    { label: "Rows", value: overview?.total_rows || 0, color: "var(--ice)", pct: 75 },
    { label: "Relationships", value: overview?.total_relationships || 0, color: "var(--coral)", pct: Math.min((overview?.total_relationships || 0) * 5, 100) },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>Database Overview</h1>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="tag" style={{ background: "var(--accent-glow)", color: "var(--accent)", fontSize: 12 }}>{activeConnection.name}</span>
            <span className="tag" style={{ background: "var(--teal-dim)", color: "var(--teal)", fontSize: 12 }}>PostgreSQL</span>
          </div>
        </div>
        <div className="flex gap-2">
          {(!docsStatus || (docsStatus.remaining === 0 && !isGeneratingDocs)) && (
            <button onClick={handleGenerateDocs} disabled={isGeneratingDocs} className="btn-ghost" title="Auto-document all tables using AI">
              {isGeneratingDocs ? <><div className="spinner"></div> Starting...</> : <><svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg> Generate Docs</>}
            </button>
          )}
          <button onClick={() => runAnalysis()} disabled={loadingAnalysis} className="btn-accent">
            {loadingAnalysis ? <><div className="spinner"></div> Analyzing...</> : <><svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Run AI Analysis</>}
          </button>
        </div>
      </div>

      {docsStatus && (docsStatus.remaining > 0 || isGeneratingDocs) && (
        <div className="card p-4 rise bg-teal-dim border-teal" style={{ borderColor: "rgba(45,212,168,0.3)" }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold" style={{ color: "var(--teal)" }}>
              🤖 Auto-Documenting Database...
            </span>
            <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
              {docsStatus.documented || 0} / {docsStatus.total_tables || overview?.total_tables || 0} Tables
            </span>
          </div>
          <div className="stat-bar" style={{ height: 4, background: "var(--bg-hover)" }}>
            <div className="stat-bar-fill" style={{ 
              width: `${docsStatus.total_tables ? ((docsStatus.documented || 0) / docsStatus.total_tables) * 100 : 0}%`, 
              background: "var(--teal)",
              transition: "width 0.5s ease"
            }}></div>
          </div>
        </div>
      )}

      {/* Metric Cards — horizontal bars instead of big numbers */}
      <div className="grid grid-cols-4 gap-3">
        {metrics.map((m, i) => (
          <div key={m.label} className={`card p-4 rise rise-${i}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{m.label}</span>
              <span className="text-xl font-bold mono" style={{ color: m.color }}>{typeof m.value === "number" ? m.value.toLocaleString() : m.value}</span>
            </div>
            <div className="stat-bar">
              <div className="stat-bar-fill" style={{ width: `${m.pct}%`, background: m.color }}></div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Analysis — Two-column card layout */}
      {analysis && (
        <div className="grid grid-cols-5 gap-3 rise">
          {/* Left 3 cols: Key Info items as horizontal rows */}
          <div className="col-span-3 card p-5 space-y-3">
            <h3 className="text-sm font-bold uppercase tracking-wider mb-3" style={{ color: "var(--accent)" }}>AI Analysis</h3>
            {[
              { label: "Purpose", value: analysis.business_purpose, color: "var(--coral)" },
              { label: "Domain", value: analysis.domain, color: "var(--teal)" },
              { label: "Model Type", value: analysis.model_type, color: "var(--ice)" },
            ].map(item => (
              <div key={item.label} className="flex gap-3 items-start">
                <span className="tag shrink-0 mt-0.5" style={{ background: `color-mix(in srgb, ${item.color} 12%, transparent)`, color: item.color }}>{item.label}</span>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{item.value || "—"}</p>
              </div>
            ))}
          </div>

          {/* Right 2 cols: Observations + Entity */}
          <div className="col-span-2 space-y-3">
            {analysis.architecture_observations?.length > 0 && (
              <div className="card p-4">
                <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>Observations</h4>
                <ul className="space-y-1.5">
                  {analysis.architecture_observations.map((o, i) => (
                    <li key={i} className="text-[11px] flex gap-2" style={{ color: "var(--text-secondary)" }}>
                      <span style={{ color: "var(--accent)" }}>›</span>{o}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.key_entity_groups?.length > 0 && (
              <div className="card p-4">
                <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>Entity Groups</h4>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.key_entity_groups.map((g, i) => (
                    <span key={i} className="tag" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>{g}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tables Overview — Clean minimal table */}
      {tables.length > 0 && (
        <div className="card overflow-hidden rise">
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
            <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Tables</h3>
            <a href="/tables" className="text-[11px] font-medium" style={{ color: "var(--accent)" }}>View All →</a>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: "var(--bg-surface)" }}>
                  {["Name", "Columns", "Rows"].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 font-semibold text-[10px] uppercase tracking-wider" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tables.slice(0, 8).map(t => (
                  <tr key={t.name} className="transition-colors" style={{ borderBottom: "1px solid var(--border)" }}
                    onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <td className="px-4 py-2.5 font-medium mono" style={{ color: "var(--text-bright)" }}>
                      {t.schema_name ? `${t.schema_name}.` : ""}{t.name}
                    </td>
                    <td className="px-4 py-2.5 mono" style={{ color: "var(--text-secondary)" }}>{t.column_count || 0}</td>
                    <td className="px-4 py-2.5 mono" style={{ color: "var(--text-secondary)" }}>{(t.row_count || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
