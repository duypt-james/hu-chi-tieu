self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => {
    caches.keys().then(n => n.forEach(k => caches.delete(k)));
    self.clients.claim();
});
self.addEventListener('fetch', () => {});
