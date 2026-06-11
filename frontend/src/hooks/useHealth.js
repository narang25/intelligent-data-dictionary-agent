import { useState, useEffect } from "react";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

export default function useHealth() {
  const [health, setHealth] = useState(null);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      const data = await res.json();
      setHealth(data);
    } catch {
      setHealth({
        status: "down",
      });
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return health;
}
