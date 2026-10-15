import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, MAX_MESSAGE_LENGTH, createAgentApi } from "../agent-api.js";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function recordingFetch(handler) {
  const calls = [];
  const fetchImpl = async (url, options = {}) => {
    calls.push({ url, options });
    return handler(url, options, calls.length);
  };
  return { calls, fetchImpl };
}

test("unknown agent ids never reach the network", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "ok" }));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.sendMessage("nobody", "Привет"), /Unknown agent/);
  assert.equal(calls.length, 0);
});

test("sendMessage posts the message without cookies", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "  Ответ соседа.  " }));
  const api = createAgentApi({ fetchImpl });

  assert.equal(await api.sendMessage("pavel", "  Как добраться?  "), "Ответ соседа.");
  assert.equal(calls[0].url, "/api/agents/pavel/chat");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.credentials, "omit");
  assert.equal(calls[0].options.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    message: "Как добраться?",
    history: [],
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

test("sendMessage sends only completed turns and bounds context", async () => {
  const { calls, fetchImpl } = recordingFetch(() => jsonResponse({ reply: "ok" }));
  const api = createAgentApi({ fetchImpl, baseUrl: "http://127.0.0.1:8000" });
  const history = Array.from({length: 101}, (_, i) => ({message: String(i), reply: "ok"}));
  history.push({message: "failed", error: "offline"}, {message: "pending", pending: true});
  await api.sendMessage("anton", "Hi", history);
  const body = JSON.parse(calls[0].options.body);
  assert.equal(calls[0].url, "http://127.0.0.1:8000/api/agents/anton/chat");
  assert.equal(body.history.length, 100);
  assert.deepEqual(body.history[0], {message: "1", reply: "ok"});
  assert.deepEqual(body.history.at(-1), {message: "100", reply: "ok"});
  assert.equal(history.length, 103);
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

  await assert.rejects(() => api.sendMessage("anton", "Hi"), /Backend недоступен/);
});
