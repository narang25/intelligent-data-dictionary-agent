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
    const text = await response.text();
    console.error("API Error:", text);
    throw new Error("Failed to fetch response from server");
  }

  return await response.json();
}
