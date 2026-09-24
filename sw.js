// Offline support: keep the game and its sprites on the phone.
// Bump CACHE when shipping changes so phones drop the old copy.
const CACHE = 'rockfire-v3';
const ASSETS = [
  './',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './sprites/adult-bath.webp',
  './sprites/adult-fetch.webp',
  './sprites/adult-fire.webp',
  './sprites/adult-happy.webp',
  './sprites/adult-idle.webp',
  './sprites/adult-run.webp',
  './sprites/adult-sad.webp',
  './sprites/adult-sleep.webp',
  './sprites/baby-bath.webp',
  './sprites/baby-fetch.webp',
  './sprites/baby-fire.webp',
  './sprites/baby-happy.webp',
  './sprites/baby-idle.webp',
  './sprites/baby-run.webp',
  './sprites/baby-sad.webp',
  './sprites/baby-sleep.webp',
  './sprites/bed.webp',
  './sprites/bg-arena.webp',
  './sprites/bg-club.webp',
  './sprites/bg-garage.webp',
  './sprites/bone.webp',
  './sprites/egg-cracked.webp',
  './sprites/egg-hatch.webp',
  './sprites/egg-idle.webp',
  './sprites/food-coal.webp',
  './sprites/food-drink.webp',
  './sprites/food-pepper.webp',
  './sprites/food-pizza.webp',
  './sprites/teen-bath.webp',
  './sprites/teen-fetch.webp',
  './sprites/teen-fire.webp',
  './sprites/teen-happy.webp',
  './sprites/teen-idle.webp',
  './sprites/teen-run.webp',
  './sprites/teen-sad.webp',
  './sprites/teen-sleep.webp',
];

self.addEventListener('install', e => {
  // cache: 'reload' skips the browser's HTTP cache, so a new version never stores old files.
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(ASSETS.map(u => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Network first so updates show up right away; fall back to the cache offline.
// Our own files are revalidated with the server every time (a cheap 304 when unchanged),
// so the browser can't hand back a stale copy for up to 10 minutes after a deploy.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const own = new URL(e.request.url).origin === location.origin;
  e.respondWith(
    fetch(own ? new Request(e.request.url, { cache: 'no-cache', credentials: 'same-origin' }) : e.request)
      .then(res => {
        if (res.ok || res.type === 'opaque') {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true })
        .then(r => r || (e.request.mode === 'navigate' ? caches.match('./') : undefined)))
  );
});
