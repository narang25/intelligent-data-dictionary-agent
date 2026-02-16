import Home from "./pages/Home";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import VisualizationPage from "./pages/VisualizationPage";

export default function App() {
  return (
    
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/visualize" element={<VisualizationPage />} />
      </Routes>
    
  );
}
