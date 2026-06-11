/* eslint-disable react-refresh/only-export-components */

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { listConnections } from "../services/api";

const ConnectionContext = createContext();

export function ConnectionProvider({ children }) {
  const [connections, setConnections] = useState([]);
  const [activeConnection, setActiveConnection] = useState(null);
  const [loading, setLoading] = useState(false);

  const refreshConnections = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listConnections();
      setConnections(data.connections || []);
      // Auto-select first if none active
      setActiveConnection((prev) => {
        if (!prev && data.connections?.length > 0) {
          return data.connections[0];
        }
        return prev;
      });
    } catch (err) {
      console.error("Failed to load connections:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) refreshConnections();

    // Re-fetch connections when user logs in
    const handleAuthChange = () => refreshConnections();
    window.addEventListener("auth-change", handleAuthChange);
    return () => window.removeEventListener("auth-change", handleAuthChange);
  }, [refreshConnections]);

  return (
    <ConnectionContext.Provider
      value={{
        connections,
        activeConnection,
        setActiveConnection,
        refreshConnections,
        loading,
      }}
    >
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  return useContext(ConnectionContext);
}
