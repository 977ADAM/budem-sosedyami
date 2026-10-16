import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, createAgentApi } from "../agent-api.js";

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

test("sendMessage posts the message and context without cookies", async () => {
  const { calls, fetchImpl } = recordingFetch(() =>
    jsonResponse({ reply: "Ответ соседа.", context: "ctx1" }),
  );
  const api = createAgentApi({ fetchImpl, baseUrl: "http://127.0.0.1:8000" });

  assert.deepEqual(await api.sendMessage("pavel", "Как добраться?"), {
    reply: "Ответ соседа.",
    context: "ctx1",
  });
  await api.sendMessage("pavel", "А потом?", "ctx1");

  assert.equal(calls[0].url, "http://127.0.0.1:8000/api/agents/pavel/chat");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.credentials, "omit");
  assert.equal(calls[0].options.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(calls[0].options.body), { message: "Как добраться?" });
  assert.deepEqual(JSON.parse(calls[1].options.body), { message: "А потом?", context: "ctx1" });
});

test("backend error detail is surfaced as is", async () => {
  const { fetchImpl } = recordingFetch(() => jsonResponse({ detail: "Неизвестный сосед" }, 422));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(
    () => api.sendMessage("nobody", "Привет"),
    (error) => error instanceof ApiError && error.status === 422 && error.message === "Неизвестный сосед",
  );
});

test("a non-JSON error still produces a readable ApiError", async () => {
  const { fetchImpl } = recordingFetch(() => new Response("Bad Gateway", { status: 502 }));
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.sendMessage("anton", "Привет"), /Ошибка сервера \(502\)/);
});

test("an unreachable backend surfaces a readable ApiError", async () => {
  const { fetchImpl } = recordingFetch(() => {
    throw new TypeError("Failed to fetch");
  });
  const api = createAgentApi({ fetchImpl });

  await assert.rejects(() => api.sendMessage("anton", "Hi"), /Сервер недоступен/);
});
