import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import DashboardPage from "./pages/DashboardPage";
import TablesPage from "./pages/TablesPage";
import QualityPage from "./pages/QualityPage";
import ExportPage from "./pages/ExportPage";
import ConnectionsPage from "./pages/ConnectionsPage";
import VisualizationPage from "./pages/VisualizationPage";
import LineagePage from "./pages/LineagePage";
import Home from "./pages/Home";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" />;
}

function AppLayout({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* App routes inside Layout */}
      <Route path="/dashboard" element={<AppLayout><DashboardPage /></AppLayout>} />
      <Route path="/tables" element={<AppLayout><TablesPage /></AppLayout>} />
      <Route path="/quality" element={<AppLayout><QualityPage /></AppLayout>} />
      <Route path="/chat" element={<AppLayout><Home /></AppLayout>} />
      <Route path="/export" element={<AppLayout><ExportPage /></AppLayout>} />
      <Route path="/connections" element={<AppLayout><ConnectionsPage /></AppLayout>} />
      <Route path="/visualize" element={<AppLayout><VisualizationPage /></AppLayout>} />
      <Route path="/lineage" element={<AppLayout><LineagePage /></AppLayout>} />
    </Routes>
  );
}
