async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`Agent API request failed (${response.status})`);
  return response.json();
}

const agentIds = new Set(["anton", "marina", "pavel", "vera"]);

export async function askAgent(agentId, message, history) {
  if (!agentIds.has(agentId)) throw new Error("Unknown agent");

  const data = await request(`/api/agents/${agentId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (typeof data.reply !== "string" || !data.reply.trim())
    throw new Error("Agent API returned an empty reply");
  return data.reply.trim();
}
