import { createContext, useContext, useState, useEffect } from "react";
import { listConnections } from "../services/api";

const ConnectionContext = createContext();

export function ConnectionProvider({ children }) {
  const [connections, setConnections] = useState([]);
  const [activeConnection, setActiveConnection] = useState(null);
  const [loading, setLoading] = useState(false);

  const refreshConnections = async () => {
    setLoading(true);
    try {
      const data = await listConnections();
      setConnections(data.connections || []);
      // Auto-select first if none active
      if (!activeConnection && data.connections?.length > 0) {
        setActiveConnection(data.connections[0]);
      }
    } catch (err) {
      console.error("Failed to load connections:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) refreshConnections();
  }, []);

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
