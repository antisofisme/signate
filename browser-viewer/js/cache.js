/**
 * Cache Module
 * Manages IndexedDB cache for offline media storage and retrieval
 */

import { DB_NAME, DB_VERSION, STORE_NAME, db, setDb } from './config.js';

// ========================================
// IndexedDB Cache Manager
// ========================================

/**
 * Initialize IndexedDB for offline media caching
 * @returns {Promise<IDBDatabase>} Database instance
 */
export async function initMediaCache() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('❌ IndexedDB failed to open:', request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            const dbInstance = request.result;
            setDb(dbInstance);
            console.log('✅ IndexedDB opened successfully');
            resolve(dbInstance);
        };

        request.onupgradeneeded = (event) => {
            const dbInstance = event.target.result;

            // Create object store for media files
            if (!dbInstance.objectStoreNames.contains(STORE_NAME)) {
                const objectStore = dbInstance.createObjectStore(STORE_NAME, { keyPath: 'content_id' });
                objectStore.createIndex('url', 'url', { unique: false });
                objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                console.log('📦 Created media cache object store');
            }
        };
    });
}

/**
 * Check if content is cached
 * @param {number} contentId - Content ID to check
 * @returns {Promise<boolean>}
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
 * @param {number} contentId - Content ID to retrieve
 * @returns {Promise<Object|null>} Cached content object
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
 * @param {Object} content - Content object with URL and metadata
 * @returns {Promise<Object|null>} Cached content entry or null on failure
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
 * Save content to cache
 * @param {Object} cacheEntry - Cache entry to save
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
 * Delete content from cache
 * @param {number} contentId - Content ID to delete
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
 * @returns {Promise<Array<number>>} Array of content IDs
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
 * Sync cache with playlist - download new content and remove unused
 * @param {Array} newPlaylist - Updated playlist array
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
 * @param {number} contentId - Content ID
 * @returns {Promise<string|null>} Blob URL or null if not cached
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
