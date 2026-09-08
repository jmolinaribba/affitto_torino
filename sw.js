self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('affitto-store').then((cache) => cache.addAll([
      './',
      './index.html',
      './app.js',
      './criteria.js',
      './manifest.json',
      './data.json'
    ]))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});
