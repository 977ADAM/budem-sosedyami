const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const source = readFileSync(require('node:path').join(__dirname, '../app.js'), 'utf8');

function setup(fetch) {
  let submit;
  const logs = Object.fromEntries(['anton', 'marina', 'pavel', 'vera'].map(id => [id, {
    children: [], append(node) { this.children.push(node); },
  }]));
  const form = {
    agent: {value: 'anton'}, message: {value: 'Привет', focus() {}}, send: {disabled: false},
    addEventListener(name, callback) { submit = callback; },
  };
  vm.runInNewContext(source, {
    document: {
      querySelector(selector) { return selector === '#chat-form' ? form : logs[selector.slice(5)]; },
      createElement() { return {}; },
    },
    location: {hostname: 'dev.coresmart.tech', port: ''}, fetch, TypeError,
  }, {filename: require('node:path').join(__dirname, '../app.js')});
  return {form, logs, submit: () => submit({preventDefault() {}})};
}
const ok = (reply = 'Ответ', context = 'token') => ({ok: true, status: 200, json: async () => ({reply, context})});

test('blank message never sends a request or adds bubbles', async () => {
  let calls = 0;
  const app = setup(async () => { calls++; return ok(); });
  app.form.message.value = '   ';
  await app.submit();
  assert.equal(calls, 0);
  assert.equal(app.logs.anton.children.length, 0);
});

test('network failure preserves the message and enables send', async () => {
  const app = setup(async () => { throw new TypeError('offline'); });
  await app.submit();
  assert.equal(app.form.message.value, 'Привет');
  assert.equal(app.form.send.disabled, false);
  assert.equal(app.logs.anton.children.at(-1).textContent, 'Сервер недоступен, попробуйте позже');
});

test('malformed successful responses preserve the last valid context', async () => {
  const payloads = [];
  let response = ok();
  const app = setup(async (url, options) => { payloads.push(JSON.parse(options.body)); return response; });
  await app.submit();
  for (const body of [null, {}, {reply: 'Ответ'}, {reply: '', context: 'new-token'}]) {
    response = {ok: true, status: 200, json: async () => body};
    app.form.message.value = 'Повтор';
    await app.submit();
    assert.equal(app.form.message.value, 'Повтор');
    assert.equal(app.logs.anton.children.at(-1).textContent, 'API вернул некорректный ответ');
  }
  assert.equal(payloads.at(-1).context, 'token');
});

test('invalid JSON is a readable error and preserves the message', async () => {
  const app = setup(async () => ({ok: true, status: 200, json: async () => { throw new SyntaxError(); }}));
  await app.submit();
  assert.equal(app.form.message.value, 'Привет');
  assert.equal(app.logs.anton.children.at(-1).textContent, 'API вернул некорректный ответ');
});

test('HTTP failure without string detail displays its status', async () => {
  const app = setup(async () => ({ok: false, status: 502, json: async () => ({detail: []})}));
  await app.submit();
  assert.equal(app.logs.anton.children.at(-1).textContent, 'Ошибка сервера (502)');
});

test('pending submit cannot send a second request', async () => {
  let calls = 0, resolve;
  const pending = new Promise(done => { resolve = done; });
  const app = setup(() => { calls++; return pending; });
  const first = app.submit();
  app.form.message.value = 'Ещё';
  const second = app.submit();
  resolve(ok());
  await Promise.all([first, second]);
  assert.equal(calls, 1);
});

test('contexts are separate for each neighbor', async () => {
  const sent = [];
  const app = setup(async (url, options) => {
    sent.push(JSON.parse(options.body));
    return ok('Ответ', url.includes('marina') ? 'marina-token' : 'anton-token');
  });
  await app.submit();
  app.form.agent.value = 'marina'; app.form.message.value = 'Привет'; await app.submit();
  app.form.agent.value = 'anton'; app.form.message.value = 'Ещё'; await app.submit();
  assert.equal(sent[1].context, undefined);
  assert.equal(sent[2].context, 'anton-token');
});
