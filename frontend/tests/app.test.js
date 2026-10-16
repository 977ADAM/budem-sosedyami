import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile } from "node:fs/promises";
import vm from "node:vm";
import { AGENTS } from "../agents.js";
import { createAgentApi, MAX_MESSAGE_LENGTH } from "../agent-api.js";

// Minimal DOM boundary for exercising the real event handlers and API client.
class Element {
  constructor() {
    this.children = [];
    this.handlers = {};
    this.dataset = {};
    this.classList = { add() {} };
    this.value = "";
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute() {}
  addEventListener(name, handler) { this.handlers[name] = handler; }
  focus() {}
}

async function openTab() {
  const elements = new Map();
  const requests = [];
  const source = (await readFile(new URL("../app.js", import.meta.url), "utf8"))
    .replace(/^import .*;$/gm, "");
  const context = vm.createContext({
    AGENTS, MAX_MESSAGE_LENGTH,
    createAgentApi: (options) => createAgentApi({ ...options, fetchImpl: async (_, options) => {
      const body = JSON.parse(options.body);
      requests.push(body);
      return new Response(JSON.stringify({reply: "Ответ", context: `ctx${requests.length}`}), {status: 200});
    }}),
    document: {
      querySelector: (selector) => {
        const element = new Element();
        elements.set(selector, element);
        return element;
      },
      createElement: () => new Element(),
    },
    window: {confirm: () => true},
  });
  vm.runInContext(source, context);
  return { elements, requests, async send(message) {
    elements.get("#message-input").value = message;
    await elements.get("#chat-form").handlers.submit({preventDefault() {}});
  }};
}

test("tab returns each neighbor's latest context; reset and reload start a new conversation", async () => {
  const tab = await openTab();
  assert.equal(tab.requests.length, 0);
  await tab.send("Первое");
  await tab.send("Второе");
  assert.deepEqual(tab.requests, [
    {message: "Первое"},
    {message: "Второе", context: "ctx1"},
  ]);
  tab.elements.get("#agent-list").children[1].children[0].handlers.click();
  await tab.send("Марина");
  assert.deepEqual(tab.requests[2], {message: "Марина"});
  tab.elements.get("#agent-list").children[0].children[0].handlers.click();
  await tab.send("Третье");
  assert.equal(tab.requests[3].context, "ctx2");
  tab.elements.get("#reset-button").handlers.click();
  assert.equal(tab.requests.length, 4);
  await tab.send("После очистки");
  assert.deepEqual(tab.requests[4], {message: "После очистки"});
  const reloaded = await openTab();
  await reloaded.send("После обновления");
  assert.deepEqual(reloaded.requests[0], {message: "После обновления"});
});
