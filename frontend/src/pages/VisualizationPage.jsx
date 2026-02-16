
import { useState } from "react";
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

export default function VisualizationPage() {
  const { chartData } = useVisualization();
  const navigate = useNavigate();
  const [chartType, setChartType] = useState("bar");

  if (!chartData) {
    return (
      <div className="p-10 text-white">
        No data available.
        <button
          onClick={() => navigate("/")}
          className="ml-4 bg-blue-600 px-3 py-1 rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  const columns = chartData.columns;
  const rows = chartData.rows;

  const numericIndex = columns.findIndex((_, colIndex) =>
    rows.every((row) => !isNaN(row[colIndex]))
  );

  if (numericIndex === -1) {
    return (
      <div className="p-10 text-white">
        No numeric column found for visualization.
        <button
          onClick={() => navigate("/")}
          className="ml-4 bg-blue-600 px-3 py-1 rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  const data = rows.map((row) => ({
    name: row[0],
    value: Number(row[numericIndex]),
  }));

  const COLORS = ["#6366F1", "#22D3EE", "#F472B6", "#34D399"];

  return (
    <div className="min-h-screen bg-neutral-900 text-white p-8">
      <h2 className="text-xl font-semibold mb-6">
        Data Visualization
      </h2>

      <div className="mb-6">
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          className="bg-neutral-800 px-4 py-2 rounded"
        >
          <option value="bar">Bar Chart</option>
          <option value="pie">Pie Chart</option>
          <option value="line">Line Chart</option>
        </select>
      </div>

      <div className="w-full h-[400px] bg-neutral-800 p-6 rounded-xl">
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
                outerRadius={120}
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

      <button
        onClick={() => navigate("/")}
        className="mt-6 bg-blue-600 px-4 py-2 rounded"
      >
        Back to Chat
      </button>
    </div>
  );
}
