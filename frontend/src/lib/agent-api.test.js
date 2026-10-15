import assert from "node:assert/strict";
import test from "node:test";

import { askAgent } from "./agent-api.js";

test("askAgent sends the message and question id with the session cookie", async () => {
  const originalFetch = globalThis.fetch;
  let requestUrl;
  let requestOptions;
  globalThis.fetch = async (url, options) => {
    requestUrl = url;
    requestOptions = options;
    return { ok: true, json: async () => ({ reply: "Можно погулять в сквере." }) };
  };

  let reply;
  try {
    reply = await askAgent("marina", "Можно ли погулять после школы?", "yard");
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(reply, "Можно погулять в сквере.");
  assert.equal(requestUrl, "/api/agents/marina/chat");
  assert.equal(requestOptions.credentials, "include");
  assert.deepEqual(JSON.parse(requestOptions.body), {
    message: "Можно ли погулять после школы?",
    question_id: "yard",
  });
});
