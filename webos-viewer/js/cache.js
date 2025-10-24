/**
 * Cache Module
 * Manages IndexedDB offline cache for media files
 */

import { DB_NAME, DB_VERSION, STORE_NAME, db, setDb } from './config.js';

// ========================================
// IndexedDB Cache Manager
// ========================================

/**
 * Initialize IndexedDB for offline media caching
 * @returns {Promise<IDBDatabase>}
 */
export async function initMediaCache() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('❌ IndexedDB failed to open:', request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            const database = request.result;
            setDb(database);
            console.log('✅ IndexedDB opened successfully');
            resolve(database);
        };

        request.onupgradeneeded = (event) => {
            const dbInstance = event.target.result;
            const oldVersion = event.oldVersion;

            // If upgrading from version 1 to 2, delete old store to force re-download
            if (oldVersion === 1 && dbInstance.objectStoreNames.contains(STORE_NAME)) {
                dbInstance.deleteObjectStore(STORE_NAME);
                console.log('🗑️  Deleted old cache (v1) - will re-download with MIME type fix');
            }

            // Create object store for media files
            if (!dbInstance.objectStoreNames.contains(STORE_NAME)) {
                const objectStore = dbInstance.createObjectStore(STORE_NAME, { keyPath: 'content_id' });
                objectStore.createIndex('url', 'url', { unique: false });
                objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                console.log('📦 Created media cache object store (v2)');
 */
export async function isContentCached(contentId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const objectStore = transaction.objectStore(STORE_NAME);
        const request = objectStore.get(contentId);

        request.onsuccess = () => {
            resolve(!!request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Get cached content
 * @param {number} contentId
 * @returns {Promise<Object|null>}
 */
export async function getCachedContent(contentId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const objectStore = transaction.objectStore(STORE_NAME);
        const request = objectStore.get(contentId);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Download and cache content
 * @param {Object} content - Content object with url, content_id, etc.
 * @returns {Promise<Object|null>}
 */
export async function downloadAndCacheContent(content) {
    try {
        console.log(`⬇️  Downloading content ${content.content_id}: ${content.title}`);

        // Fetch content from URL
        const response = await fetch(content.url);

        if (!response.ok) {
            throw new Error(`Failed to fetch: ${response.status}`);
        }

        // Get blob data
        const blob = await response.blob();
        const contentType = response.headers.get('content-type') || content.mime_type || 'application/octet-stream';

        // Store in IndexedDB
        const cacheEntry = {
            content_id: content.content_id,
            title: content.title,
            url: content.url,
            content_type: content.content_type,
            mime_type: contentType,
            blob: blob,
            size: blob.size,
            timestamp: Date.now()
        };

        await saveToCache(cacheEntry);

        console.log(`✅ Cached content ${content.content_id} (${(blob.size / 1024 / 1024).toFixed(2)} MB)`);
        return cacheEntry;

    } catch (error) {
        console.error(`❌ Failed to cache content ${content.content_id}:`, error);
        return null;
    }
}

/**
 * Save to cache
 * @param {Object} cacheEntry
 * @returns {Promise<void>}
 */
export async function saveToCache(cacheEntry) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const objectStore = transaction.objectStore(STORE_NAME);
        const request = objectStore.put(cacheEntry);

        request.onsuccess = () => {
            resolve();
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Delete from cache
 * @param {number} contentId
 * @returns {Promise<void>}
 */
export async function deleteFromCache(contentId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const objectStore = transaction.objectStore(STORE_NAME);
        const request = objectStore.delete(contentId);

        request.onsuccess = () => {
            console.log(`🗑️  Removed content ${contentId} from cache`);
            resolve();
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Get all cached content IDs
 * @returns {Promise<Array<number>>}
 */
export async function getAllCachedContentIds() {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const objectStore = transaction.objectStore(STORE_NAME);
        const request = objectStore.getAllKeys();

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Sync cache with playlist
 * @param {Array} newPlaylist
 * @returns {Promise<void>}
 */
export async function syncCacheWithPlaylist(newPlaylist) {
    try {
        // Get all cached content IDs
        const cachedIds = await getAllCachedContentIds();
        const playlistIds = newPlaylist.map(item => item.content_id);

        // Find content to remove (in cache but not in playlist)
        const idsToRemove = cachedIds.filter(id => !playlistIds.includes(id));

        // Find content to download (in playlist but not in cache)
        const idsToDownload = playlistIds.filter(id => !cachedIds.includes(id));

        // Remove unused content from cache
        for (const id of idsToRemove) {
            await deleteFromCache(id);
        }

        // Download new content
        for (const content of newPlaylist) {
            if (idsToDownload.includes(content.content_id)) {
                await downloadAndCacheContent(content);
            }
        }

        console.log(`🔄 Cache synced: +${idsToDownload.length} downloaded, -${idsToRemove.length} removed`);

    } catch (error) {
        console.error('❌ Cache sync failed:', error);
    }
}

/**
 * Get cached blob URL for playback
 * @param {number} contentId
 * @returns {Promise<string|null>}
 */
export async function getCachedBlobUrl(contentId) {
    try {
        const cached = await getCachedContent(contentId);

        if (!cached) {
            return null;
        }

        // Create blob with correct MIME type for playback
        // This is critical for video playback - browser needs to know the video format
        const typedBlob = new Blob([cached.blob], { type: cached.mime_type });
        const blobUrl = URL.createObjectURL(typedBlob);
        return blobUrl;

    } catch (error) {
        console.error(`❌ Failed to get cached blob URL for ${contentId}:`, error);
        return null;
    }
}
