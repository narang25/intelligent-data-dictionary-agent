import { useState, useEffect, useRef, useCallback } from "react";
import { useConnection } from "../context/ConnectionContext";
import { getOverview, analyzeDatabase, listTables, triggerBatchDocs, getBatchDocsStatus, getRelationshipGraph } from "../services/api";

export default function DashboardPage() {
  const { activeConnection } = useConnection();
  const [overview, setOverview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [tables, setTables] = useState([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [graphData, setGraphData] = useState(null);

  // Batch Docs State
  const [docsStatus, setDocsStatus] = useState(null);
  const [isGeneratingDocs, setIsGeneratingDocs] = useState(false);

  // Graph interaction state
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);


  const fetchData = useCallback(async () => {
    setAnalysis(null);
    try {
      const [ov, tb, graph] = await Promise.all([
        getOverview(activeConnection.id),
        listTables(activeConnection.id).catch(() => ({ tables: [] })),
        getRelationshipGraph(activeConnection.id).catch(() => ({ nodes: [], edges: [] })),
      ]);
      setOverview(ov);
      setTables(tb.tables || []);
      setGraphData(graph);
    } catch (err) { console.error(err); }
  }, [activeConnection?.id]);

  useEffect(() => {
    if (activeConnection?.id) fetchData();
  }, [fetchData, activeConnection?.id]);

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

      {/* Metric Cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { ...metrics[0], icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/></svg> },
          { ...metrics[1], icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M12 3v18M8 3v18M16 3v18"/></svg> },
          { ...metrics[2], icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M3 8h18M3 12h18M3 16h18"/></svg> },
          { ...metrics[3], icon: <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg> },
        ].map((m, i) => (
          <div key={m.label} className={`card p-4 rise rise-${i}`} style={{ background: `linear-gradient(135deg, var(--bg-raised) 60%, color-mix(in srgb, ${m.color} 8%, transparent))` }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `color-mix(in srgb, ${m.color} 12%, transparent)`, color: m.color }}>
                  {m.icon}
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{m.label}</span>
              </div>
              <span className="text-xl font-bold mono" style={{ color: m.color }}>{typeof m.value === "number" ? m.value.toLocaleString() : m.value}</span>
            </div>
            <div className="stat-bar">
              <div className="stat-bar-fill" style={{ width: `${m.pct}%`, background: m.color }}></div>
            </div>
          </div>
        ))}
      </div>

      {/* Schema Distribution Donut */}
      {overview && (() => {
        const schemas = {};
        tables.forEach(t => { const s = t.schema_name || 'public'; schemas[s] = (schemas[s] || 0) + 1; });
        const schemaEntries = Object.entries(schemas).sort((a, b) => b[1] - a[1]);
        const total = schemaEntries.reduce((s, [, v]) => s + v, 0) || 1;
        const colors = ["var(--accent)", "var(--teal)", "var(--ice)", "var(--coral)"];
        let offset = 0;
        return schemaEntries.length > 0 && (
          <div className="card p-5 rise">
            <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: "var(--text-muted)" }}>Schema Distribution</h3>
            <div className="flex items-center gap-8">
              <div className="relative" style={{ width: 120, height: 120 }}>
                <svg viewBox="0 0 100 100" width="120" height="120">
                  {schemaEntries.map(([name, count], i) => {
                    const pct = count / total;
                    const dashLen = pct * 251.2;
                    const dashOffset = -offset * 251.2;
                    offset += pct;
                    return (
                      <circle key={name} cx="50" cy="50" r="40" fill="none"
                        stroke={colors[i % colors.length]} strokeWidth="10"
                        strokeDasharray={`${dashLen} ${251.2 - dashLen}`}
                        strokeDashoffset={dashOffset}
                        style={{ transform: "rotate(-90deg)", transformOrigin: "center" }}
                      />
                    );
                  })}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-lg font-bold mono" style={{ color: "var(--text-bright)" }}>{total}</span>
                  <span className="text-[8px] uppercase" style={{ color: "var(--text-muted)" }}>Total</span>
                </div>
              </div>
              <div className="flex-1 space-y-2">
                {schemaEntries.map(([name, count], i) => (
                  <div key={name} className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded" style={{ background: colors[i % colors.length] }}></div>
                    <span className="text-sm mono flex-1" style={{ color: "var(--text-primary)" }}>{name}</span>
                    <span className="text-sm mono font-bold" style={{ color: colors[i % colors.length] }}>{count}</span>
                    <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{Math.round(count / total * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })()}

      {/* ═══════ Interactive Relationship Graph ═══════ */}
      {graphData && graphData.edges.length > 0 && (
        <RelationshipGraph
          graphData={graphData}
          hoveredNode={hoveredNode}
          setHoveredNode={setHoveredNode}
          selectedNode={selectedNode}
          setSelectedNode={setSelectedNode}
        />
      )}

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


// ═══════════════════════════════════════════
// Interactive Relationship Graph Component
// ═══════════════════════════════════════════
function RelationshipGraph({ graphData, hoveredNode, setHoveredNode, selectedNode, setSelectedNode }) {
  const svgRef = useRef(null);
  const [positions, setPositions] = useState({});
  const [dragging, setDragging] = useState(null);
  const [svgSize, setSvgSize] = useState({ width: 900, height: 450 });

  // Compute initial circular layout
  useEffect(() => {
    if (!graphData?.nodes?.length) return;

    const container = svgRef.current?.parentElement;
    const w = container?.clientWidth || 900;
    const h = 450;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSvgSize({ width: w, height: h });

    // Only set positions of nodes that have edges (connected nodes)
    const connectedIds = new Set();
    graphData.edges.forEach(e => {
      connectedIds.add(e.source);
      connectedIds.add(e.target);
    });

    const connectedNodes = graphData.nodes.filter(n => connectedIds.has(n.id));
    const totalNodes = connectedNodes.length;
    if (totalNodes === 0) return;

    const cx = w / 2;
    const cy = h / 2;
    const radiusX = (w / 2) - 100;
    const radiusY = (h / 2) - 60;

    const newPos = {};
    connectedNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / totalNodes - Math.PI / 2;
      newPos[node.id] = {
        x: cx + radiusX * Math.cos(angle),
        y: cy + radiusY * Math.sin(angle),
      };
    });
    setPositions(newPos);
  }, [graphData]);

  // Drag handlers
  const handleMouseDown = useCallback((nodeId, e) => {
    e.preventDefault();
    setDragging(nodeId);
    setSelectedNode(nodeId);
  }, [setSelectedNode]);

  const handleMouseMove = useCallback((e) => {
    if (!dragging || !svgRef.current) return;
    const svg = svgRef.current;
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setPositions(prev => ({ ...prev, [dragging]: { x, y } }));
  }, [dragging]);

  const handleMouseUp = useCallback(() => {
    setDragging(null);
  }, []);

  if (!graphData?.edges?.length || Object.keys(positions).length === 0) return null;

  // Determine which edges/nodes to highlight
  const highlightId = hoveredNode || selectedNode;
  const connectedToHighlight = new Set();
  if (highlightId) {
    graphData.edges.forEach(e => {
      if (e.source === highlightId) connectedToHighlight.add(e.target);
      if (e.target === highlightId) connectedToHighlight.add(e.source);
    });
  }

  return (
    <div className="card p-0 overflow-hidden rise">
      <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <span className="text-lg">🔗</span>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-bright)" }}>Schema Relationship Graph</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] mono" style={{ color: "var(--text-muted)" }}>
            {graphData.edges.length} connections • Drag nodes to rearrange
          </span>
          {selectedNode && (
            <button onClick={() => setSelectedNode(null)} className="text-[10px] font-bold px-2 py-0.5 rounded" style={{ background: "var(--accent-glow)", color: "var(--accent)" }}>
              Clear Selection
            </button>
          )}
        </div>
      </div>
      <div style={{ background: "var(--bg-base)", position: "relative" }}>
        <svg
          ref={svgRef}
          width="100%"
          height={svgSize.height}
          viewBox={`0 0 ${svgSize.width} ${svgSize.height}`}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ cursor: dragging ? "grabbing" : "default" }}
        >
          <defs>
            <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--border-active)" />
            </marker>
            <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--accent)" />
            </marker>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" />
            </filter>
          </defs>

          {/* Edges */}
          {graphData.edges.map((edge, i) => {
            const from = positions[edge.source];
            const to = positions[edge.target];
            if (!from || !to) return null;

            const isActive = highlightId && (edge.source === highlightId || edge.target === highlightId);
            const isDimmed = highlightId && !isActive;

            // Compute a slight curve for the edge
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const mx = (from.x + to.x) / 2 + dy * 0.1;
            const my = (from.y + to.y) / 2 - dx * 0.1;

            return (
              <g key={i}>
                <path
                  d={`M ${from.x} ${from.y} Q ${mx} ${my} ${to.x} ${to.y}`}
                  fill="none"
                  stroke={isActive ? "var(--accent)" : "var(--border-active)"}
                  strokeWidth={isActive ? 2 : 1}
                  strokeDasharray={isActive ? "none" : "6 3"}
                  opacity={isDimmed ? 0.15 : isActive ? 1 : 0.5}
                  markerEnd={isActive ? "url(#arrowhead-active)" : "url(#arrowhead)"}
                  style={{ transition: "opacity 0.2s, stroke-width 0.2s" }}
                />
                {/* Edge label on hover */}
                {isActive && (
                  <text x={mx} y={my - 8} textAnchor="middle" fill="var(--accent)" fontSize="9" fontFamily="monospace" fontWeight="bold">
                    {edge.source_column} → {edge.target_column}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {graphData.nodes.filter(n => positions[n.id]).map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;

            const isHighlighted = node.id === highlightId;
            const isConnected = connectedToHighlight.has(node.id);
            const isDimmed = highlightId && !isHighlighted && !isConnected;

            const nodeColor = isHighlighted ? "var(--accent)" : isConnected ? "var(--teal)" : "var(--text-muted)";

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onMouseDown={(e) => handleMouseDown(node.id, e)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: "grab", transition: dragging === node.id ? "none" : "opacity 0.2s", opacity: isDimmed ? 0.2 : 1 }}
              >
                {/* Glow ring on highlight */}
                {isHighlighted && (
                  <circle r="30" fill="none" stroke="var(--accent)" strokeWidth="1" opacity="0.3" filter="url(#glow)" />
                )}
                
                {/* Node circle */}
                <circle
                  r="6"
                  fill={isHighlighted ? "var(--accent)" : isConnected ? "var(--teal)" : "var(--bg-raised)"}
                  stroke={nodeColor}
                  strokeWidth={isHighlighted ? 2.5 : 1.5}
                />

                {/* Label */}
                <text
                  y={-14}
                  textAnchor="middle"
                  fill={isHighlighted ? "var(--accent)" : isConnected ? "var(--teal)" : "var(--text-secondary)"}
                  fontSize={isHighlighted ? "11" : "10"}
                  fontFamily="monospace"
                  fontWeight={isHighlighted ? "bold" : "normal"}
                >
                  {node.label}
                </text>

                {/* Row count badge on highlight */}
                {isHighlighted && (
                  <text y={18} textAnchor="middle" fill="var(--text-muted)" fontSize="8" fontFamily="monospace">
                    {node.row_count.toLocaleString()} rows • {node.column_count} cols
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
