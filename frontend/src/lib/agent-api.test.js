import assert from "node:assert/strict";
import test from "node:test";

import { askAgent } from "./agent-api.js";

test("askAgent sends free text and page-local message history to the selected agent", async () => {
  const originalFetch = globalThis.fetch;
  let requestUrl;
  let requestBody;
  globalThis.fetch = async (url, options) => {
    requestUrl = url;
    requestBody = JSON.parse(options.body);
    return { ok: true, json: async () => ({ reply: "Можно погулять в сквере." }) };
  };

  try {
    await askAgent("marina", "Можно ли погулять после школы?", [
      {
        message: "Как вы обычно идёте в школу?",
        reply: "Мы с дочкой идём пешком по спокойной улице.",
      },
    ]);
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(requestUrl, "/api/agents/marina/chat");
  assert.deepEqual(requestBody, {
    message: "Можно ли погулять после школы?",
    history: [
      {
        message: "Как вы обычно идёте в школу?",
        reply: "Мы с дочкой идём пешком по спокойной улице.",
      },
    ],
  });
});
