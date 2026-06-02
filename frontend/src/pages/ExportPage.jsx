import { useState } from "react";
import { useConnection } from "../context/ConnectionContext";
import { createExport, previewExport, getExportDownloadUrl } from "../services/api";

export default function ExportPage() {
  const { activeConnection } = useConnection();
  const [format, setFormat] = useState("json");
  const [preview, setPreview] = useState(null);
  const [exportResult, setExportResult] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingExport, setLoadingExport] = useState(false);

  const handlePreview = async () => {
    setLoadingPreview(true);
    try { setPreview(await previewExport(activeConnection.id, format)); }
    catch (err) { console.error(err); }
    finally { setLoadingPreview(false); }
  };

  const handleExport = async () => {
    setLoadingExport(true);
    try { setExportResult(await createExport(activeConnection.id, format)); }
    catch (err) { console.error(err); }
    finally { setLoadingExport(false); }
  };

  if (!activeConnection) {
    return <div className="flex items-center justify-center h-[80vh]" style={{ color: "var(--text-muted)" }}>Connect a database to export.</div>;
  }

  const formats = [
    { value: "json", label: "JSON", desc: "Structured data dictionary" },
    { value: "markdown", label: "Markdown", desc: "Documentation format" },
    { value: "html", label: "HTML", desc: "Styled web report" },
  ];

  return (
    <div className="space-y-5 max-w-2xl mx-auto">
      <div>
        <h1 className="text-xl font-bold" style={{ color: "var(--text-bright)" }}>Export</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Generate a data dictionary for {activeConnection.name}</p>
      </div>

      {/* Format toggle — radio-style */}
      <div className="card p-4 rise">
        <h3 className="text-[10px] font-bold uppercase tracking-wider mb-3" style={{ color: "var(--text-muted)" }}>Format</h3>
        <div className="flex gap-2">
          {formats.map(f => (
            <button key={f.value} onClick={() => setFormat(f.value)}
              className="flex-1 text-left p-3 rounded-lg transition-all duration-150"
              style={{
                background: format === f.value ? "var(--accent-glow)" : "var(--bg-surface)",
                border: format === f.value ? "1px solid var(--border-active)" : "1px solid var(--border)",
              }}>
              <p className="text-sm font-semibold" style={{ color: format === f.value ? "var(--accent)" : "var(--text-secondary)" }}>{f.label}</p>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{f.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={handlePreview} disabled={loadingPreview} className="btn-ghost">
          {loadingPreview ? <><div className="spinner"></div> Loading...</> : "Preview Raw Data"}
        </button>
        <button onClick={handleExport} disabled={loadingExport} className="btn-accent">
          {loadingExport ? <><div className="spinner"></div> Generating...</> : `Export ${format.toUpperCase()}`}
        </button>
      </div>

      {/* Export result */}
      {exportResult && (
        <div className="card p-4 rise" style={{ borderColor: "rgba(45,212,168,0.2)" }}>
          <p className="text-xs font-semibold" style={{ color: "var(--teal)" }}>✓ Export generated</p>
          <p className="text-[10px] mono mt-0.5" style={{ color: "var(--text-muted)" }}>Job: {exportResult.job_id}</p>
          <a href={getExportDownloadUrl(exportResult.job_id)} target="_blank" rel="noopener noreferrer" className="btn-accent mt-3 inline-flex" style={{ fontSize: 11 }}>
            Download
          </a>
        </div>
      )}

      {/* Preview */}
      {preview && (
        <div className="card overflow-hidden rise">
          <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
            <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              {preview.format === 'json' ? "Raw Output (Native JSON Metadata)" : `Preview (${preview.format.toUpperCase()})`}
            </span>
          </div>
          <div className="max-h-[350px] overflow-auto p-4" style={{ background: "var(--bg-surface)", padding: preview.format === 'html' ? 0 : '1rem' }}>
            {preview.format === 'html' ? (
              <iframe 
                srcDoc={preview.preview} 
                className="w-full h-[350px] border-none bg-white"
                title="HTML Preview"
              />
            ) : preview.format === 'markdown' ? (
              <pre className="text-[10px] mono leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>
                {preview.preview}
              </pre>
            ) : (
              <pre className="text-[10px] mono leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>
                {JSON.stringify(preview.preview, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
