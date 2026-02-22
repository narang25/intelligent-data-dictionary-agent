import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { VisualizationProvider } from "./context/VisualizationContext";
import { ChatProvider } from "./context/ChatContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <VisualizationProvider>
          <ChatProvider>
            <App />
          </ChatProvider>
        </VisualizationProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
