const PREFIX = `xwing-rules-${self.registration.scope}-`;
const CACHE = `${PREFIX}__VERSION__`;
const PRECACHE = __PRECACHE__;
const root = new URL(self.registration.scope);

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(
    PRECACHE.map(path => new Request(new URL(path, root), { cache: 'reload' }))
  )));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name.startsWith(PREFIX) && name !== CACHE) await caches.delete(name);
    }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== root.origin ||
      !url.pathname.startsWith(root.pathname)) return;
  if (url.pathname === root.pathname) url.pathname += 'index.html';
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    return await cache.match(url.href, { ignoreSearch: true }) || fetch(event.request);
  })());
});
