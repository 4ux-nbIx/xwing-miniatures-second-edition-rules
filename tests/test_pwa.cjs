const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');
const vm = require('node:vm');

function worker(scope) {
  const handlers = {};
  const stored = new Map();
  const deleted = [];
  const cache = {
    async addAll(requests) { requests.forEach(r => stored.set(r.url, `cached:${r.url}`)); },
    async match(url) {
      const key = new URL(url);
      key.search = '';
      return stored.get(key.href);
    },
  };
  const context = {
    URL, Request,
    self: {
      registration: { scope },
      clients: { async claim() {} },
      addEventListener(name, handler) { handlers[name] = handler; },
    },
    caches: {
      async open() { return cache; },
      async keys() { return [`xwing-rules-${scope}-old`, 'unrelated-cache']; },
      async delete(name) { deleted.push(name); },
    },
    async fetch(request) { return `network:${request.url}`; },
  };
  const source = readFileSync('web/sw.js', 'utf8')
    .replace('__VERSION__', 'test-version')
    .replace('__PRECACHE__', JSON.stringify(['index.html', 'glossary/glossary-abilities.html']));
  vm.runInNewContext(source, context);
  return { handlers, stored, deleted };
}

for (const path of ['/', '/xwing-miniatures-second-edition-rules/']) {
  test(`offline routes and cache isolation at ${path}`, async () => {
    const scope = `https://example.com${path}`;
    const { handlers, stored, deleted } = worker(scope);
    let pending;
    handlers.install({ waitUntil(promise) { pending = promise; } });
    await pending;
    assert.ok(stored.has(`${scope}glossary/glossary-abilities.html`));
    handlers.activate({ waitUntil(promise) { pending = promise; } });
    await pending;
    assert.deepEqual(deleted, [`xwing-rules-${scope}-old`]);
    async function request(relative, method = 'GET') {
      let response;
      handlers.fetch({
        request: new Request(new URL(relative, scope), { method }),
        respondWith(promise) { response = promise; },
      });
      return response;
    }
    assert.equal(await request('./'), `cached:${scope}index.html`);
    assert.equal(await request('glossary/glossary-abilities.html?from=home'),
      `cached:${scope}glossary/glossary-abilities.html`);
    assert.equal(await request('source.pdf'), `network:${scope}source.pdf`);
    assert.equal(await request('https://other.example/'), undefined);
    assert.equal(await request('index.html', 'POST'), undefined);
    if (path !== '/') assert.equal(await request('/another-site/'), undefined);
  });
}

test('registration resolves from the script on nested rule pages', async () => {
  for (const protocol of ['https:', 'file:']) {
    let onLoad;
    let registration;
    vm.runInNewContext(readFileSync('web/pwa.js', 'utf8'), {
      URL,
      location: { protocol },
      document: { currentScript: { src: 'https://example.com/rules/pwa.js' } },
      window: { addEventListener(name, handler) { onLoad = handler; } },
      navigator: { serviceWorker: { async register(url) { registration = url.href; } } },
      console,
    });
    if (protocol === 'file:') assert.equal(onLoad, undefined);
    else {
      await onLoad();
      assert.equal(registration, 'https://example.com/rules/sw.js');
    }
  }
});
