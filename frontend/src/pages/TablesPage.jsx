import { useState, useEffect } from "react";
import { useConnection } from "../context/ConnectionContext";
import { listTables, getTableDetail, getSampleData, analyzeTable, analyzeQuality } from "../services/api";

export default function TablesPage() {
  const { activeConnection } = useConnection();
  const [tables, setTables] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [sampleData, setSampleData] = useState(null);
  const [tableAnalysis, setTableAnalysis] = useState(null);
  const [loadingSample, setLoadingSample] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [tab, setTab] = useState("schema");

  useEffect(() => {
    if (activeConnection?.id) fetchTables();
  }, [activeConnection?.id, search]);

  const fetchTables = async () => {
    try { setTables((await listTables(activeConnection.id, search)).tables || []); }
    catch (err) { console.error(err); }
  };

  const selectTable = async (name) => {
    setSelected(name); setTab("schema"); setSampleData(null); setTableAnalysis(null);
    try { setDetail(await getTableDetail(activeConnection.id, name)); }
    catch (err) { console.error(err); }
  };

  const fetchSample = async () => {
    setLoadingSample(true);
    try { setSampleData(await getSampleData(activeConnection.id, selected)); }
    catch (err) { console.error(err); } finally { setLoadingSample(false); }
  };

  const fetchAnalysis = async () => {
    setLoadingAnalysis(true);
    try { setTableAnalysis(await analyzeTable(activeConnection.id, selected)); }
    catch (err) { console.error(err); } finally { setLoadingAnalysis(false); }
  };

  if (!activeConnection) {
    return <div className="flex items-center justify-center h-[80vh]" style={{ color: "var(--text-muted)" }}>Connect a database first.</div>;
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-5rem)]">
      {/* Left panel — Table list */}
      <div className="w-[260px] min-w-[260px] card flex flex-col">
        <div className="p-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <div className="relative">
            <svg className="absolute left-2.5 top-1/2 -translate-y-1/2" width="14" height="14" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter tables..."
              className="w-full pl-8 pr-3 py-2 rounded-lg text-xs focus:outline-none mono"
              style={{ background: "var(--bg-surface)", color: "var(--text-primary)", border: "1px solid var(--border)" }} />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5">
          {tables.map(t => (
            <button key={t.name} onClick={() => selectTable(t.name)}
              className="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-150 group"
              style={{
                background: selected === t.name ? "var(--accent-glow)" : "transparent",
                color: selected === t.name ? "var(--accent)" : "var(--text-secondary)",
                borderLeft: selected === t.name ? "2px solid var(--accent)" : "2px solid transparent",
              }}>
              <div className="font-medium mono truncate">{t.name}</div>
              <div className="flex gap-2 mt-0.5" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                <span>{t.column_count} cols</span>
                <span>·</span>
                <span>{(t.row_count || 0).toLocaleString()} rows</span>
              </div>
            </button>
          ))}
          {tables.length === 0 && <p className="text-xs p-4 text-center" style={{ color: "var(--text-muted)" }}>No tables. Sync your connection.</p>}
        </div>
      </div>

      {/* Right panel — Detail */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {!selected ? (
          <div className="flex items-center justify-center h-full" style={{ color: "var(--text-muted)" }}>
            <div className="text-center">
              <svg width="32" height="32" fill="none" stroke="var(--text-muted)" strokeWidth="1" viewBox="0 0 24 24" className="mx-auto mb-3 opacity-40"><path d="M3 6h18M3 12h18M3 18h18M9 6v12M15 6v12"/></svg>
              <p className="text-sm">Select a table to explore</p>
            </div>
          </div>
        ) : detail ? (
          <div className="rise space-y-4">
            {/* Table header */}
            <div>
              <h2 className="text-lg font-bold mono" style={{ color: "var(--text-bright)" }}>
                {detail.schema_name ? <span style={{ color: "var(--text-muted)" }}>{detail.schema_name}.</span> : null}{detail.name}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="tag" style={{ background: "var(--accent-glow)", color: "var(--accent)", fontSize: 12 }}>TABLE</span>
                <span className="text-xs mono" style={{ color: "var(--text-muted)" }}>{detail.row_count?.toLocaleString() || "?"} rows · {detail.columns?.length} columns</span>
              </div>
            </div>

            {/* Tab bar — underline style */}
            <div className="flex gap-0" style={{ borderBottom: "1px solid var(--border)" }}>
              {[
                { id: "schema", label: "Schema" },
                { id: "ai", label: "AI Analysis" },
                { id: "sample", label: "Preview" },
              ].map(t => (
                <button key={t.id} onClick={() => {
                  setTab(t.id);
                  if (t.id === "sample" && !sampleData) fetchSample();
                  if (t.id === "ai" && !tableAnalysis) fetchAnalysis();
                }}
                  className="px-4 py-2.5 text-sm font-semibold transition-all duration-150"
                  style={{
                    color: tab === t.id ? "var(--accent)" : "var(--text-muted)",
                    borderBottom: tab === t.id ? "2px solid var(--accent)" : "2px solid transparent",
                    marginBottom: "-1px",
                  }}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Schema Tab */}
            {tab === "schema" && (
              <div className="card overflow-hidden rise">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ background: "var(--bg-surface)" }}>
                      {["Column", "Type", "Nullable", "Keys", "Description"].map(h => (
                        <th key={h} className="text-left px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detail.columns?.map(c => (
                      <tr key={c.name} className="transition-colors" style={{ borderBottom: "1px solid var(--border)" }}
                        onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                        <td className="px-4 py-2 font-medium mono" style={{ color: "var(--text-bright)", fontSize: 11 }}>{c.name}</td>
                        <td className="px-4 py-2 mono" style={{ color: "var(--teal)", fontSize: 10 }}>{c.data_type}</td>
                        <td className="px-4 py-2" style={{ color: "var(--text-muted)", fontSize: 11 }}>{c.is_nullable ? "yes" : "no"}</td>
                        <td className="px-4 py-2">
                          {c.is_primary_key && <span className="tag mr-1" style={{ background: "var(--accent-glow)", color: "var(--accent)", fontSize: 9 }}>PK</span>}
                          {c.is_foreign_key && <span className="tag" style={{ background: "var(--teal-dim)", color: "var(--teal)", fontSize: 9 }}>FK</span>}
                        </td>
                        <td className="px-4 py-2 max-w-xs truncate" style={{ color: "var(--text-muted)", fontSize: 10 }}>{c.ai_description || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* AI Analysis Tab */}
            {tab === "ai" && (
              <div className="space-y-3 rise">
                {loadingAnalysis ? (
                  <div className="card p-8 flex items-center justify-center gap-2"><div className="spinner"></div><span className="text-xs" style={{ color: "var(--text-muted)" }}>Analyzing with AI...</span></div>
                ) : tableAnalysis ? (
                  <>
                    <div className="card p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="tag" style={{ background: "var(--coral-dim)", color: "var(--coral)" }}>Context</span>
                      </div>
                      <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>{tableAnalysis.business_context}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {tableAnalysis.key_insights?.length > 0 && (
                        <div className="card p-4">
                          <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--accent)" }}>Insights</h4>
                          <ul className="space-y-1.5">
                            {tableAnalysis.key_insights.map((ins, i) => (
                              <li key={i} className="text-[11px] flex gap-2" style={{ color: "var(--text-secondary)" }}>
                                <span style={{ color: "var(--accent)" }}>›</span>{ins}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {tableAnalysis.recommendations?.length > 0 && (
                        <div className="card p-4">
                          <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--teal)" }}>Recommendations</h4>
                          <ul className="space-y-1.5">
                            {tableAnalysis.recommendations.map((rec, i) => (
                              <li key={i} className="text-[11px] flex gap-2" style={{ color: "var(--text-secondary)" }}>
                                <span style={{ color: "var(--teal)" }}>›</span>{rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="card p-8 text-center">{<p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading analysis...</p>}</div>
                )}
              </div>
            )}

            {/* Sample Data Tab */}
            {tab === "sample" && (
              <div className="card overflow-auto max-h-[500px] rise">
                {loadingSample ? (
                  <div className="p-8 flex items-center justify-center gap-2"><div className="spinner"></div><span className="text-xs" style={{ color: "var(--text-muted)" }}>Loading preview...</span></div>
                ) : sampleData ? (
                  <table className="w-full text-[11px] mono">
                    <thead>
                      <tr className="sticky top-0" style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)" }}>
                        {sampleData.columns?.map(col => (
                          <th key={col} className="text-left px-3 py-2 font-semibold whitespace-nowrap text-[10px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleData.rows?.map((row, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid var(--border)" }} className="transition-colors"
                          onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                          {row.map((val, j) => (
                            <td key={j} className="px-3 py-1.5 whitespace-nowrap max-w-[180px] truncate" style={{ color: val != null ? "var(--text-secondary)" : "var(--text-muted)" }}>
                              {val != null ? String(val) : <em>null</em>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 12 }}>No data</div>}
              </div>
            )}

            {/* Relationships */}
            {detail.relationships?.length > 0 && (
              <div className="card p-4">
                <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>Relationships</h4>
                <div className="space-y-1">
                  {detail.relationships.map((r, i) => (
                    <div key={i} className="flex items-center gap-2 text-[11px] mono">
                      <span style={{ color: "var(--accent)" }}>{r.source_column}</span>
                      <svg width="12" height="12" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                      <span style={{ color: "var(--teal)" }}>{r.target_table}.{r.target_column}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
