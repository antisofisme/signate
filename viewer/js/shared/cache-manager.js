/**
 * Cache Manager for Digital Signage Viewer
 *
 * Provides JavaScript API wrapper for Service Worker cache management.
 * Handles priority-based caching, storage monitoring, and automatic cleanup.
 *
 * Features:
 * - Simple API for preloading content
 * - Cache statistics and storage usage
 * - Priority-based caching (high priority = cache first)
 * - Automatic cleanup when storage quota reached
 * - Event-driven updates for cache status
 *
 * @version 1.0.0
 * @author Smart TV Digital Signage System
 */

window.CacheManager = {
    /**
     * Service Worker registration
     * @type {ServiceWorkerRegistration|null}
     */
    registration: null,

    /**
     * Cache statistics
     * @type {Object}
     */
    stats: {
        totalSize: 0,
        totalItems: 0,
        byCache: {}
    },

    /**
     * Event listeners
     * @type {Object}
     */
    listeners: {
        'update': [],
        'quota-exceeded': [],
        'cache-cleared': []
    },

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    /**
     * Initialize Cache Manager
     * Registers Service Worker and sets up monitoring
     *
     * @returns {Promise<boolean>} - True if initialized successfully
     */
    init: async function() {
        try {
            console.log('[CacheManager] Initializing...');

            // Check if Service Worker is supported
            if (!('serviceWorker' in navigator)) {
                console.warn('[CacheManager] Service Worker not supported');
                return false;
            }

            // Register Service Worker
            this.registration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });

            console.log('[CacheManager] Service Worker registered:', this.registration.scope);

            // Wait for Service Worker to be ready
            await navigator.serviceWorker.ready;

            // Listen for Service Worker updates
            this.registration.addEventListener('updatefound', () => {
                console.log('[CacheManager] Service Worker update found');
                this._handleServiceWorkerUpdate();
            });

            // Listen for messages from Service Worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                this._handleServiceWorkerMessage(event);
            });

            // Update cache statistics
            await this.updateStats();

            // Monitor storage quota
            this._startQuotaMonitoring();

            console.log('[CacheManager] Initialized successfully');
            return true;

        } catch (error) {
            console.error('[CacheManager] Initialization failed:', error);
            return false;
        }
    },

    // ========================================================================
    // CACHE OPERATIONS
    // ========================================================================

    /**
     * Preload content URLs into cache
     *
     * @param {Array<string>} urls - Array of content URLs to preload
     * @param {Object} options - Preload options
     * @param {number} options.priority - Priority (1-10, higher = more important)
     * @param {Function} options.onProgress - Progress callback (current, total)
     * @returns {Promise<Object>} - Preload results
     */
    preload: async function(urls, options = {}) {
        try {
            const { priority = 5, onProgress } = options;

            console.log(`[CacheManager] Preloading ${urls.length} URLs (priority: ${priority})`);

            // Sort by priority (high priority first)
            const sortedUrls = this._sortByPriority(urls, priority);

            // Send preload command to Service Worker
            if (navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({
                    action: 'PRELOAD_CONTENT',
                    data: { urls: sortedUrls }
                });
            }

            // Track progress manually if needed
            if (onProgress) {
                let completed = 0;
                for (const url of sortedUrls) {
                    try {
                        await fetch(url);
                        completed++;
                        onProgress(completed, sortedUrls.length);
                    } catch (error) {
                        console.warn('[CacheManager] Preload failed for:', url);
                    }
                }
            }

            // Update stats after preload
            await this.updateStats();

            return {
                success: true,
                preloaded: urls.length
            };

        } catch (error) {
            console.error('[CacheManager] Preload failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    },

    /**
     * Clear specific cache or all caches
     *
     * @param {string|null} cacheName - Cache name to clear (null = all caches)
     * @returns {Promise<boolean>} - True if cleared successfully
     */
    clear: async function(cacheName = null) {
        try {
            console.log('[CacheManager] Clearing cache:', cacheName || 'all');

            // Send clear command to Service Worker
            if (navigator.serviceWorker.controller) {
                navigator.serviceWorker.controller.postMessage({
                    action: 'CLEAR_CACHE',
                    data: { cacheName }
                });
            }

            // Update stats after clear
            await this.updateStats();

            // Emit event
            this._emit('cache-cleared', { cacheName });

            return true;

        } catch (error) {
            console.error('[CacheManager] Clear failed:', error);
            return false;
        }
    },

    /**
     * Get cache size and item count
     *
     * @returns {Promise<Object>} - Cache statistics
     */
    getSize: async function() {
        try {
            // Request cache size from Service Worker
            const stats = await this._sendMessageToSW({
                action: 'GET_CACHE_SIZE'
            });

            return stats || this.stats;

        } catch (error) {
            console.error('[CacheManager] Get size failed:', error);
            return this.stats;
        }
    },

    /**
     * Get cached items list
     *
     * @param {string|null} cacheName - Cache name (null = all caches)
     * @returns {Promise<Array>} - Array of cached URLs
     */
    getItems: async function(cacheName = null) {
        try {
            const cacheNames = cacheName
                ? [cacheName]
                : await caches.keys();

            const items = [];

            for (const name of cacheNames) {
                const cache = await caches.open(name);
                const requests = await cache.keys();

                for (const request of requests) {
                    items.push({
                        url: request.url,
                        cache: name
                    });
                }
            }

            return items;

        } catch (error) {
            console.error('[CacheManager] Get items failed:', error);
            return [];
        }
    },

    /**
     * Update cache statistics
     *
     * @returns {Promise<void>}
     */
    updateStats: async function() {
        try {
            const cacheNames = await caches.keys();
            let totalSize = 0;
            let totalItems = 0;
            const byCache = {};

            for (const cacheName of cacheNames) {
                const cache = await caches.open(cacheName);
                const requests = await cache.keys();

                let cacheSize = 0;
                for (const request of requests) {
                    const response = await cache.match(request);
                    if (response) {
                        const blob = await response.blob();
                        cacheSize += blob.size;
                    }
                }

                totalSize += cacheSize;
                totalItems += requests.length;

                byCache[cacheName] = {
                    size: cacheSize,
                    count: requests.length
                };
            }

            this.stats = {
                totalSize,
                totalItems,
                byCache
            };

            // Emit update event
            this._emit('update', this.stats);

            console.log('[CacheManager] Stats updated:', this.stats);

        } catch (error) {
            console.error('[CacheManager] Update stats failed:', error);
        }
    },

    // ========================================================================
    // STORAGE QUOTA MANAGEMENT
    // ========================================================================

    /**
     * Check storage quota
     *
     * @returns {Promise<Object>} - Quota information
     */
    checkQuota: async function() {
        try {
            if (!navigator.storage || !navigator.storage.estimate) {
                return {
                    supported: false,
                    usage: 0,
                    quota: 0,
                    percentage: 0
                };
            }

            const estimate = await navigator.storage.estimate();
            const usage = estimate.usage || 0;
            const quota = estimate.quota || 0;
            const percentage = quota > 0 ? (usage / quota) * 100 : 0;

            return {
                supported: true,
                usage,
                quota,
                percentage,
                available: quota - usage
            };

        } catch (error) {
            console.error('[CacheManager] Check quota failed:', error);
            return {
                supported: false,
                usage: 0,
                quota: 0,
                percentage: 0
            };
        }
    },

    /**
     * Start monitoring storage quota
     *
     * @private
     */
    _startQuotaMonitoring: function() {
        // Check quota every 5 minutes
        setInterval(async () => {
            const quota = await this.checkQuota();

            if (quota.percentage > 90) {
                console.warn('[CacheManager] Storage quota near limit:', quota.percentage + '%');
                this._emit('quota-exceeded', quota);
            }
        }, 5 * 60 * 1000);
    },

    // ========================================================================
    // EVENT MANAGEMENT
    // ========================================================================

    /**
     * Add event listener
     *
     * @param {string} event - Event name (update, quota-exceeded, cache-cleared)
     * @param {Function} callback - Callback function
     */
    on: function(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    },

    /**
     * Remove event listener
     *
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    off: function(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
        }
    },

    /**
     * Emit event
     *
     * @param {string} event - Event name
     * @param {any} data - Event data
     * @private
     */
    _emit: function(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach((callback) => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('[CacheManager] Event listener error:', error);
                }
            });
        }
    },

    // ========================================================================
    // UTILITY METHODS
    // ========================================================================

    /**
     * Sort URLs by priority
     *
     * @param {Array<string>} urls - URLs to sort
     * @param {number} priority - Priority value
     * @returns {Array<string>} - Sorted URLs
     * @private
     */
    _sortByPriority: function(urls, priority) {
        // Higher priority = fetch first
        // For now, just return as-is (can add more complex logic later)
        return urls;
    },

    /**
     * Handle Service Worker update
     *
     * @private
     */
    _handleServiceWorkerUpdate: function() {
        const installing = this.registration.installing;

        if (installing) {
            installing.addEventListener('statechange', () => {
                if (installing.state === 'installed' && navigator.serviceWorker.controller) {
                    // New Service Worker available
                    console.log('[CacheManager] New Service Worker available');

                    // Notify user to refresh
                    this._emit('update-available', {
                        message: 'A new version is available. Refresh to update.'
                    });
                }
            });
        }
    },

    /**
     * Handle message from Service Worker
     *
     * @param {MessageEvent} event - Message event
     * @private
     */
    _handleServiceWorkerMessage: function(event) {
        const { action, data } = event.data;

        console.log('[CacheManager] Message from SW:', action, data);

        // Handle different message types
        switch (action) {
            case 'CACHE_UPDATED':
                this.updateStats();
                break;

            case 'QUOTA_EXCEEDED':
                this._emit('quota-exceeded', data);
                break;

            default:
                console.log('[CacheManager] Unknown message:', action);
        }
    },

    /**
     * Send message to Service Worker and wait for response
     *
     * @param {Object} message - Message object
     * @returns {Promise<any>} - Response from Service Worker
     * @private
     */
    _sendMessageToSW: function(message) {
        return new Promise((resolve, reject) => {
            if (!navigator.serviceWorker.controller) {
                reject(new Error('No Service Worker controller'));
                return;
            }

            const channel = new MessageChannel();

            channel.port1.onmessage = (event) => {
                if (event.data.error) {
                    reject(new Error(event.data.error));
                } else {
                    resolve(event.data);
                }
            };

            navigator.serviceWorker.controller.postMessage(message, [channel.port2]);

            // Timeout after 10 seconds
            setTimeout(() => {
                reject(new Error('Service Worker response timeout'));
            }, 10000);
        });
    },

    /**
     * Format bytes to human-readable size
     *
     * @param {number} bytes - Bytes
     * @returns {string} - Formatted size
     */
    formatBytes: function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// ============================================================================
// CONSOLE HELPERS
// ============================================================================

/**
 * Show cache statistics in console
 */
window.showCacheStats = async function() {
    const stats = await CacheManager.getSize();
    console.table(stats.byCache);
    console.log('Total Size:', CacheManager.formatBytes(stats.totalSize));
    console.log('Total Items:', stats.totalItems);
};

/**
 * Clear all caches via console
 */
window.clearAllCaches = async function() {
    const confirmed = confirm('Clear all caches? This will delete all cached content.');
    if (confirmed) {
        await CacheManager.clear();
        console.log('[CacheManager] All caches cleared');
    }
};

/**
 * Show storage quota in console
 */
window.showStorageQuota = async function() {
    const quota = await CacheManager.checkQuota();
    console.log('Storage Quota:', {
        usage: CacheManager.formatBytes(quota.usage),
        quota: CacheManager.formatBytes(quota.quota),
        percentage: quota.percentage.toFixed(2) + '%',
        available: CacheManager.formatBytes(quota.available)
    });
};

console.log('[CacheManager] Loaded (v1.0.0) - Use showCacheStats(), clearAllCaches(), showStorageQuota()');
