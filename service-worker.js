/**
 * LoL Analytics S16 · Study Atlas — Service Worker
 * Provides offline caching so the app works without internet.
 * Strategy: Cache-first for assets, network-first for the main HTML.
 */

const CACHE_NAME = 'lol-analytics-v1.0';
const OFFLINE_URL = './LOL_Analytics_Study_Atlas_Master.html';

// Resources to pre-cache on install
const PRECACHE_ASSETS = [
  './LOL_Analytics_Study_Atlas_Master.html',
  './manifest.json',
  './assets/diagrams/enterprise_lifecycle.svg',
  './assets/diagrams/project_mapped_s16_lifecycle.svg',
];

// ── Install: pre-cache critical assets ───────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Pre-caching core assets');
      // Add one by one so a single 404 doesn't break everything
      return Promise.allSettled(
        PRECACHE_ASSETS.map(url =>
          cache.add(url).catch(err => console.warn('[SW] Failed to cache:', url, err))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// ── Activate: clean up old caches ────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME)
          .map(k => {
            console.log('[SW] Deleting old cache:', k);
            return caches.delete(k);
          })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: stale-while-revalidate for HTML, cache-first for assets ────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  const isMainDoc = request.destination === 'document' ||
                    url.pathname.endsWith('.html') ||
                    url.pathname === '/' ||
                    url.pathname === '';

  if (isMainDoc) {
    // Network-first for HTML: try network, fall back to cache
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
  } else {
    // Cache-first for static assets (SVG, images, icons)
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          }
          return response;
        }).catch(() => {
          console.warn('[SW] Fetch failed for:', request.url);
        });
      })
    );
  }
});

// ── Message: force-refresh on demand ─────────────────────────────────────────
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CACHE_CLEAR') {
    caches.delete(CACHE_NAME).then(() => {
      event.ports[0].postMessage({ cleared: true });
    });
  }
});
