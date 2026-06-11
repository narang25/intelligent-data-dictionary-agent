import { useState, useEffect, useCallback } from "react";
import { getAllLineage, createLineage, deleteLineage } from "../services/api";
import { useConnection } from "../context/ConnectionContext";

export default function LineagePage() {
  const { activeConnection } = useConnection();
  const [lineage, setLineage] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ source_table: "", source_column: "", target_table: "", target_column: "", transformation_expression: "" });

  const fetchLineage = useCallback(async () => {
    if (!activeConnection?.id) return;
    setLoading(true);
    try {
      const data = await getAllLineage(activeConnection.id);
      setLineage(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [activeConnection]);

  useEffect(() => { fetchLineage(); }, [fetchLineage]);

  const handleAdd = async () => {
    try {
      await createLineage(form);
      setForm({ source_table: "", source_column: "", target_table: "", target_column: "", transformation_expression: "" });
      setShowAdd(false);
      fetchLineage();
    } catch (e) { console.error(e); }
  };

  const handleDelete = async (id) => {
    try {
      await deleteLineage(id);
      fetchLineage();
    } catch (e) { console.error(e); }
  };

  // Filter out any completely empty ones that got saved by accident
  const validLineage = lineage.filter(l => l.source_table || l.target_table);


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>🔗 Data Lineage</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Track column-level data flow across tables</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-accent text-sm px-4 py-2">
          + Add Lineage
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <div className="card p-4 space-y-3">
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-bright)" }}>New Lineage Entry</h3>
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="Source Table" className="input" value={form.source_table} onChange={e => setForm({ ...form, source_table: e.target.value })} />
            <input placeholder="Source Column" className="input" value={form.source_column} onChange={e => setForm({ ...form, source_column: e.target.value })} />
            <input placeholder="Target Table" className="input" value={form.target_table} onChange={e => setForm({ ...form, target_table: e.target.value })} />
            <input placeholder="Target Column" className="input" value={form.target_column} onChange={e => setForm({ ...form, target_column: e.target.value })} />
          </div>
          <input placeholder="Transformation (e.g. UPPER(first_name) || ' ' || last_name)" className="input w-full" value={form.transformation_expression} onChange={e => setForm({ ...form, transformation_expression: e.target.value })} />
          <button onClick={handleAdd} className="btn-accent text-sm px-4 py-2">Save</button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>Loading lineage data...</div>
      ) : validLineage.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-lg mb-2" style={{ color: "var(--text-muted)" }}>No lineage data yet</p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Click "+ Add Lineage" to define column-level data flows</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Visual Flow Cards */}
          <div className="grid grid-cols-1 gap-4">
            {validLineage.map(l => {
              const isAuto = l.transformation_expression === "Auto (Foreign Key)";
              const accentColor = isAuto ? "var(--teal)" : "var(--purple)";
              const bgColor = isAuto ? "rgba(45, 212, 191, 0.05)" : "rgba(168, 85, 247, 0.05)";

              return (
                <div key={l.id} className="card p-4 flex flex-col sm:flex-row items-center gap-4 sm:gap-6 border border-transparent hover:border-gray-800 transition-all">
                  
                  {/* Source Table */}
                  <div className="flex-1 w-full rounded-lg p-3 text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                    <div className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>Source</div>
                    <div className="text-sm font-semibold truncate" style={{ color: "var(--text-bright)" }}>{l.source_table}</div>
                    <div className="text-xs font-mono mt-1 px-2 py-1 rounded inline-block" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
                      {l.source_column}
                    </div>
                  </div>

                  {/* Transformation Arrow */}
                  <div className="flex flex-col items-center shrink-0 w-48">
                    <span className="text-[10px] mb-1 px-2 py-0.5 rounded-full" style={{ background: bgColor, color: accentColor }}>
                      {isAuto ? "FOREIGN KEY" : "MANUAL ETL"}
                    </span>
                    <div className="w-full flex items-center justify-center relative my-2">
                      <div className="h-[2px] w-full" style={{ background: accentColor, opacity: 0.5 }}></div>
                      <div className="absolute right-0 w-3 h-3 border-t-2 border-r-2 transform rotate-45 mr-1" style={{ borderColor: accentColor, opacity: 0.5 }}></div>
                    </div>
                    {l.transformation_expression && !isAuto && (
                      <span className="text-[10px] mono text-center truncate w-full" style={{ color: "var(--ice)" }} title={l.transformation_expression}>
                        {l.transformation_expression}
                      </span>
                    )}
                  </div>

                  {/* Target Table */}
                  <div className="flex-1 w-full rounded-lg p-3 text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                    <div className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>Target</div>
                    <div className="text-sm font-semibold truncate" style={{ color: "var(--text-bright)" }}>{l.target_table}</div>
                    <div className="text-xs font-mono mt-1 px-2 py-1 rounded inline-block" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
                      {l.target_column}
                    </div>
                  </div>

                </div>
              );
            })}
          </div>

          {/* Table view */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--text-bright)" }}>All Lineage Entries</h3>
            <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--bg-surface)" }}>
                  <th className="text-left px-3 py-2 text-xs font-semibold" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>Source</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>Target</th>
                  <th className="text-left px-3 py-2 text-xs font-semibold" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>Transform</th>
                  <th className="text-center px-3 py-2 text-xs font-semibold" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)", width: 50 }}></th>
                </tr>
              </thead>
              <tbody>
                {validLineage.map(l => {
                  const isAuto = l.transformation_expression === "Auto (Foreign Key)";
                  return (
                    <tr key={l.id} className="hover:bg-white/5" style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="px-3 py-2 text-xs mono" style={{ color: "var(--text-secondary)" }}>{l.source_table}.{l.source_column}</td>
                      <td className="px-3 py-2 text-xs mono" style={{ color: "var(--text-secondary)" }}>{l.target_table}.{l.target_column}</td>
                      <td className="px-3 py-2 text-xs" style={{ color: isAuto ? "var(--teal)" : "var(--ice)" }}>{l.transformation_expression || "—"}</td>
                      <td className="px-3 py-2 text-center">
                        {!isAuto && (
                          <button 
                            onClick={() => handleDelete(l.id)} 
                            className="p-1 hover:bg-red-500/20 text-red-400 rounded cursor-pointer bg-transparent border-none"
                            title="Delete Lineage"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
