import { useState, useEffect, useCallback } from "react";
import { getAllLineage, createLineage } from "../services/api";

export default function LineagePage() {
  const [lineage, setLineage] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ source_table: "", source_column: "", target_table: "", target_column: "", transformation_expression: "" });

  const fetchLineage = useCallback(async () => {
    try {
      const data = await getAllLineage();
      setLineage(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchLineage(); }, [fetchLineage]);

  const handleAdd = async () => {
    try {
      await createLineage(form);
      setForm({ source_table: "", source_column: "", target_table: "", target_column: "", transformation_expression: "" });
      setShowAdd(false);
      fetchLineage();
    } catch (e) { console.error(e); }
  };

  // Build node-edge graph from lineage data
  const nodes = new Map();
  const edges = [];
  lineage.forEach((l) => {
    const srcKey = `${l.source_table}.${l.source_column}`;
    const tgtKey = `${l.target_table}.${l.target_column}`;
    if (!nodes.has(srcKey)) nodes.set(srcKey, { id: srcKey, table: l.source_table, column: l.source_column });
    if (!nodes.has(tgtKey)) nodes.set(tgtKey, { id: tgtKey, table: l.target_table, column: l.target_column });
    edges.push({ from: srcKey, to: tgtKey, transform: l.transformation_expression });
  });

  // Group nodes by table
  const tableGroups = {};
  nodes.forEach((n) => {
    if (!tableGroups[n.table]) tableGroups[n.table] = [];
    tableGroups[n.table].push(n);
  });

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
      ) : lineage.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-lg mb-2" style={{ color: "var(--text-muted)" }}>No lineage data yet</p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Click "+ Add Lineage" to define column-level data flows</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* DAG Visualization */}
          <div className="card p-6" style={{ minHeight: 300 }}>
            <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text-bright)" }}>Lineage Graph</h3>
            <div className="flex flex-wrap gap-8 items-start">
              {Object.entries(tableGroups).map(([table, cols]) => (
                <div key={table} className="rounded-xl p-4 min-w-[180px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                  <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "var(--ice)" }}>📋 {table}</div>
                  {cols.map(c => (
                    <div key={c.id} className="text-xs px-2 py-1.5 rounded mb-1" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
                      {c.column}
                    </div>
                  ))}
                </div>
              ))}
            </div>
            {/* Edges */}
            <div className="mt-4 space-y-1">
              {edges.map((e, i) => (
                <div key={i} className="text-xs flex items-center gap-2" style={{ color: "var(--text-muted)" }}>
                  <span className="font-mono px-1.5 py-0.5 rounded" style={{ background: "var(--bg-surface)" }}>{e.from}</span>
                  <span style={{ color: "var(--teal)" }}>→</span>
                  <span className="font-mono px-1.5 py-0.5 rounded" style={{ background: "var(--bg-surface)" }}>{e.to}</span>
                  {e.transform && <span className="italic" style={{ color: "var(--ice)" }}>({e.transform})</span>}
                </div>
              ))}
            </div>
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
                </tr>
              </thead>
              <tbody>
                {lineage.map(l => (
                  <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="px-3 py-2 text-xs mono" style={{ color: "var(--text-secondary)" }}>{l.source_table}.{l.source_column}</td>
                    <td className="px-3 py-2 text-xs mono" style={{ color: "var(--text-secondary)" }}>{l.target_table}.{l.target_column}</td>
                    <td className="px-3 py-2 text-xs" style={{ color: "var(--ice)" }}>{l.transformation_expression || "—"}</td>
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
