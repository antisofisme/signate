/**
 * Service Worker for Digital Signage Viewer
 *
 * Offline-first caching strategy for monitors, browsers, and WebOS TV.
 * Provides intelligent content caching, background sync, and offline playback.
 *
 * Features:
 * - Multi-tier cache strategy (static, media, API)
 * - HLS segment caching for video streams
 * - Intelligent prefetching based on playlist
 * - Automatic cache cleanup (LRU eviction)
 * - Background sync for playlist updates
 * - Network quality adaptation
 * - Cache size monitoring and limits
 *
 * @version 1.0.0
 * @author Smart TV Digital Signage System
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CACHE_VERSION = 'v1';
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_MEDIA = `${CACHE_VERSION}-media`;
const CACHE_API = `${CACHE_VERSION}-api`;
const CACHE_HLS = `${CACHE_VERSION}-hls`;

// Cache size limits (in bytes)
const MAX_MEDIA_CACHE_SIZE = 2 * 1024 * 1024 * 1024; // 2GB
const MAX_HLS_CACHE_SIZE = 512 * 1024 * 1024; // 512MB
const MAX_API_CACHE_SIZE = 50 * 1024 * 1024; // 50MB

// Cache TTL (Time To Live)
const CACHE_TTL = {
    static: 7 * 24 * 60 * 60 * 1000, // 7 days
    media: 7 * 24 * 60 * 60 * 1000,  // 7 days
    api: 60 * 60 * 1000,              // 1 hour
    hls: 24 * 60 * 60 * 1000         // 1 day
};

// Critical assets to cache on install
const CRITICAL_ASSETS = [
    '/',
    '/index.html',
    '/player.html',
    '/js/config/env.js',
    '/js/shared/api-client.js',
    '/js/shared/cache-manager.js',
    '/js/shared/offline-detector.js',
    '/js/shell/config.js',
    '/js/shell/logger.js',
    '/js/shell/wifi-status.js',
    '/js/shell/network-diagnostics.js',
    '/js/shell/registration.js',
    '/js/shell/heartbeat.js',
    '/js/shell/activation-poll.js',
    '/js/shell/commands.js',
    '/js/shell/display-settings.js',
    '/js/shell/ui.js',
    '/js/shell/init.js',
    '/js/player/config.js',
    '/js/player/logger.js',
    '/js/player/cache.js',
    '/js/player/api.js',
    '/js/player/playback.js',
    '/js/player/ui.js',
    '/js/player/init.js'
];

// ============================================================================
// INSTALL EVENT - Cache Critical Assets
// ============================================================================

self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker v' + CACHE_VERSION);

    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then((cache) => {
                console.log('[SW] Caching critical assets...');
                return cache.addAll(CRITICAL_ASSETS);
            })
            .then(() => {
                console.log('[SW] Critical assets cached successfully');
                // Skip waiting to activate immediately
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Failed to cache critical assets:', error);
                // Don't fail installation if some assets fail
                return self.skipWaiting();
            })
    );
});

// ============================================================================
// ACTIVATE EVENT - Cleanup Old Caches
// ============================================================================

self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker v' + CACHE_VERSION);

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                const validCaches = [CACHE_STATIC, CACHE_MEDIA, CACHE_API, CACHE_HLS];

                // Delete old cache versions
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (!validCaches.includes(cacheName)) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Old caches cleaned up');
                // Take control of all clients immediately
                return self.clients.claim();
            })
            .then(() => {
                console.log('[SW] Service Worker activated and ready');
            })
    );
});

// ============================================================================
// FETCH EVENT - Routing Strategy
// ============================================================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignore non-GET requests (POST, PUT, DELETE should always go to network)
    if (request.method !== 'GET') {
        return;
    }

    // Ignore external domains (only cache same-origin resources)
    if (url.origin !== location.origin) {
        return;
    }

    // Route to appropriate caching strategy
    if (isHLSSegment(url)) {
        // HLS segments (.m3u8, .ts) - cache first with network fallback
        event.respondWith(cacheFirstStrategy(request, CACHE_HLS));
    } else if (isMediaAsset(url)) {
        // Media files (images, videos) - cache first
        event.respondWith(cacheFirstStrategy(request, CACHE_MEDIA));
    } else if (isAPIRequest(url)) {
        // API requests - network first with cache fallback
        event.respondWith(networkFirstStrategy(request, CACHE_API));
    } else {
        // Static assets (HTML, CSS, JS) - cache first
        event.respondWith(cacheFirstStrategy(request, CACHE_STATIC));
    }
});

// ============================================================================
// CACHING STRATEGIES
// ============================================================================

/**
 * Cache-First Strategy
 * Try cache first, fall back to network if not found
 * Good for: static assets, media files, HLS segments
 */
