async function request(path, options) {
  const response = await fetch(path, { ...options, credentials: "include" });
  if (!response.ok) throw new Error(`Agent API request failed (${response.status})`);
  if (response.status === 204) return null;
  return response.json();
}

const agentIds = new Set(["anton", "marina", "pavel", "vera"]);

export async function startSession() {
  await request("/api/session", { method: "POST" });
}

export async function clearSession() {
  await request("/api/session", { method: "DELETE" });
  await startSession();
}

export async function getAgentHistory(agentId) {
  if (!agentIds.has(agentId)) throw new Error("Unknown agent");
  const data = await request(`/api/agents/${agentId}/history`);
  return Array.isArray(data.turns) ? data.turns : [];
}

export async function askAgent(agentId, message, questionId = null) {
  if (!agentIds.has(agentId)) throw new Error("Unknown agent");

  const data = await request(`/api/agents/${agentId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, question_id: questionId }),
  });
  if (typeof data.reply !== "string" || !data.reply.trim())
    throw new Error("Agent API returned an empty reply");
  return data.reply.trim();
}
