import { useState, useMemo, useRef, useEffect } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useVisualization } from "../context/VisualizationContext";
import { useNavigate } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export default function VisualizationPage() {
  const { chartData } = useVisualization();
  const navigate = useNavigate();
  const chartRef = useRef(null);

  const [chartType, setChartType] = useState("bar");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");

  const columns = useMemo(() => chartData?.columns || [], [chartData]);
  const rows = useMemo(() => chartData?.rows || [], [chartData]);

  // Detect numeric columns
  const numericColumns = useMemo(() => {
    if (!columns.length) return [];
    return columns.filter((_, colIndex) =>
      rows.every((row) => !isNaN(row[colIndex]))
    );
  }, [columns, rows]);

  // Smart auto setup
  useEffect(() => {
    if (!columns.length || !rows.length) return;

    const numericIndex = columns.findIndex((_, i) =>
      rows.every((row) => !isNaN(row[i]))
    );

    if (numericIndex === -1) return;

    const firstColIndex = 0;
    const isDateColumn = rows.every((row) => !isNaN(Date.parse(row[firstColIndex])));

    if (isDateColumn) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setChartType("line");
    } else if (rows.length <= 8) {
      setChartType("pie");
    } else {
      setChartType("bar");
    }

    setXColumn(columns[firstColIndex]);
    setYColumn(columns[numericIndex]);
  }, [columns, rows]);

  if (!chartData) {
    return (
      <div className="p-10 text-primary bg-primary min-h-screen">
        No data available.
        <button
          onClick={() => navigate("/chat")}
          className="ml-4 bg-blue-600 text-white px-3 py-1 rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!numericColumns.length) {
    return (
      <div className="p-10 text-primary bg-primary min-h-screen">
        No numeric column found.
        <button
          onClick={() => navigate("/chat")}
          className="ml-4 bg-blue-600 text-white px-3 py-1 rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  const xIndex = columns.indexOf(xColumn);
  const yIndex = columns.indexOf(yColumn);

  const data = rows.map((row) => ({
    name: row[xIndex],
    value: Number(row[yIndex]),
  }));

  const COLORS = ["#6366F1", "#22D3EE", "#F472B6", "#34D399"];

  // =========================
  // CLEAN EXPORT CONTAINER
  // =========================
  const downloadPNG = async () => {
    const canvas = await html2canvas(chartRef.current, {
      backgroundColor: "#ffffff",
      scale: 2, // higher quality
    });

    const link = document.createElement("a");
    link.download = "chart.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  const downloadPDF = async () => {
    const canvas = await html2canvas(chartRef.current, {
      backgroundColor: "#ffffff",
      scale: 2,
    });

    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("landscape");
    const imgWidth = 280;
    const imgHeight =
      (canvas.height * imgWidth) / canvas.width;

    pdf.addImage(imgData, "PNG", 10, 10, imgWidth, imgHeight);
    pdf.save("chart.pdf");
  };

  return (
    <div className="min-h-screen bg-primary text-primary p-8">

      <h2 className="text-xl font-semibold mb-2">
        Data Visualization
      </h2>

      <div className="mb-4 text-sm text-accent">
        💡 Suggested Chart: {chartType.toUpperCase()}
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">

        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          className="bg-surface text-primary px-4 py-2 rounded border border-primary"
        >
          <option value="bar">Bar</option>
          <option value="line">Line</option>
          <option value="pie">Pie</option>
        </select>

        <select
          value={xColumn}
          onChange={(e) => setXColumn(e.target.value)}
          className="bg-surface text-primary px-4 py-2 rounded border border-primary"
        >
          {columns.map((col) => (
            <option key={col} value={col}>
              X: {col}
            </option>
          ))}
        </select>

        <select
          value={yColumn}
          onChange={(e) => setYColumn(e.target.value)}
          className="bg-surface text-primary px-4 py-2 rounded border border-primary"
        >
          {numericColumns.map((col) => (
            <option key={col} value={col}>
              Y: {col}
            </option>
          ))}
        </select>

        <div className="flex gap-2">
          <button
            onClick={downloadPNG}
            className="bg-green-600 text-white px-3 py-2 rounded text-xs"
          >
            Download PNG
          </button>

          <button
            onClick={downloadPDF}
            className="bg-purple-600 text-white px-3 py-2 rounded text-xs"
          >
            Download PDF
          </button>
        </div>
      </div>

      {/* EXPORT SAFE WRAPPER */}
      <div
        style={{
          backgroundColor: "#ffffff",
          padding: "24px",
          borderRadius: "12px",
        }}
      >
        <div
          ref={chartRef}
          style={{ width: "100%", height: "450px" }}
        >
          <ResponsiveContainer>
            {chartType === "bar" && (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366F1" />
              </BarChart>
            )}

            {chartType === "line" && (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#22D3EE" />
              </LineChart>
            )}

            {chartType === "pie" && (
              <PieChart>
                <Tooltip />
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={130}
                >
                  {data.map((_, index) => (
                    <Cell
                      key={index}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
              </PieChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      <button
        onClick={() => navigate("/chat")}
        className="mt-6 bg-blue-600 text-white px-4 py-2 rounded"
      >
        Back to Chat
      </button>
    </div>
  );
}
