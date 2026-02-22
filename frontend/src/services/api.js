// Use environment variable or fallback to localhost for development
// In production with nginx proxy, use relative path /api
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getHeaders() {
  const token = localStorage.getItem("token");

  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

export async function signupUser(email, password) {
  const res = await fetch(`${BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);
  return data;
}

export async function loginUser(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);
  return data;
}

export async function sendMessageToAPI(question, sessionId = null) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail);
  return data;
}
