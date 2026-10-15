async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`Agent API request failed (${response.status})`);
  return response.json();
}

const agentChatPaths = Object.freeze({
  anton: "/api/agents/anton/chat",
  marina: "/api/agents/marina/chat",
  pavel: "/api/agents/pavel/chat",
  vera: "/api/agents/vera/chat",
});

export async function askAgent(agentId, questionId, history) {
  const path = agentChatPaths[agentId];
  if (!path) throw new Error("Unknown agent");

  const data = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question_id: questionId, history }),
  });
  if (typeof data.reply !== "string" || !data.reply.trim())
    throw new Error("Agent API returned an empty reply");
  return data.reply.trim();
}