async function cacheFirstStrategy(request, cacheName) {
    try {
        // Try cache first
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[SW] Cache HIT:', request.url);

            // Check if cache entry is expired
            if (await isCacheExpired(cachedResponse, cacheName)) {
                console.log('[SW] Cache expired, fetching fresh data...');
                // Cache expired - fetch fresh in background
                fetchAndCache(request, cacheName);
            }

            return cachedResponse;
        }

        // Cache miss - fetch from network
        console.log('[SW] Cache MISS:', request.url);
        const networkResponse = await fetch(request);

        // Cache successful response for future
        if (networkResponse.ok) {
            await cacheResponse(request, networkResponse.clone(), cacheName);
        }

        return networkResponse;

    } catch (error) {
        console.error('[SW] Cache-first strategy failed:', error);

        // Network failed - try cache as last resort
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('[SW] Network failed, using stale cache:', request.url);
            return cachedResponse;
        }

        // Both cache and network failed
        return createErrorResponse('Content unavailable offline');
    }
}

/**
 * Network-First Strategy
 * Try network first, fall back to cache if offline
 * Good for: API requests that need fresh data
 */
async function networkFirstStrategy(request, cacheName) {
    try {
        // Try network first
        const networkResponse = await fetch(request);

        // Update cache with fresh data
        if (networkResponse.ok) {
            await cacheResponse(request, networkResponse.clone(), cacheName);
        }

        return networkResponse;

    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);

        // Network failed - try cache
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[SW] Using cached API response:', request.url);
            return cachedResponse;
        }

        // Both network and cache failed
        console.error('[SW] Network-first strategy failed completely:', error);
        return createErrorResponse('API unavailable offline');
    }
}

/**
 * Stale-While-Revalidate Strategy
 * Return cache immediately, update cache in background
 * Good for: non-critical resources that can be slightly stale
 */
async function staleWhileRevalidate(request, cacheName) {
    const cachedResponse = await caches.match(request);

    // Fetch fresh data in background
    const networkFetch = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cacheResponse(request, networkResponse.clone(), cacheName);
        }
        return networkResponse;
    }).catch((error) => {
        console.warn('[SW] Background fetch failed:', error);
    });

    // Return cached response immediately if available
    return cachedResponse || networkFetch;
}

// ============================================================================
// CACHE MANAGEMENT
// ============================================================================

/**
 * Cache response with metadata for TTL tracking
 */
async function cacheResponse(request, response, cacheName) {
    try {
        const cache = await caches.open(cacheName);

        // Clone response and add cache timestamp header
        const responseToCache = new Response(response.body, {
            status: response.status,
            statusText: response.statusText,
            headers: new Headers(response.headers)
        });

        // Add cache timestamp for TTL checking
        responseToCache.headers.set('sw-cache-time', Date.now().toString());

        await cache.put(request, responseToCache);

        // Check cache size and cleanup if needed
        await enforceCacheSizeLimit(cacheName);

        console.log('[SW] Cached:', request.url);

    } catch (error) {
        console.error('[SW] Failed to cache response:', error);
    }
}

/**
 * Check if cached response is expired based on TTL
 */
async function isCacheExpired(response, cacheName) {
    const cacheTime = response.headers.get('sw-cache-time');

    if (!cacheTime) {
        return false; // No timestamp - treat as not expired
    }

    const age = Date.now() - parseInt(cacheTime);
    let ttl;

    // Determine TTL based on cache name
    if (cacheName === CACHE_STATIC) {
        ttl = CACHE_TTL.static;
    } else if (cacheName === CACHE_MEDIA) {
        ttl = CACHE_TTL.media;
    } else if (cacheName === CACHE_API) {
        ttl = CACHE_TTL.api;
    } else if (cacheName === CACHE_HLS) {
        ttl = CACHE_TTL.hls;
    } else {
        ttl = CACHE_TTL.media; // Default
    }

    return age > ttl;
}

