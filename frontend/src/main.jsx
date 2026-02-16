import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { VisualizationProvider } from "./context/VisualizationContext";
import { ChatProvider } from "./context/ChatContext";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <VisualizationProvider>
        <ChatProvider>
          <App />
        </ChatProvider>
      </VisualizationProvider>
    </BrowserRouter>
  </StrictMode>
);
