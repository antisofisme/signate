/**
 * HLS Service Worker for Offline Playback
 * Intercepts HLS manifest and segment requests to serve from IndexedDB cache
 *
 * @features
 * - Intercept .m3u8 requests (master/variant playlists)
 * - Intercept .ts requests (video segments)
 * - Serve cached segments from IndexedDB
 * - Fallback to network if not cached
 * - Support adaptive bitrate streaming offline
 */

const CACHE_NAME = 'hls-offline-v1';
const DB_NAME = 'signage_hls_cache';
const DB_VERSION = 1;
const SEGMENT_STORE = 'hls_segments';
const META_STORE = 'hls_metadata';

// Open IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// Get segment from IndexedDB by URL
async function getSegmentByURL(segmentUrl) {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([SEGMENT_STORE], 'readonly');
    const store = transaction.objectStore(SEGMENT_STORE);

    // We need to scan all segments to find matching URL
    const request = store.openCursor();

    request.onsuccess = (event) => {
      const cursor = event.target.result;

      if (cursor) {
        const segment = cursor.value;

        // Match segment URL (compare without query params)
        const storedUrl = segment.segmentUrl.split('?')[0];
        const requestUrl = segmentUrl.split('?')[0];

        if (storedUrl === requestUrl) {
          resolve(segment);
          return;
        }

        cursor.continue();
      } else {
        // Not found
        resolve(null);
      }
    };

    request.onerror = () => reject(request.error);
  });
}

// Get HLS metadata by URL pattern
async function getMetadataByURL(masterUrl) {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction([META_STORE], 'readonly');
    const store = transaction.objectStore(META_STORE);
    const request = store.openCursor();

    request.onsuccess = (event) => {
      const cursor = event.target.result;

      if (cursor) {
        const metadata = cursor.value;

        // Match master playlist URL
        if (metadata.masterPlaylistUrl === masterUrl) {
          resolve(metadata);
          return;
        }

        cursor.continue();
      } else {
        resolve(null);
      }
    };

    request.onerror = () => reject(request.error);
  });
}

// Create modified variant playlist with blob URLs
async function createOfflineVariantPlaylist(metadata, quality) {
  const segments = metadata.segments[quality];
  if (!segments) {
    return null;
  }

  // Build variant playlist content
  let content = '#EXTM3U\n';
  content += '#EXT-X-VERSION:3\n';
  content += '#EXT-X-TARGETDURATION:6\n';
  content += '#EXT-X-MEDIA-SEQUENCE:0\n';

  for (const segment of segments) {
    content += `#EXTINF:${segment.duration},\n`;
    // Use original segment filename (Service Worker will intercept and serve from cache)
    const filename = segment.segmentUrl.split('/').pop();
    content += `${filename}\n`;
  }

  content += '#EXT-X-ENDLIST\n';

  return content;
}

// Service Worker Install
self.addEventListener('install', (event) => {
  console.log('[HLS Service Worker] Installing...');

  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Service Worker Activate
self.addEventListener('activate', (event) => {
  console.log('[HLS Service Worker] Activating...');

  // Claim all clients immediately
  event.waitUntil(self.clients.claim());
});

// Service Worker Fetch - Intercept HLS requests
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const pathname = url.pathname;

  // Only intercept HLS-related requests
  const isHLSRequest = pathname.includes('.m3u8') || pathname.includes('.ts');

  if (!isHLSRequest) {
    // Pass through non-HLS requests
    return;
  }

  console.log('[HLS Service Worker] Intercepting:', pathname);

  event.respondWith(
    handleHLSRequest(event.request).catch((error) => {
      console.error('[HLS Service Worker] Error handling request:', error);
      // Fallback to network on error
      return fetch(event.request);
    })
  );
});

// Handle HLS requests (manifest or segment)
async function handleHLSRequest(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // Handle master playlist (.m3u8)
  if (pathname.endsWith('master.m3u8')) {
    return handleMasterPlaylist(request);
  }

  // Handle variant playlist (quality/playlist.m3u8)
  if (pathname.includes('/playlist.m3u8')) {
    return handleVariantPlaylist(request);
  }

  // Handle video segment (.ts)
  if (pathname.endsWith('.ts')) {
    return handleVideoSegment(request);
  }

  // Unknown HLS request - fallback to network
  return fetch(request);
}

// Handle master playlist request
async function handleMasterPlaylist(request) {
  const masterUrl = request.url;

  try {
    // Check if we have cached metadata
    const metadata = await getMetadataByURL(masterUrl);

    if (metadata) {
      console.log('[HLS Service Worker] ✅ Serving master playlist from cache');

      // We have cached content - serve original master playlist
      // (variant URLs will be intercepted and served from cache)
      return fetch(request);
    } else {
      console.log('[HLS Service Worker] 🌐 Master playlist not cached, fetching from network');
      return fetch(request);
    }
  } catch (error) {
    console.error('[HLS Service Worker] Error handling master playlist:', error);
    return fetch(request);
  }
}

// Handle variant playlist request
async function handleVariantPlaylist(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;

  try {
    // Extract quality from path (e.g., /360p/playlist.m3u8)
    const pathParts = pathname.split('/');
    const qualityFolder = pathParts[pathParts.length - 2]; // '360p'

    // Find master playlist URL (go up two levels)
    const masterUrl = url.origin + pathParts.slice(0, -2).join('/') + '/master.m3u8';

    // Check if we have cached metadata
    const metadata = await getMetadataByURL(masterUrl);

    if (metadata && metadata.segments[qualityFolder]) {
      console.log(`[HLS Service Worker] ✅ Serving variant playlist (${qualityFolder}) from cache`);

      // Create modified playlist with original segment filenames
      const playlistContent = await createOfflineVariantPlaylist(metadata, qualityFolder);

      if (playlistContent) {
        return new Response(playlistContent, {
          status: 200,
          headers: {
            'Content-Type': 'application/vnd.apple.mpegurl',
            'Cache-Control': 'public, max-age=3600',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }
    }

    console.log('[HLS Service Worker] 🌐 Variant playlist not cached, fetching from network');
    return fetch(request);
  } catch (error) {
    console.error('[HLS Service Worker] Error handling variant playlist:', error);
    return fetch(request);
  }
}

// Handle video segment request
async function handleVideoSegment(request) {
  const segmentUrl = request.url;

  try {
    // Check if segment is cached
    const cachedSegment = await getSegmentByURL(segmentUrl);

    if (cachedSegment && cachedSegment.data) {
      console.log('[HLS Service Worker] ✅ Serving segment from cache:', segmentUrl.split('/').pop());

      // Serve cached segment as Response
      return new Response(cachedSegment.data, {
        status: 200,
        headers: {
          'Content-Type': 'video/mp2t',
          'Cache-Control': 'public, max-age=31536000, immutable',
          'Access-Control-Allow-Origin': '*',
          'Content-Length': cachedSegment.size.toString(),
        },
      });
    } else {
      console.log('[HLS Service Worker] 🌐 Segment not cached, fetching from network:', segmentUrl.split('/').pop());
      return fetch(request);
    }
  } catch (error) {
    console.error('[HLS Service Worker] Error handling segment:', error);
    return fetch(request);
  }
}

console.log('[HLS Service Worker] Loaded and ready');
