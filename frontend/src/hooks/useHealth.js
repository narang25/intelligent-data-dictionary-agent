import { useState, useEffect } from "react";

const BASE_URL = "http://localhost:8000";

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
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return health;
}
