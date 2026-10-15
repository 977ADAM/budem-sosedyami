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
      requests.push(JSON.parse(options.body));
      return new Response(JSON.stringify({reply: "Ответ"}), {status: 200});
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

test("tab owns separate neighbor histories; reset and reload discard them without network calls", async () => {
  const tab = await openTab();
  assert.equal(tab.requests.length, 0);
  await tab.send("Первое");
  await tab.send("Второе");
  assert.deepEqual(tab.requests[1].history, [{message: "Первое", reply: "Ответ"}]);
  const buttons = tab.elements.get("#agent-list").children;
  buttons[1].children[0].handlers.click();
  await tab.send("Марина");
  assert.deepEqual(tab.requests[2].history, []);
  tab.elements.get("#agent-list").children[0].children[0].handlers.click();
  await tab.send("Третье");
  assert.equal(tab.requests[3].history.length, 2);
  tab.elements.get("#reset-button").handlers.click();
  assert.equal(tab.requests.length, 4);
  await tab.send("После очистки");
  assert.deepEqual(tab.requests[4].history, []);
  const reloaded = await openTab();
  await reloaded.send("После обновления");
  assert.deepEqual(reloaded.requests[0].history, []);
});
