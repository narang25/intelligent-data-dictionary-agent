import { useState } from "react";
import { useVisualization } from "../../context/VisualizationContext";
import { useNavigate } from "react-router-dom";

export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";
  const navigate = useNavigate();
  const { setChartData } = useVisualization();

  const [copied, setCopied] = useState(false);

  const copySQL = async () => {
    if (!message.sql) return;

    try {
      await navigator.clipboard.writeText(message.sql);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);

    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  const exportCSV = () => {
    if (!message.result?.columns) return;

    const headers = message.result.columns.join(",");
    const rows = message.result.rows
      .map((row) => row.join(","))
      .join("\n");

    const csvContent = headers + "\n" + rows;

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "query_result.csv";
    link.click();
  };

  const generateChart = () => {
    if (!message.result?.columns) return;

    setChartData(message.result);
    navigate("/visualize");
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} w-full`}>
      <div
        className={`px-4 py-3 rounded-xl max-w-[80%] text-sm whitespace-pre-wrap break-words overflow-hidden ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-neutral-800 text-neutral-200"
        }`}
      >
        {!isUser && message.mode && (
          <div className="text-xs mb-2 opacity-60 uppercase tracking-wide">
            {message.mode}
          </div>
        )}

        <div className="break-words overflow-wrap-anywhere">{message.text}</div>

        {!isUser && message.mode === "sql" && message.sql && (
          <div className="mt-4 space-y-4">

            {/* SQL Block */}
            <div className="bg-black text-green-400 p-3 rounded-lg text-xs overflow-x-auto relative">
              <div className="flex justify-between items-center mb-2">
                <div className="text-white font-semibold">
                  SQL Query
                </div>

                <button
                  onClick={copySQL}
                  className={`text-xs px-2 py-1 rounded transition ${
                    copied
                      ? "bg-green-600 text-white"
                      : "bg-neutral-700 hover:bg-neutral-600"
                  }`}
                >
                  {copied ? "Copied ✓" : "Copy"}
                </button>
              </div>

              <pre>{message.sql}</pre>
            </div>

            {/* Explanation */}
            {message.explanation && (
              <div className="bg-neutral-700 p-3 rounded-lg text-xs">
                <div className="font-semibold mb-1">
                  Explanation
                </div>
                {message.explanation}
              </div>
            )}

            {/* Result Table */}
            {message.result?.columns && (
              <div className="overflow-x-auto">

                <div className="flex justify-between items-center mb-2">
                  <div className="text-xs font-semibold">
                    Query Result
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={exportCSV}
                      className="text-xs bg-neutral-700 px-2 py-1 rounded hover:bg-neutral-600 transition"
                    >
                      Export CSV
                    </button>

                    <button
                      onClick={generateChart}
                      className="text-xs bg-blue-600 px-2 py-1 rounded hover:bg-blue-500 transition"
                    >
                      Generate Chart
                    </button>
                  </div>
                </div>

                <table className="text-xs border border-neutral-700 w-full">
                  <thead>
                    <tr className="bg-neutral-900">
                      {message.result.columns.map((col, idx) => (
                        <th
                          key={idx}
                          className="border border-neutral-700 px-3 py-2 text-left"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {message.result.rows.map((row, rIndex) => (
                      <tr key={rIndex} className="hover:bg-neutral-700/50">
                        {row.map((cell, cIndex) => (
                          <td
                            key={cIndex}
                            className="border border-neutral-700 px-3 py-2"
                          >
                            {String(cell)}
                          </td>
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
