const BASE_URL = "http://localhost:8000";

export async function sendMessageToAPI(question, sessionId = null) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch response");
  }

  return await response.json();
}
