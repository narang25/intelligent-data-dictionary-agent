import { createContext, useContext, useState } from "react";

const VisualizationContext = createContext();

export function VisualizationProvider({ children }) {
  const [chartData, setChartData] = useState(null);

  return (
    <VisualizationContext.Provider value={{ chartData, setChartData }}>
      {children}
    </VisualizationContext.Provider>
  );
}

export function useVisualization() {
  const context = useContext(VisualizationContext);

  if (!context) {
    throw new Error(
      "useVisualization must be used inside VisualizationProvider"
    );
  }

  return context;
}
