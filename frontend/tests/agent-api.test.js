import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, MAX_MESSAGE_LENGTH, createAgentApi } from "../agent-api.js";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function noContent() {
  return new Response(null, { status: 204 });
}

function recordingFetch(handler) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    calls.push({ url, options });
    return handler(url, options, calls.length);
  };
  return { calls, fetchImpl };
}

test("startSession posts to /api/session with credentials", async () => {
  const { calls, fetchImpl } = recordingFetch(() => noContent());
  const api = createAgentApi({ fetchImpl });

  assert.equal(await api.startSession(), null);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/session");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.credentials, "include");
});

test("baseUrl is prepended to every request", async () => {
  const { calls, fetchImpl } = recordingFetch(() => noContent());
  const api = createAgentApi({ fetchImpl, baseUrl: "http://127.0.0.1:8000" });

  await api.startSession();
  await api.getHistory("anton");

  assert.deepEqual(
    calls.map((call) => call.url),
    ["http://127.0.0.1:8000/api/session", "http://127.0.0.1:8000/api/agents/anton/history"],
  );
});

test("resetSession deletes the session and starts a fresh one", async () => {
  const { calls, fetchImpl } = recordingFetch(() => noContent());
  const api = createAgentApi({ fetchImpl });

  await api.resetSession();

  assert.deepEqual(
    calls.map((call) => [call.url, call.options.method]),
    [
      ["/api/session", "DELETE"],
      ["/api/session", "POST"],
    ],
  );
});

test("getHistory returns the turns reported by the backend", async () => {
  const turns = [
    { message: "Привет", reply: "Привет!", question_id: null },
  ];
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ turns }));
  const api = createAgentApi({ fetchImpl });

  assert.deepEqual(await api.getHistory("marina"), turns);
  assert.equal(calls[0].url, "/api/agents/marina/history");
  assert.equal(calls[0].options.credentials, "include");
});

test("getHistory tolerates a malformed payload", async () => {
  const { fetchImpl } = recordingFetch(() => jsonResponse({ turns: null }));
  const api = createAgentApi({ fetchImpl });

  assert.deepEqual(await api.getHistory("anton"), []);
});

test("unknown agent ids never reach the network", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "ok" }));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.getHistory("nobody"), /Unknown agent/);
  await assert.rejects(() => api.sendMessage("nobody", "Привет"), /Unknown agent/);
  assert.equal(calls.length, 0);
});

test("sendMessage posts the message with a null question id", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "  Ответ соседа.  " }));
  const api = createAgentApi({ fetchImpl });

  assert.equal(await api.sendMessage("pavel", "  Как добраться?  "), "Ответ соседа.");
  assert.equal(calls[0].url, "/api/agents/pavel/chat");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.credentials, "include");
  assert.equal(calls[0].options.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    message: "Как добраться?",
    question_id: null,
  });
});

test("sendMessage rejects blank and oversized messages without calling the backend", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "ok" }));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.sendMessage("vera", "   "), ApiError);
  await assert.rejects(
    () => api.sendMessage("vera", "а".repeat(MAX_MESSAGE_LENGTH + 1)),
    ApiError,
  );
  assert.equal(calls.length, 0);
});

test("sendMessage rejects an empty reply", async () => {
  const { fetchImpl } = recordingFetch(() => jsonResponse({ reply: "   " }));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.sendMessage("anton", "Привет"), /пустой ответ/);
});

test("sendMessage restarts the session once after a 401", async () => {
  let chatAttempts = 0;
  const { calls, fetchImpl } = recordingFetch((url) => {
    if (url.endsWith("/chat")) {
      chatAttempts += 1;
      return chatAttempts === 1 ? jsonResponse({ detail: "expired" }, 401) : jsonResponse({ reply: "Привет!" });
    }
    return noContent();
  });
  const api = createAgentApi({ fetchImpl });

  assert.equal(await api.sendMessage("anton", "Привет"), "Привет!");
  assert.deepEqual(
    calls.map((call) => call.url),
    ["/api/agents/anton/chat", "/api/session", "/api/agents/anton/chat"],
  );
});

test("upstream failures surface as ApiError with the status code", async () => {
  const { fetchImpl } = recordingFetch(() => jsonResponse({ detail: "DeepSeek request failed" }, 502));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(
    () => api.sendMessage("anton", "Привет"),
    (error) => error instanceof ApiError && error.status === 502 && /502/.test(error.message),
  );
});

test("an unreachable backend surfaces a readable ApiError", async () => {
  const { fetchImpl } = recordingFetch(() => {
    throw new TypeError("Failed to fetch");
  });
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.startSession(), /Backend недоступен/);
});
