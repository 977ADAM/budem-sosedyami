/** Stateless API: the caller owns conversation history. */

import { AGENT_IDS } from "./agents.js";

export const MAX_MESSAGE_LENGTH = 500;

const STATUS_MESSAGES = {
  422: "Сообщение пустое или длиннее " + MAX_MESSAGE_LENGTH + " символов",
  502: "Сосед не ответил: ошибка обращения к модели (502)",
  503: "Модель не настроена: на backend нет DEEPSEEK_API_KEY (503)",
  504: "Модель не ответила вовремя (504)",
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function describeFailure(status, payload) {
  const detail = payload && typeof payload.detail === "string" ? payload.detail.trim() : "";
  const base = STATUS_MESSAGES[status] ?? `Backend ответил ошибкой ${status}`;
  return detail ? `${base} — ${detail}` : base;
}

function requireAgent(agentId) {
  if (!AGENT_IDS.has(agentId)) {
    throw new ApiError("Unknown agent", 0);
  }
}

export function createAgentApi({ fetchImpl = globalThis.fetch, baseUrl = "" } = {}) {
  if (typeof fetchImpl !== "function") {
    throw new Error("fetch is not available in this environment");
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetchImpl(`${baseUrl}${path}`, { ...options, credentials: "omit" });
    } catch (cause) {
      throw new ApiError(
        "Backend недоступен: проверь, запущен ли uvicorn на 127.0.0.1:8000",
        0,
        { cause },
      );
    }

    if (response.status === 204) {
      return null;
    }

    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }

    if (!response.ok) {
      throw new ApiError(describeFailure(response.status, payload), response.status);
    }
    return payload;
  }

  async function sendMessage(agentId, message, turns = []) {
    requireAgent(agentId);
    const text = String(message ?? "").trim();
    if (!text) {
      throw new ApiError("Сообщение пустое", 422);
    }
    if (text.length > MAX_MESSAGE_LENGTH) {
      throw new ApiError(`Сообщение длиннее ${MAX_MESSAGE_LENGTH} символов`, 422);
    }

    const history = turns
      .filter((turn) => !turn.pending && !turn.error && typeof turn.reply === "string" && turn.reply.trim())
      .slice(-100)
      .map(({ message, reply }) => ({ message, reply }));
    const data = await request(`/api/agents/${agentId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history }),
    });

    const reply = typeof data?.reply === "string" ? data.reply.trim() : "";
    if (!reply) {
      throw new ApiError("Сосед вернул пустой ответ", 502);
    }
    return reply;
  }

  return { sendMessage };
}
