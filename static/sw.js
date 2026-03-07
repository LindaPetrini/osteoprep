const CACHE_NAME = 'osteoprep-v2';
const STATIC_CACHE = 'osteoprep-static-v2';

const PRECACHE_URLS = [
  '/',
  '/static/htmx.min.js',
  '/static/app.js',
  '/static/tailwind.min.css',
  '/static/daisyui.min.css',
  '/static/icon-192.png',
  '/static/icon-512.png',
];

// Endpoints that should never be cached
const SKIP_PATTERNS = [
  '/chat/',
  '/generate',
  '/search',
  '/sw.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME && key !== STATIC_CACHE)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip HTMX partial requests (fragments, not full pages)
  if (event.request.headers.get('HX-Request') === 'true') return;

  // Skip API/dynamic endpoints
  if (SKIP_PATTERNS.some(p => url.pathname.includes(p))) return;

  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then(cache => cache.put(event.request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages: network-first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
