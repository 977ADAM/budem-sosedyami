const API_URL = "http://127.0.0.1:8000";
const contexts = {};
const form = document.querySelector("#chat-form");

function bubble(log, className, text) {
  const node = document.createElement("li");
  node.className = `bubble ${className}`;
  node.textContent = text;
  log.append(node);
  log.scrollTop = log.scrollHeight;
  return node;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const agent = form.agent.value;
  const message = form.message.value.trim();
  const log = document.querySelector(`#log-${agent}`);
  bubble(log, "from-user", message);
  const answer = bubble(log, "from-agent is-pending", "печатает…");
  form.message.value = "";
  form.send.disabled = true;

  try {
    const response = await fetch(`${API_URL}/api/agents/${agent}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, context: contexts[agent] }),
    });
    const data = await response.json().catch(() => ({ detail: `Ошибка сервера (${response.status})` }));
    if (!response.ok) throw new Error(data.detail);
    contexts[agent] = data.context;
    answer.className = "bubble from-agent";
    answer.textContent = data.reply;
  } catch (error) {
    answer.className = "bubble failure";
    answer.textContent = error instanceof TypeError ? "Сервер недоступен, попробуйте позже" : error.message;
    form.message.value = message;
  } finally {
    form.send.disabled = false;
    form.message.focus();
  }
});