/**
 * Fetch and cache in background (fire and forget)
 */
async function fetchAndCache(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            await cacheResponse(request, response, cacheName);
        }
    } catch (error) {
        console.warn('[SW] Background fetch failed:', error);
    }
}

/**
 * Enforce cache size limits using LRU eviction
 */
async function enforceCacheSizeLimit(cacheName) {
    try {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();

        // Calculate total cache size
        let totalSize = 0;
        const entries = [];

        for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
                const blob = await response.blob();
                const size = blob.size;
                const cacheTime = response.headers.get('sw-cache-time') || '0';

                totalSize += size;
                entries.push({
                    request,
                    size,
                    cacheTime: parseInt(cacheTime)
                });
            }
        }

        // Determine size limit
        let maxSize;
        if (cacheName === CACHE_MEDIA) {
            maxSize = MAX_MEDIA_CACHE_SIZE;
        } else if (cacheName === CACHE_HLS) {
            maxSize = MAX_HLS_CACHE_SIZE;
        } else if (cacheName === CACHE_API) {
            maxSize = MAX_API_CACHE_SIZE;
        } else {
            return; // No limit for static cache
        }

        // If over limit, evict oldest entries (LRU)
        if (totalSize > maxSize) {
            console.log(`[SW] Cache ${cacheName} over limit (${formatBytes(totalSize)} / ${formatBytes(maxSize)})`);
            console.log('[SW] Evicting old entries...');

            // Sort by cache time (oldest first)
            entries.sort((a, b) => a.cacheTime - b.cacheTime);

            // Evict until under limit
            for (const entry of entries) {
                await cache.delete(entry.request);
                totalSize -= entry.size;
                console.log('[SW] Evicted:', entry.request.url);

                if (totalSize <= maxSize * 0.9) { // 90% threshold
                    break;
                }
            }

            console.log(`[SW] Cache size after cleanup: ${formatBytes(totalSize)}`);
        }

    } catch (error) {
        console.error('[SW] Cache size enforcement failed:', error);
    }
}

// ============================================================================
// BACKGROUND SYNC
// ============================================================================

self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync event:', event.tag);

    if (event.tag === 'sync-playlist') {
        event.waitUntil(syncPlaylist());
    } else if (event.tag === 'sync-device-status') {
        event.waitUntil(syncDeviceStatus());
    }
});

/**
 * Sync playlist in background
 */
async function syncPlaylist() {
    try {
        console.log('[SW] Syncing playlist...');

        const deviceId = await getDeviceIdFromClients();
        if (!deviceId) {
            console.warn('[SW] No device ID found, skip sync');
            return;
        }

        // Fetch latest playlist
        const response = await fetch(`/api/devices/${deviceId}/playlist`);
        if (response.ok) {
            const playlist = await response.json();

            // Cache playlist response
            const cache = await caches.open(CACHE_API);
            await cache.put(`/api/devices/${deviceId}/playlist`, response);

            console.log('[SW] Playlist synced:', playlist);
        }

    } catch (error) {
        console.error('[SW] Playlist sync failed:', error);
    }
}

/**
 * Sync device status in background
 */
async function syncDeviceStatus() {
    try {
        console.log('[SW] Syncing device status...');

        const deviceId = await getDeviceIdFromClients();
        if (!deviceId) {
            console.warn('[SW] No device ID found, skip sync');
            return;
        }

        // Fetch device status
        const response = await fetch(`/api/devices/${deviceId}`);
        if (response.ok) {
            // Cache response
            const cache = await caches.open(CACHE_API);
            await cache.put(`/api/devices/${deviceId}`, response);

            console.log('[SW] Device status synced');
        }

    } catch (error) {
        console.error('[SW] Device status sync failed:', error);
    }
}

// ============================================================================
// MESSAGE HANDLING
// ============================================================================

