import { useState } from "react";
import { useVisualization } from "../../context/VisualizationContext";
import { useNavigate } from "react-router-dom";
import { explainSQL } from "../../services/api";

export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";
  const navigate = useNavigate();
  const { setChartData } = useVisualization();
  const [copied, setCopied] = useState(false);
  const [explainResult, setExplainResult] = useState(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [showExplain, setShowExplain] = useState(false);

  const copySQL = async () => {
    if (!message.sql) return;
    try {
      await navigator.clipboard.writeText(message.sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) { console.error("Copy failed:", err); }
  };

  const exportCSV = () => {
    if (!message.result?.columns) return;
    const headers = message.result.columns.join(",");
    const rows = message.result.rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([headers + "\n" + rows], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "query_result.csv";
    link.click();
  };

  const generateChart = () => {
    if (!message.result?.columns) return;
    setChartData(message.result);
    navigate("/visualize");
  };

  const handleExplain = async () => {
    if (explainResult) {
      setShowExplain(!showExplain);
      return;
    }
    setExplainLoading(true);
    try {
      const res = await explainSQL(message.sql);
      setExplainResult(res);
      setShowExplain(true);
    } catch (err) { console.error("Explain failed:", err); }
    finally { setExplainLoading(false); }
  };

  // Confidence badge color
  const confidenceColor = (score) => {
    if (score >= 80) return "var(--teal)";
    if (score >= 50) return "#f59e0b";
    return "var(--coral)";
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} w-full`}>
      {/* AI avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mr-2.5 mt-1" style={{ background: "var(--accent-glow)", border: "1px solid var(--border-active)" }}>
          <span className="text-xs">✨</span>
        </div>
      )}
      <div className="max-w-[75%] rounded-xl px-4 py-3 whitespace-pre-wrap break-words overflow-hidden"
        style={isUser
          ? { background: "linear-gradient(135deg, var(--accent), var(--accent-dim))", color: "var(--user-bubble-text)", fontSize: 14, borderBottomRightRadius: 4 }
          : { background: "var(--bg-raised)", border: "1px solid var(--border)", color: "var(--text-primary)", fontSize: 14, borderTopLeftRadius: 4 }}>

        {/* Mode label + confidence badge */}
        {!isUser && message.mode && (
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold"
              style={{ color: message.mode === "sql" ? "var(--ice)" : "var(--teal)" }}>
              {message.mode === "sql" ? "📊 SQL Query" : "📖 Documentation"}
            </span>
            {message.confidence && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{ background: `color-mix(in srgb, ${confidenceColor(message.confidence.score)} 15%, transparent)`, color: confidenceColor(message.confidence.score), border: `1px solid ${confidenceColor(message.confidence.score)}` }}>
                {message.confidence.score}% confidence
              </span>
            )}
          </div>
        )}

        {/* Message text */}
        <div className="overflow-wrap-anywhere leading-relaxed">{message.text}</div>

        {/* Confidence warnings */}
        {!isUser && message.confidence?.warning && (
          <div className="mt-2 p-2 rounded-lg text-xs" style={{ background: "var(--coral-dim)", border: "1px solid rgba(232,105,90,0.2)", color: "var(--coral)" }}>
            ⚠️ {message.confidence.warning}
          </div>
        )}

        {/* SQL block + results */}
        {!isUser && message.mode === "sql" && message.sql && (
          <div className="mt-4 space-y-3">

            {/* SQL code */}
            <div className="p-3 rounded-lg text-sm overflow-x-auto relative mono"
              style={{ background: "var(--code-bg)", color: "var(--code-text)" }}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold" style={{ color: "#fff" }}>SQL</span>
                <div className="flex gap-1.5">
                  <button onClick={handleExplain} disabled={explainLoading}
                    className="text-xs px-2.5 py-1 rounded transition-all"
                    style={{ background: showExplain ? "var(--ice)" : "var(--bg-hover)", color: showExplain ? "#fff" : "var(--ice)", border: "1px solid rgba(96,165,250,0.3)" }}>
                    {explainLoading ? "Analyzing..." : showExplain ? "Hide Explain" : "🔍 Explain"}
                  </button>
                  <button onClick={copySQL}
                    className="text-xs px-2.5 py-1 rounded transition-all"
                    style={copied
                      ? { background: "var(--teal)", color: "#fff" }
                      : { background: "var(--bg-hover)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}>
                    {copied ? "Copied ✓" : "Copy"}
                  </button>
                </div>
              </div>
              <pre className="text-xs leading-relaxed">{message.sql}</pre>
            </div>

            {/* AI Explain Result */}
            {showExplain && explainResult && (
              <div className="space-y-2 rise">
                <div className="p-3 rounded-lg" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
                  <div className="font-semibold text-xs mb-1.5" style={{ color: "var(--ice)" }}>🧠 Plain English Explanation</div>
                  <div className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>{explainResult.explanation}</div>
                </div>
                {explainResult.performance_risks?.length > 0 && (
                  <div className="p-3 rounded-lg" style={{ background: "var(--coral-dim)", border: "1px solid rgba(232,105,90,0.15)" }}>
                    <div className="font-semibold text-xs mb-1.5" style={{ color: "var(--coral)" }}>⚠️ Performance Risks</div>
                    <ul className="space-y-1">
                      {explainResult.performance_risks.map((risk, i) => (
                        <li key={i} className="text-xs flex gap-1.5" style={{ color: "var(--text-secondary)" }}>
                          <span style={{ color: "var(--coral)" }}>›</span>{risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {explainResult.optimized_sql && (
                  <div className="p-3 rounded-lg" style={{ background: "var(--teal-dim)", border: "1px solid rgba(45,212,168,0.15)" }}>
                    <div className="font-semibold text-xs mb-1.5" style={{ color: "var(--teal)" }}>✨ Optimized Version</div>
                    <pre className="text-xs mono leading-relaxed" style={{ color: "var(--text-secondary)" }}>{explainResult.optimized_sql}</pre>
                  </div>
                )}
              </div>
            )}

            {/* Explanation */}
            {message.explanation && (
              <div className="p-3 rounded-lg text-sm"
                style={{ background: "var(--ice-dim)", border: "1px solid rgba(96,165,250,0.15)", color: "var(--text-primary)" }}>
                <div className="font-semibold mb-1 text-xs" style={{ color: "var(--ice)" }}>💡 Explanation</div>
                <div className="leading-relaxed" style={{ color: "var(--text-secondary)" }}>{message.explanation}</div>
              </div>
            )}

            {/* Result table */}
            {message.result?.columns && (
              <div className="overflow-x-auto">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Result</span>
                  <div className="flex gap-2">
                    <button onClick={exportCSV} className="btn-ghost" style={{ padding: "4px 10px", fontSize: 11 }}>Export CSV</button>
                    <button onClick={generateChart} className="btn-accent" style={{ padding: "4px 10px", fontSize: 11 }}>Chart</button>
                  </div>
                </div>

                <table className="w-full text-sm mono" style={{ borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "var(--bg-surface)" }}>
                      {message.result.columns.map((col, i) => (
                        <th key={i} className="text-left px-3 py-2 text-xs font-semibold"
                          style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {message.result.rows.map((row, ri) => (
                      <tr key={ri} style={{ borderBottom: "1px solid var(--border)" }}>
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-3 py-1.5 text-xs"
                            style={{ color: "var(--text-secondary)" }}>{String(cell)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
