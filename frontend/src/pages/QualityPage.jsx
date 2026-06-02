import { useState, useEffect } from "react";
import { useConnection } from "../context/ConnectionContext";
import { getQualityScores, analyzeQuality } from "../services/api";

export default function QualityPage() {
  const { activeConnection } = useConnection();
  const [quality, setQuality] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [expandedTable, setExpandedTable] = useState(null);

  useEffect(() => {
    if (activeConnection?.id) fetchQuality();
  }, [activeConnection?.id]);

  const fetchQuality = async () => {
    try { setQuality(await getQualityScores(activeConnection.id)); }
    catch (err) { console.error(err); }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    try { setQuality(await analyzeQuality(activeConnection.id)); }
    catch (err) { console.error(err); }
    finally { setAnalyzing(false); }
  };

  if (!activeConnection) {
    return <div className="flex items-center justify-center h-[80vh]" style={{ color: "var(--text-muted)" }}>Connect a database to view data quality.</div>;
  }

  const score = quality?.overall_score || 0;
  const scoreColor = score >= 80 ? "var(--teal)" : score >= 60 ? "var(--accent)" : "var(--coral)";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>Data Quality</h1>
          <p className="text-sm mt-1 mono" style={{ color: "var(--text-muted)" }}>{quality?.tables?.length || 0} tables analyzed</p>
        </div>
        <button onClick={runAnalysis} disabled={analyzing} className="btn-accent">
          {analyzing ? <><div className="spinner"></div> Scanning...</> : "Run Analysis"}
        </button>
      </div>

      {/* Top-level score — Horizontal bar instead of donut */}
      {quality && (
        <div className="card p-5 rise">
          <div className="flex items-center gap-6">
            {/* Big score number */}
            <div className="text-center shrink-0" style={{ minWidth: 80 }}>
              <p className="text-5xl font-bold mono" style={{ color: scoreColor }}>{score}</p>
              <p className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: "var(--text-muted)" }}>Overall</p>
            </div>
            {/* Full-width bar */}
            <div className="flex-1 space-y-2">
              <div className="stat-bar" style={{ height: 10 }}>
                <div className="stat-bar-fill" style={{ width: `${score}%`, background: scoreColor, height: "100%" }}></div>
              </div>
              <div className="flex justify-between text-[10px] mono" style={{ color: "var(--text-muted)" }}>
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>
          </div>

          {/* Summary metrics row */}
          <div className="grid grid-cols-4 gap-3 mt-5 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
            {[
              { label: "Tables", value: quality.tables?.length || 0 },
              { label: "Issues", value: quality.tables?.filter(t => (t.overall_score || 0) < 80).length || 0 },
              { label: "Best Score", value: Math.max(...(quality.tables || []).map(t => t.overall_score || 0), 0) },
              { label: "Worst Score", value: Math.min(...(quality.tables || []).map(t => t.overall_score || 100), 100) },
            ].map(m => (
              <div key={m.label} className="text-center">
                <p className="text-base font-bold mono" style={{ color: "var(--text-bright)" }}>{m.value}</p>
                <p className="text-[9px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-table list */}
      {quality?.tables?.length > 0 ? (
        <div className="space-y-1.5">
          {quality.tables.map((t, idx) => {
            const ts = t.overall_score || 0;
            const tc = ts >= 80 ? "var(--teal)" : ts >= 60 ? "var(--accent)" : "var(--coral)";
            return (
              <div key={t.table_name} className={`card overflow-hidden rise rise-${idx % 5}`}>
                <button onClick={() => setExpandedTable(expandedTable === t.table_name ? null : t.table_name)}
                  className="w-full px-4 py-3 flex items-center justify-between transition-all"
                  style={{ borderBottom: expandedTable === t.table_name ? "1px solid var(--border)" : "none" }}>
                  <div className="flex items-center gap-3">
                    {/* Score badge */}
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold mono" style={{ background: `color-mix(in srgb, ${tc} 12%, transparent)`, color: tc }}>{ts}</div>
                    <span className="text-sm font-semibold mono" style={{ color: "var(--text-bright)" }}>{t.table_name}</span>
                  </div>
                  <div className="flex items-center gap-5">
                    {/* Mini stat bars */}
                    <div className="flex items-center gap-2 text-[10px]">
                      <span style={{ color: "var(--text-muted)" }}>Completeness</span>
                      <div className="stat-bar" style={{ width: 50, height: 4 }}>
                        <div className="stat-bar-fill" style={{ width: `${t.completeness || 100}%`, background: "var(--teal)", height: "100%" }}></div>
                      </div>
                      <span className="mono" style={{ color: "var(--teal)" }}>{t.completeness || 100}%</span>
                    </div>
                    <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" style={{ color: "var(--text-muted)", transform: expandedTable === t.table_name ? "rotate(180deg)" : "", transition: "transform 0.2s" }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/>
                    </svg>
                  </div>
                </button>

                {expandedTable === t.table_name && (
                  <div className="px-4 py-3 rise">
                    {/* Quality bars */}
                    <div className="grid grid-cols-4 gap-3 mb-4">
                      {[
                        { label: "Score", value: ts, color: tc },
                        { label: "Completeness", value: t.completeness || 100, color: "var(--teal)" },
                        { label: "Uniqueness", value: t.uniqueness || 100, color: "var(--ice)" },
                        { label: "Duplication", value: 0, color: "var(--accent)" },
                      ].map(m => (
                        <div key={m.label}>
                          <div className="flex items-center justify-between text-[10px] mb-1">
                            <span style={{ color: "var(--text-muted)" }}>{m.label}</span>
                            <span className="mono font-semibold" style={{ color: m.color }}>{m.value}%</span>
                          </div>
                          <div className="stat-bar" style={{ height: 4 }}>
                            <div className="stat-bar-fill" style={{ width: `${m.value}%`, background: m.color, height: "100%" }}></div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Column table */}
                    {t.details && Array.isArray(t.details) && (
                      <table className="w-full text-[11px]">
                        <thead>
                          <tr style={{ background: "var(--bg-surface)" }}>
                            {["Column", "Type", "Nulls", "Uniqueness", "Stats"].map(h => (
                              <th key={h} className="text-left px-3 py-2 text-[9px] font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {t.details.map(col => (
                            <tr key={col.column} style={{ borderBottom: "1px solid var(--border)" }}>
                              <td className="px-3 py-1.5 mono font-medium" style={{ color: "var(--text-bright)" }}>{col.column}</td>
                              <td className="px-3 py-1.5 mono" style={{ color: "var(--teal)", fontSize: 10 }}>{col.data_type || "—"}</td>
                              <td className="px-3 py-1.5">
                                <div className="flex items-center gap-1.5">
                                  <div className="stat-bar" style={{ width: 40, height: 3 }}>
                                    <div className="stat-bar-fill" style={{ width: `${100 - (col.completeness || 100)}%`, background: col.null_count > 0 ? "var(--coral)" : "var(--bg-hover)", height: "100%" }}></div>
                                  </div>
                                  <span className="mono" style={{ color: "var(--text-muted)", fontSize: 10 }}>{col.null_count || 0}</span>
                                </div>
                              </td>
                              <td className="px-3 py-1.5 mono" style={{ color: (col.uniqueness || 100) >= 80 ? "var(--teal)" : "var(--accent)", fontSize: 10 }}>{col.uniqueness || 100}%</td>
                              <td className="px-3 py-1.5 mono" style={{ color: "var(--text-muted)", fontSize: 10 }}>{col.min !== undefined ? `${col.min} – ${col.max}` : "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : !analyzing && (
        <div className="card p-12 text-center">
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>No quality data. Click "Run Analysis" to scan your tables.</p>
        </div>
      )}
    </div>
  );
}
