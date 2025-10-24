/**
 * Player Cache Module
 * Manages IndexedDB cache for offline media storage and retrieval
 */

window.PlayerCache = {
    // Cache configuration
    DB_NAME: 'signage_media_cache',
    DB_VERSION: 2,
    STORE_NAME: 'media_files',

    // Database instance
    cacheDb: null,

    /**
     * Initialize IndexedDB for offline media caching
     * @returns {Promise<IDBDatabase>} Database instance
     */
    initMediaCache: async function() {
        const self = this;

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(self.DB_NAME, self.DB_VERSION);

            request.onerror = () => {
                console.error('❌ IndexedDB failed to open:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                self.cacheDb = request.result;
                window.PlayerState.cacheDb = self.cacheDb;
                console.log('✅ IndexedDB opened successfully');
                resolve(self.cacheDb);
            };

            request.onupgradeneeded = (event) => {
                const dbInstance = event.target.result;
                const oldVersion = event.oldVersion;

                // If upgrading from version 1 to 2, delete old store to force re-download
                if (oldVersion === 1 && dbInstance.objectStoreNames.contains(self.STORE_NAME)) {
                    dbInstance.deleteObjectStore(self.STORE_NAME);
                    console.log('🗑️  Deleted old cache (v1) - will re-download with MIME type fix');
                }

                // Create object store for media files
                if (!dbInstance.objectStoreNames.contains(self.STORE_NAME)) {
                    const objectStore = dbInstance.createObjectStore(self.STORE_NAME, { keyPath: 'content_id' });
                    objectStore.createIndex('url', 'url', { unique: false });
                    objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                    console.log('📦 Created media cache object store (v2)');
                }
            };
        });
    },

    /**
     * Check if content is cached
     * @param {number} contentId - Content ID to check
     * @returns {Promise<boolean>}
     */
    isContentCached: async function(contentId) {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readonly');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.get(contentId);

            request.onsuccess = () => {
                resolve(!!request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    },

    /**
     * Get cached content
     * @param {number} contentId - Content ID to retrieve
     * @returns {Promise<Object|null>} Cached content object
     */
    getCachedContent: async function(contentId) {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readonly');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.get(contentId);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    },

    /**
     * Download and cache content
     * @param {Object} content - Content object with URL and metadata
     * @returns {Promise<Object|null>} Cached content entry or null on failure
     */
    downloadAndCacheContent: async function(content) {
        const self = this;

        try {
            console.log('⬇️  Downloading content ' + content.content_id + ': ' + content.title);

            // Fetch content from URL
            const response = await fetch(content.url);

            if (!response.ok) {
                throw new Error('Failed to fetch: ' + response.status);
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

            await self.saveToCache(cacheEntry);

            console.log('✅ Cached content ' + content.content_id + ' (' + (blob.size / 1024 / 1024).toFixed(2) + ' MB)');
            return cacheEntry;

        } catch (error) {
            console.error('❌ Failed to cache content ' + content.content_id + ':', error);
            return null;
        }
    },

    /**
     * Save content to cache
     * @param {Object} cacheEntry - Cache entry to save
     * @returns {Promise<void>}
     */
    saveToCache: async function(cacheEntry) {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.put(cacheEntry);

            request.onsuccess = () => {
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    },

    /**
     * Delete content from cache
     * @param {number} contentId - Content ID to delete
     * @returns {Promise<void>}
     */
    deleteFromCache: async function(contentId) {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.delete(contentId);

            request.onsuccess = () => {
                console.log('🗑️  Removed content ' + contentId + ' from cache');
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    },

    /**
     * Get all cached content IDs
     * @returns {Promise<Array<number>>} Array of content IDs
     */
    getAllCachedContentIds: async function() {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readonly');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.getAllKeys();

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    },

    /**
     * Sync cache with playlist - download new content and remove unused
     * @param {Array} newPlaylist - Updated playlist array
     * @returns {Promise<void>}
     */
    syncCacheWithPlaylist: async function(newPlaylist) {
        const self = this;

        try {
            // Get all cached content IDs
            const cachedIds = await self.getAllCachedContentIds();
            const playlistIds = newPlaylist.map(function(item) { return item.content_id; });

            // Find content to remove (in cache but not in playlist)
            const idsToRemove = cachedIds.filter(function(id) { return !playlistIds.includes(id); });

            // Find content to download (in playlist but not in cache)
            const idsToDownload = playlistIds.filter(function(id) { return !cachedIds.includes(id); });

            // Remove unused content from cache
            for (let i = 0; i < idsToRemove.length; i++) {
                await self.deleteFromCache(idsToRemove[i]);
            }

            // Download new content
            for (let i = 0; i < newPlaylist.length; i++) {
                const content = newPlaylist[i];
                if (idsToDownload.includes(content.content_id)) {
                    await self.downloadAndCacheContent(content);
                }
            }

            console.log('🔄 Cache synced: +' + idsToDownload.length + ' downloaded, -' + idsToRemove.length + ' removed');

        } catch (error) {
            console.error('❌ Cache sync failed:', error);
        }
    },

    /**
     * Get cached blob URL for playback
     * @param {number} contentId - Content ID
     * @returns {Promise<string|null>} Blob URL or null if not cached
     */
    getCachedBlobUrl: async function(contentId) {
        const self = this;

        try {
            const cached = await self.getCachedContent(contentId);

            if (!cached) {
                return null;
            }

            // Create blob with correct MIME type for playback
            // This is critical for video playback - browser needs to know the video format
            const typedBlob = new Blob([cached.blob], { type: cached.mime_type });
            const blobUrl = URL.createObjectURL(typedBlob);
            return blobUrl;

        } catch (error) {
            console.error('❌ Failed to get cached blob URL for ' + contentId + ':', error);
            return null;
        }
    },

    /**
     * Clear all cache (for debugging/reset)
     * @returns {Promise<void>}
     */
    clearAllCache: async function() {
        const self = this;

        return new Promise((resolve, reject) => {
            const transaction = self.cacheDb.transaction([self.STORE_NAME], 'readwrite');
            const objectStore = transaction.objectStore(self.STORE_NAME);
            const request = objectStore.clear();

            request.onsuccess = () => {
                console.log('🗑️  All cache cleared');
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }
};
