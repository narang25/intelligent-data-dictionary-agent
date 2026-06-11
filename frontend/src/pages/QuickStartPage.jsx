import { useState, useEffect, useCallback } from "react";
import { useConnection } from "../context/ConnectionContext";
import { getOverview, analyzeDatabase, sendMessageToAPI, getQualityScores, listAlerts, createExport, listTables, previewExport } from "../services/api";
import { useNavigate } from "react-router-dom";
import { SkeletonGrid, SkeletonCard, SkeletonLine } from "../components/UI/Skeleton";

export default function QuickStartPage() {
  const { activeConnection } = useConnection();
  const [overview, setOverview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [healthScore, setHealthScore] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [topTables, setTopTables] = useState([]);
  const [schemaDist, setSchemaDist] = useState([]);
  const [generatingDocs, setGeneratingDocs] = useState(false);
  const [exporting, setExporting] = useState(false);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setAnalysis(null);
    setAnswers({});
    try {
      const [overviewData, qualityData, alertsData, tablesData] = await Promise.all([
        getOverview(activeConnection.id).catch(() => null),
        getQualityScores(activeConnection.id).catch(() => null),
        listAlerts(true).catch(() => []),
        listTables(activeConnection.id, "").catch(() => ({ tables: [] }))
      ]);
      setOverview(overviewData);
      setHealthScore(qualityData?.overall_score ?? null);
      setAlerts(alertsData.slice(0, 3));
      
      const allTables = tablesData.tables || [];
      const sortedTables = [...allTables].sort((a, b) => (b.row_count || 0) - (a.row_count || 0));
      setTopTables(sortedTables.slice(0, 5));

      // Schema distribution
      const schemaMap = {};
      allTables.forEach(t => {
        const s = t.schema_name || "public";
        schemaMap[s] = (schemaMap[s] || 0) + 1;
      });
      const dist = Object.entries(schemaMap).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
      setSchemaDist(dist);

      // Auto-run AI analysis for the selected connection (uses backend cache)
      setLoadingAnalysis(true);
      try {
        setAnalysis(await analyzeDatabase(activeConnection.id, false, false));
      } catch (e) { console.error(e); }
      finally { setLoadingAnalysis(false); }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [activeConnection?.id]);

  useEffect(() => {
    if (activeConnection?.id) fetchData();
  }, [fetchData, activeConnection?.id]);

  const runQuickAnalysis = async () => {
    setLoadingAnalysis(true);
    setAnswers({});
    try { 
      setAnalysis(await analyzeDatabase(activeConnection.id, false, false)); 
    }
    catch (err) { console.error(err); }
    finally { setLoadingAnalysis(false); }
  };

  const handleQuestionClick = async (question, index) => {
    // If it's already open/loading, don't re-trigger
    if (answers[index]) return; 

    setAnswers(prev => ({ ...prev, [index]: { loading: true } }));
    try {
      const res = await sendMessageToAPI(question, null, activeConnection.id);
      setAnswers(prev => ({ ...prev, [index]: { loading: false, data: res } }));
    } catch (err) {
      console.error(err);
      setAnswers(prev => ({ ...prev, [index]: { loading: false, error: err.message || "Failed to load answer" } }));
    }
  };

  const handleGenerateDocs = async () => {
    setGeneratingDocs(true);
    try {
      // Fetch the generated HTML for the dictionary
      const res = await previewExport(activeConnection.id, "html");
      
      // Use html2pdf to download the HTML as a PDF
      const opt = {
        margin:       10,
        filename:     `${activeConnection.name.replace(/\\s/g, '_')}_Schema_Docs.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      
      const element = document.createElement('div');
      element.innerHTML = res.preview;
      
      // html2pdf is loaded globally via index.html
      if (window.html2pdf) {
        window.html2pdf().set(opt).from(element).save();
      } else {
        alert("PDF generator not loaded yet.");
      }
    } catch (err) { 
      console.error(err); 
      alert("Failed to generate PDF."); 
    }
    finally { setGeneratingDocs(false); }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await createExport(activeConnection.id, "json");
      const token = localStorage.getItem("token");
      
      // Create a temporary link to download the file directly
      const V1 = import.meta.env.VITE_API_URL || "http://localhost:8000/v1";
      const downloadUrl = `${V1}/export/${res.job_id}/download?token=${token}`;
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', '');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      
    } catch (err) { 
      console.error(err); 
      alert("Failed to download JSON export."); 
    }
    finally { setExporting(false); }
  };

  // ───── Welcome State (no connection) ─────
  if (!activeConnection) {
    return (
      <div className="flex flex-col items-center justify-center h-[85vh] text-center">
        <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-5" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
          <svg width="28" height="28" fill="none" stroke="var(--accent)" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-bright)" }}>Quick Start</h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-muted)" }}>
          Connect a database to get instant AI-powered insights.
        </p>
        <button onClick={() => navigate("/connections")} className="btn-accent text-sm">
          Select Connection
        </button>
      </div>
    );
  }

  // ───── Loading State (Skeleton) ─────
  if (loading && !overview) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2"><SkeletonLine width="200px" /><SkeletonLine width="120px" /></div>
          <div className="flex gap-2"><SkeletonCard style={{ width: 120, height: 36 }} /><SkeletonCard style={{ width: 160, height: 36 }} /></div>
        </div>
        <SkeletonGrid count={4} />
        <div className="grid grid-cols-2 gap-4">
          <SkeletonCard style={{ height: 180 }} />
          <SkeletonCard style={{ height: 180 }} />
        </div>
        <SkeletonCard style={{ height: 250 }} />
      </div>
    );
  }

  // ───── Connected State ─────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>Quick Insights</h1>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="tag" style={{ background: "var(--accent-glow)", color: "var(--accent)", fontSize: 12 }}>{activeConnection.name}</span>
            {healthScore !== null && (
              <span className="tag flex items-center gap-1" style={{ background: healthScore > 80 ? "rgba(45, 212, 168, 0.15)" : "rgba(245, 158, 11, 0.15)", color: healthScore > 80 ? "var(--teal)" : "#f59e0b", fontSize: 12 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                Health: {healthScore}%
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Quick Actions */}
          <button onClick={handleExport} disabled={exporting} className="btn-ghost" style={{ fontSize: 12, padding: "6px 12px" }}>
            {exporting ? "Exporting..." : "↓ Export JSON"}
          </button>
          <button onClick={handleGenerateDocs} disabled={generatingDocs} className="btn-ghost" style={{ fontSize: 12, padding: "6px 12px" }}>
            {generatingDocs ? "Generating..." : "⚡ Generate Docs"}
          </button>
          <button onClick={runQuickAnalysis} disabled={loadingAnalysis} className="btn-accent">
            {loadingAnalysis ? <><div className="spinner"></div> Generating...</> : <><svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Generate Quick Insights</>}
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Tables", value: overview?.total_tables || 0, color: "var(--accent)", icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/></svg> },
          { label: "Columns", value: overview?.total_columns || 0, color: "var(--teal)", icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M12 3v18M8 3v18M16 3v18"/></svg> },
          { label: "Rows", value: overview?.total_rows || 0, color: "var(--ice)", icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M3 8h18M3 12h18M3 16h18"/></svg> },
          { label: "Relationships", value: overview?.total_relationships || 0, color: "var(--coral)", icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg> },
        ].map((m, i) => (
          <div key={m.label} className={`card p-4 rise rise-${i}`} style={{ background: `linear-gradient(135deg, var(--bg-raised) 60%, color-mix(in srgb, ${m.color} 8%, transparent))` }}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `color-mix(in srgb, ${m.color} 12%, transparent)`, color: m.color }}>
                  {m.icon}
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{m.label}</span>
              </div>
              <span className="text-xl font-bold mono" style={{ color: m.color }}>{typeof m.value === "number" ? m.value.toLocaleString() : m.value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Schema Distribution + Alerts Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Schema Distribution Chart */}
        {schemaDist.length > 0 && (
          <div className="card p-5 rise">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg">📊</span>
              <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-bright)" }}>Schema Distribution</h3>
            </div>
            <div className="space-y-3">
              {schemaDist.map((s, i) => {
                const maxCount = schemaDist[0].count;
                const pct = Math.round((s.count / maxCount) * 100);
                const colors = ["var(--accent)", "var(--teal)", "var(--ice)", "var(--coral)"];
                const color = colors[i % colors.length];
                return (
                  <div key={s.name}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs mono font-semibold" style={{ color: "var(--text-bright)" }}>{s.name}</span>
                      <span className="text-xs mono" style={{ color }}>{s.count} tables</span>
                    </div>
                    <div className="stat-bar" style={{ height: 6 }}>
                      <div className="stat-bar-fill" style={{ width: `${pct}%`, background: color, transition: "width 0.6s ease" }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Critical Alerts */}
        {alerts.length > 0 ? (
          <div className="card p-5 rise" style={{ background: "var(--coral-dim)", border: "1px solid rgba(232,105,90,0.2)" }}>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg">🚨</span>
              <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--coral)" }}>Critical Alerts</h3>
            </div>
            <div className="space-y-3">
              {alerts.map(a => (
                <div key={a.id} className="flex flex-col p-3 rounded-lg" style={{ background: "rgba(0,0,0,0.2)", border: "1px solid rgba(232,105,90,0.1)" }}>
                  <span className="text-xs font-bold truncate" style={{ color: "var(--text-bright)" }}>{a.table_name}.{a.column_name}</span>
                  <span className="text-xs mt-1 overflow-hidden" style={{ color: "var(--coral)", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{a.message}</span>
                </div>
              ))}
            </div>
          </div>
        ) : schemaDist.length === 0 ? null : (
          <div className="card p-5 rise flex flex-col items-center justify-center" style={{ border: "1px solid var(--border)" }}>
            <span className="text-2xl mb-2">✅</span>
            <p className="text-sm font-semibold" style={{ color: "var(--teal)" }}>No Active Alerts</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Your database is looking healthy!</p>
          </div>
        )}
      </div>

      {/* Loading indicator for auto-analysis */}
      {loadingAnalysis && !analysis && (
        <div className="card p-8 flex items-center justify-center gap-3 rise">
          <div className="spinner"></div>
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>Generating AI insights automatically...</span>
        </div>
      )}

      {/* AI Analysis View */}
      {analysis && (
        <div className="space-y-4 rise">
          {/* Business Purpose Card */}
          <div className="card p-6" style={{ background: "var(--bg-raised)", border: "1px solid var(--accent-glow)" }}>
            <h3 className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "var(--accent)" }}>Business Purpose</h3>
            <p className="text-base leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-bright)" }}>
              {analysis.business_purpose || "No purpose inferred."}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Suggested Questions */}
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">💡</span>
                <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-bright)" }}>Suggested Questions</h3>
              </div>
              <ul className="space-y-3">
                {analysis.suggested_questions?.length > 0 ? (
                  analysis.suggested_questions.map((q, i) => (
                    <div key={i} className="flex flex-col rounded-lg overflow-hidden transition-all duration-300" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                      <button 
                        onClick={() => handleQuestionClick(q, i)}
                        className="flex gap-3 text-sm p-3 w-full text-left cursor-pointer hover:bg-white/5 transition-colors items-start"
                      >
                        <span style={{ color: "var(--accent)", marginTop: "2px" }}>→</span>
                        <span className="flex-1" style={{ color: "var(--text-secondary)" }}>{q}</span>
                        {!answers[i] && (
                          <span className="text-[10px] uppercase font-bold opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: "var(--accent)" }}>Ask AI</span>
                        )}
                      </button>
                      
                      {/* Answer Dropdown */}
                      {answers[i] && (
                        <div className="p-4 border-t" style={{ borderColor: "var(--border)", background: "rgba(0,0,0,0.2)" }}>
                          {answers[i].loading ? (
                            <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                              <div className="spinner"></div> Generating answer...
                            </div>
                          ) : answers[i].error ? (
                            <div className="text-xs text-red-400">{answers[i].error}</div>
                          ) : answers[i].data ? (
                            <div className="space-y-3">
                              <p className="text-sm whitespace-pre-wrap leading-relaxed" style={{ color: "var(--text-bright)" }}>
                                {answers[i].data.answer}
                              </p>
                              {answers[i].data.result?.rows && (
                                <div className="mt-2 overflow-x-auto rounded-lg border border-gray-700/50 max-h-[200px] custom-scrollbar">
                                  <table className="w-full text-left border-collapse text-[11px]">
                                    <thead>
                                      <tr style={{ background: "var(--bg-hover)" }}>
                                        {answers[i].data.result.columns.map((col, idx) => (
                                          <th key={idx} className="p-2 border-b border-gray-700/50 font-bold whitespace-nowrap text-gray-400">{col}</th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {answers[i].data.result.rows.map((row, rowIdx) => (
                                        <tr key={rowIdx} className="border-b border-gray-800/30 hover:bg-white/5 transition-colors">
                                          {row.map((cell, cellIdx) => (
                                            <td key={cellIdx} className="p-2 whitespace-nowrap text-gray-300">{cell !== null ? String(cell) : "NULL"}</td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              )}
                            </div>
                          ) : null}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>No questions generated.</p>
                )}
              </ul>
            </div>

            {/* Top Tables Leaderboard */}
            <div className="card p-5 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">🏆</span>
                <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-bright)" }}>Top Tables by Data Volume</h3>
              </div>
              
              {topTables.length > 0 ? (
                <div className="space-y-3">
                  {topTables.map((t, i) => {
                    const maxRows = topTables[0].row_count || 1;
                    const pct = Math.round(((t.row_count || 0) / maxRows) * 100);
                    const colors = ["var(--accent)", "var(--teal)", "var(--ice)", "var(--coral)", "#a78bfa"];
                    const color = colors[i];
                    const medals = ["🥇", "🥈", "🥉", "4.", "5."];
                    return (
                      <div key={t.name}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{medals[i]}</span>
                            <span className="text-xs mono font-semibold truncate" style={{ color: "var(--text-bright)", maxWidth: 180 }} title={t.name}>{t.name}</span>
                          </div>
                          <span className="text-[11px] mono" style={{ color }}>{(t.row_count || 0).toLocaleString()} rows</span>
                        </div>
                        <div className="stat-bar" style={{ height: 5 }}>
                          <div className="stat-bar-fill" style={{ width: `${pct}%`, background: color, transition: "width 0.6s ease" }}></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>No tables found.</p>
              )}
            </div>
          </div>

          {/* Enhance Button */}
          <div className="flex justify-center mt-8">
            <button 
              onClick={() => navigate("/dashboard")} 
              className="btn-cta-pulse px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all hover:scale-105"
              style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-dim))", color: "#0d0d0f", boxShadow: "0 0 24px var(--accent-glow)" }}
            >
              ✨ Enter Full Dashboard
              <span className="text-xs font-normal opacity-80">(Deep Analysis)</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
