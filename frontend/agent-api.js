/** Thin client: the backend owns history, validation and error texts. */

export const MAX_MESSAGE_LENGTH = 500;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function createAgentApi({ fetchImpl = globalThis.fetch, baseUrl = "" } = {}) {
  /** Returns `{ reply, context }`; pass `context` back to continue the conversation. */
  async function sendMessage(agentId, message, context = null) {
    let response;
    try {
      response = await fetchImpl(`${baseUrl}/api/agents/${encodeURIComponent(agentId)}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "omit",
        body: JSON.stringify(context ? { message, context } : { message }),
      });
    } catch {
      throw new ApiError("Сервер недоступен, попробуйте позже", 0);
    }

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(data?.detail ?? `Ошибка сервера (${response.status})`, response.status);
    }
    return { reply: data.reply, context: data.context };
  }

  return { sendMessage };
}