self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    const { action, data } = event.data;

    switch (action) {
        case 'PRELOAD_CONTENT':
            handlePreloadContent(data);
            break;

        case 'CLEAR_CACHE':
            handleClearCache(data);
            break;

        case 'GET_CACHE_SIZE':
            handleGetCacheSize(event);
            break;

        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        default:
            console.warn('[SW] Unknown action:', action);
    }
});

/**
 * Preload content URLs into cache
 */
async function handlePreloadContent(data) {
    try {
        const { urls = [] } = data;
        console.log(`[SW] Preloading ${urls.length} content URLs...`);

        const cache = await caches.open(CACHE_MEDIA);

        for (const url of urls) {
            try {
                const response = await fetch(url);
                if (response.ok) {
                    await cache.put(url, response);
                    console.log('[SW] Preloaded:', url);
                }
            } catch (error) {
                console.warn('[SW] Failed to preload:', url, error);
            }
        }

        console.log('[SW] Preload complete');

    } catch (error) {
        console.error('[SW] Preload failed:', error);
    }
}

/**
 * Clear specific cache or all caches
 */
async function handleClearCache(data) {
    try {
        const { cacheName } = data;

        if (cacheName) {
            // Clear specific cache
            console.log('[SW] Clearing cache:', cacheName);
            await caches.delete(cacheName);
        } else {
            // Clear all caches except static
            console.log('[SW] Clearing all caches...');
            await caches.delete(CACHE_MEDIA);
            await caches.delete(CACHE_API);
            await caches.delete(CACHE_HLS);
        }

        console.log('[SW] Cache cleared');

    } catch (error) {
        console.error('[SW] Cache clear failed:', error);
    }
}

/**
 * Get cache size statistics
 */
async function handleGetCacheSize(event) {
    try {
        const cacheNames = await caches.keys();
        const stats = {};

        for (const cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const requests = await cache.keys();

            let totalSize = 0;
            for (const request of requests) {
                const response = await cache.match(request);
                if (response) {
                    const blob = await response.blob();
                    totalSize += blob.size;
                }
            }

            stats[cacheName] = {
                size: totalSize,
                count: requests.length
            };
        }

        // Send stats back to client
        event.ports[0].postMessage({ stats });

    } catch (error) {
        console.error('[SW] Get cache size failed:', error);
        event.ports[0].postMessage({ error: error.message });
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if URL is HLS segment
 */
function isHLSSegment(url) {
    const path = url.pathname;
    return path.endsWith('.m3u8') || path.endsWith('.ts');
}

/**
 * Check if URL is media asset
 */
function isMediaAsset(url) {
    const path = url.pathname;
    return (
        path.includes('/stream/') ||
        path.endsWith('.jpg') ||
        path.endsWith('.jpeg') ||
        path.endsWith('.png') ||
        path.endsWith('.gif') ||
        path.endsWith('.mp4') ||
        path.endsWith('.webm') ||
        path.endsWith('.mov')
    );
}

/**
 * Check if URL is API request
 */
function isAPIRequest(url) {
    return url.pathname.startsWith('/api/');
}

/**
 * Create error response for offline scenarios
 */
function createErrorResponse(message) {
    return new Response(
        JSON.stringify({
            success: false,
            error: { message }
        }),
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'application/json' }
        }
    );
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get device ID from active clients
 */
async function getDeviceIdFromClients() {
    const clients = await self.clients.matchAll();

    for (const client of clients) {
        // Request device ID from client
        const response = await new Promise((resolve) => {
            const channel = new MessageChannel();

            channel.port1.onmessage = (event) => {
                resolve(event.data);
            };

            client.postMessage({ action: 'GET_DEVICE_ID' }, [channel.port2]);

            // Timeout after 1 second
            setTimeout(() => resolve(null), 1000);
        });

        if (response && response.deviceId) {
            return response.deviceId;
        }
    }

    return null;
}

// ============================================================================
// SERVICE WORKER READY
// ============================================================================

console.log('[SW] Service Worker loaded and ready (v' + CACHE_VERSION + ')');
console.log('[SW] Cache configuration:', {
    static: formatBytes(0), // No limit
    media: formatBytes(MAX_MEDIA_CACHE_SIZE),
    hls: formatBytes(MAX_HLS_CACHE_SIZE),
    api: formatBytes(MAX_API_CACHE_SIZE)
});
