/**
 * PWA Service Worker
 * Handles app shell caching for offline reload capability
 *
 * @strategy
 * - App Shell (index.html): NetworkFirst with offline fallback
 * - Static Assets (JS/CSS with hash): CacheFirst (immutable)
 * - API Requests: NetworkOnly (never cache)
 * - HLS Segments (.m3u8, .ts): NetworkOnly (handled by IndexedDB in player)
 * - Version Check: NetworkOnly (always fresh)
 *
 * @important
 * This SW coordinates with existing HLS caching in player-hls-cache.ts
 * HLS requests are passed through to let IndexedDB handle them
 */

/// <reference lib="webworker" />

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import {
  NetworkFirst,
  CacheFirst,
  NetworkOnly,
  StaleWhileRevalidate,
} from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

declare let self: ServiceWorkerGlobalScope;

// Cache names
const CACHE_PREFIX = 'signage-player';
const STATIC_CACHE = `${CACHE_PREFIX}-static-v1`;
const RUNTIME_CACHE = `${CACHE_PREFIX}-runtime-v1`;

/**
 * Precache static assets injected by Vite PWA plugin
 * This will be replaced with actual asset list during build
 */
precacheAndRoute(self.__WB_MANIFEST || []);

/**
 * Clean up old caches from previous versions
 */
cleanupOutdatedCaches();

/**
 * Skip waiting and claim clients immediately
 * This ensures new SW takes over quickly
 */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

/**
 * Route: HLS Segments - PASS THROUGH
 * Let existing IndexedDB caching in player-hls-cache.ts handle these
 */
registerRoute(
  ({ url }) =>
    url.pathname.endsWith('.m3u8') ||
    url.pathname.endsWith('.ts') ||
    url.pathname.includes('/hls/'),
  new NetworkOnly()
);

/**
 * Route: API Requests - Network Only
 * Never cache API responses (they should be fresh)
 */
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkOnly()
);

/**
 * Route: Version Check - Network Only
 * Always get fresh version info
 */
registerRoute(
  ({ url }) => url.pathname.includes('version.json'),
  new NetworkOnly()
);

/**
 * Route: WebSocket - Skip (handled by browser)
 * SW cannot intercept WebSocket connections
 */

/**
 * Route: Hashed Static Assets - Cache First
 * Files with hash in name are immutable (e.g., main-abc123.js)
 */
registerRoute(
  ({ url }) => {
    // Match files with hash pattern: name-[hash].ext
    const hasHash = /\/assets\/.*-[a-f0-9]{8,}\.(js|css|woff2?|png|jpg|jpeg|svg|gif|ico)$/i.test(
      url.pathname
    );
    return hasHash;
  },
  new CacheFirst({
    cacheName: STATIC_CACHE,
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        purgeOnQuotaError: true,
      }),
    ],
  })
);

/**
 * Route: Non-hashed Static Assets - Stale While Revalidate
 * Get from cache first, update in background
 */
registerRoute(
  ({ url }) => {
    const isStaticAsset = /\.(png|jpg|jpeg|svg|gif|ico|woff2?|ttf|eot)$/i.test(
      url.pathname
    );
    const hasHash = /\/assets\/.*-[a-f0-9]{8,}\./i.test(url.pathname);
    return isStaticAsset && !hasHash;
  },
  new StaleWhileRevalidate({
    cacheName: RUNTIME_CACHE,
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        purgeOnQuotaError: true,
      }),
    ],
  })
);

/**
 * Route: Navigation Requests (HTML) - Network First with Offline Fallback
 * Try network first, fallback to cache, then offline page
 */
const navigationHandler = new NetworkFirst({
  cacheName: RUNTIME_CACHE,
  networkTimeoutSeconds: 5,
  plugins: [
    new CacheableResponsePlugin({
      statuses: [0, 200],
    }),
  ],
});

// Register navigation route with offline fallback
registerRoute(
  new NavigationRoute(navigationHandler, {
    // Don't handle menu routes differently - they're SPA routes
    allowlist: [/^\/$/], // Only root path
  })
);

// Fallback for navigation when offline
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          // Try to get from network
          const networkResponse = await fetch(event.request);
          return networkResponse;
        } catch (error) {
          // Network failed, try cache
          const cache = await caches.open(RUNTIME_CACHE);
          const cachedResponse = await cache.match(event.request);

          if (cachedResponse) {
            return cachedResponse;
          }

          // No cache, return offline page
          const offlineResponse = await cache.match('/offline.html');
          if (offlineResponse) {
            return offlineResponse;
          }

          // Fallback: return a basic offline response
          return new Response(
            '<html><body><h1>Offline</h1><p>No cached version available.</p></body></html>',
            {
              headers: { 'Content-Type': 'text/html' },
            }
          );
        }
      })()
    );
  }
});

/**
 * Handle install event - cache offline page
 */
self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(RUNTIME_CACHE);
      // Cache the offline page
      await cache.add('/offline.html');
      console.log('[PWA SW] Offline page cached');
    })()
  );
});

/**
 * Log SW lifecycle events for debugging
 */
console.log('[PWA SW] Service Worker loaded');
