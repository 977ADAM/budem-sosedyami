/**
 * Состояние и рендер простого чата поверх локального FastAPI backend.
 *
 * Сервер владеет историей диалогов, поэтому UI только показывает ответы,
 * которые вернул backend, и не отправляет прошлые реплики.
 */

import { MAX_MESSAGE_LENGTH, createAgentApi } from "./agent-api.js";
import { AGENTS } from "./agents.js";

/**
 * Статика отдаётся с 127.0.0.1:3000, backend живёт на 127.0.0.1:8000 — это
 * ровно тот origin, который backend разрешает в CORS. Относительные пути
 * ушли бы на статический сервер, поэтому адрес backend задан явно.
 */
const API_BASE_URL = "http://127.0.0.1:8000";

const api = createAgentApi({ baseUrl: API_BASE_URL });

const elements = {
  agentList: document.querySelector("#agent-list"),
  log: document.querySelector("#chat-log"),
  form: document.querySelector("#chat-form"),
  input: document.querySelector("#message-input"),
  send: document.querySelector("#send-button"),
  reset: document.querySelector("#reset-button"),
  status: document.querySelector("#status"),
  counter: document.querySelector("#counter"),
};

const state = {
  agentId: AGENTS[0].id,
  turns: new Map(AGENTS.map((agent) => [agent.id, []])),
  hydrated: new Set(),
  pending: false,
};

function agentById(agentId) {
  return AGENTS.find((agent) => agent.id === agentId);
}

function setStatus(message, kind = "info") {
  elements.status.textContent = message;
  elements.status.dataset.kind = kind;
}

function setPending(pending) {
  state.pending = pending;
  elements.send.disabled = pending;
  elements.reset.disabled = pending;
  elements.input.disabled = pending;
}

function updateCounter() {
  elements.counter.textContent = `${elements.input.value.length}/${MAX_MESSAGE_LENGTH}`;
}

function renderAgentList() {
  elements.agentList.replaceChildren();
  for (const agent of AGENTS) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    const isCurrent = agent.id === state.agentId;

    button.type = "button";
    button.className = "agent";
    button.dataset.agentId = agent.id;
    button.setAttribute("aria-pressed", String(isCurrent));
    if (isCurrent) button.classList.add("is-current");

    const name = document.createElement("span");
    name.className = "agent-name";
    name.textContent = agent.name;

    const tagline = document.createElement("span");
    tagline.className = "agent-tagline";
    tagline.textContent = agent.tagline;

    button.append(name, tagline);
    button.addEventListener("click", () => selectAgent(agent.id));
    item.append(button);
    elements.agentList.append(item);
  }
}

function bubble(className, text) {
  const node = document.createElement("p");
  node.className = `bubble ${className}`;
  node.textContent = text;
  return node;
}

function renderLog() {
  const turns = state.turns.get(state.agentId) ?? [];
  elements.log.replaceChildren();

  if (turns.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = `Пока пусто. Задай вопрос — ${agentById(state.agentId).name} ответит по своей выдуманной истории.`;
    elements.log.append(empty);
  }

  for (const turn of turns) {
    const item = document.createElement("li");
    item.className = "turn";
    item.append(bubble("from-user", turn.message));

    if (turn.pending) {
      item.append(bubble("from-agent is-pending", "печатает…"));
    } else if (turn.error) {
      item.append(bubble("failure", turn.error));
    } else {
      item.append(bubble("from-agent", turn.reply));
    }

    elements.log.append(item);
  }

  elements.log.scrollTop = elements.log.scrollHeight;
}

async function selectAgent(agentId) {
  if (agentId === state.agentId) return;
  state.agentId = agentId;
  renderAgentList();
  renderLog();
  await loadHistory(agentId);
}

async function loadHistory(agentId) {
  if (state.hydrated.has(agentId)) return;
  try {
    const turns = await api.getHistory(agentId);
    state.turns.set(agentId, turns);
    state.hydrated.add(agentId);
    if (agentId === state.agentId) renderLog();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function onSubmit(event) {
  event.preventDefault();
  if (state.pending) return;

  const text = elements.input.value.trim();
  if (!text) return;

  const agentId = state.agentId;
  const turns = state.turns.get(agentId) ?? [];
  state.turns.set(agentId, turns);

  elements.input.value = "";
  updateCounter();
  turns.push({ message: text, pending: true });
  renderLog();
  setPending(true);
  setStatus("Сосед печатает…");

  try {
    const reply = await api.sendMessage(agentId, text);
    turns[turns.length - 1] = { message: text, reply };
    setStatus("");
  } catch (error) {
    turns[turns.length - 1] = { message: text, error: error.message };
    elements.input.value = text;
    updateCounter();
    setStatus("");
  } finally {
    setPending(false);
    if (agentId === state.agentId) renderLog();
    elements.input.focus();
  }
}

async function onReset() {
  if (state.pending) return;
  if (!window.confirm("Сбросить сессию? Все диалоги с соседями будут удалены.")) return;

  setPending(true);
  setStatus("Сбрасываю сессию…");
  try {
    await api.resetSession();
    for (const agentId of state.turns.keys()) state.turns.set(agentId, []);
    state.hydrated.clear();
    state.hydrated.add(state.agentId);
    renderLog();
    setStatus("Сессия сброшена", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    setPending(false);
  }
}

async function boot() {
  elements.input.maxLength = MAX_MESSAGE_LENGTH;
  updateCounter();
  renderAgentList();
  renderLog();

  elements.form.addEventListener("submit", onSubmit);
  elements.reset.addEventListener("click", onReset);
  elements.input.addEventListener("input", updateCounter);

  setStatus("Подключаюсь к backend…");
  try {
    await api.startSession();
    setStatus("");
  } catch (error) {
    setStatus(error.message, "error");
  }

  await loadHistory(state.agentId);
  elements.input.focus();
}

boot();
