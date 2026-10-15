async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`Agent API request failed (${response.status})`);
  return response.json();
}

export async function askAgent(agentId, questionId) {
  const data = await request("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent_id: agentId, question_id: questionId }),
  });
  if (typeof data.reply !== "string" || !data.reply.trim())
    throw new Error("Agent API returned an empty reply");
  return data.reply.trim();
}

export async function loadDialogue(agentId) {
  const data = await request(`/api/dialogue/${encodeURIComponent(agentId)}`);
  if (!data.answers || typeof data.answers !== "object" || Array.isArray(data.answers))
    throw new Error("Agent API returned an invalid dialogue");
  return data.answers;
}

export async function resetDialogues() {
  await request("/api/dialogue/reset", { method: "POST" });
}
