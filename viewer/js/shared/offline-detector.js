/**
 * Offline Detector for Digital Signage Viewer
 *
 * Monitors network connectivity and quality for adaptive playback.
 * Provides online/offline detection, network speed monitoring, and quality adaptation.
 *
 * Features:
 * - Online/offline detection with navigator.onLine
 * - Network quality monitoring (fast/slow/offline)
 * - Adaptive quality selection based on connection speed
 * - Automatic fallback to cached content when offline
 * - Event-driven updates for network status changes
 *
 * @version 1.0.0
 * @author Smart TV Digital Signage System
 */

window.OfflineDetector = {
    /**
     * Current network status
     * @type {Object}
     */
    status: {
        online: true,
        quality: 'unknown', // 'fast', 'slow', 'offline', 'unknown'
        speed: 0, // Mbps
        latency: 0, // ms
        lastCheck: null
    },

    /**
     * Event listeners
     * @type {Object}
     */
    listeners: {
        'online': [],
        'offline': [],
        'quality-change': []
    },

    /**
     * Configuration
     * @type {Object}
     */
    config: {
        checkInterval: 30000, // Check every 30 seconds
        timeoutMs: 5000, // 5 second timeout for checks
        testUrl: '/api/health', // Endpoint for connectivity tests
        testFileUrl: null, // URL for download speed test (optional)
        testFileSize: 1024 * 100, // 100KB for speed test
        fastThresholdMbps: 5, // > 5 Mbps = fast
        slowThresholdMbps: 1 // < 1 Mbps = slow
    },

    /**
     * Check interval ID
     * @type {number|null}
     */
    checkIntervalId: null,

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    /**
     * Initialize Offline Detector
     * Starts monitoring network status
     *
     * @param {Object} options - Configuration options
     * @returns {void}
     */
    init: function(options = {}) {
        try {
            console.log('[OfflineDetector] Initializing...');

            // Merge options with defaults
            this.config = {
                ...this.config,
                ...options
            };

            // Set initial status from navigator.onLine
            this.status.online = navigator.onLine;
            this.status.quality = navigator.onLine ? 'unknown' : 'offline';

            // Listen for online/offline events
            window.addEventListener('online', () => this._handleOnline());
            window.addEventListener('offline', () => this._handleOffline());

            // Start periodic checks
            this._startPeriodicChecks();

            // Do initial check
            this.check();

            console.log('[OfflineDetector] Initialized successfully');

        } catch (error) {
            console.error('[OfflineDetector] Initialization failed:', error);
        }
    },

    /**
     * Stop monitoring
     *
     * @returns {void}
     */
    stop: function() {
        if (this.checkIntervalId) {
            clearInterval(this.checkIntervalId);
            this.checkIntervalId = null;
            console.log('[OfflineDetector] Monitoring stopped');
        }
    },

    // ========================================================================
    // NETWORK CHECKING
    // ========================================================================

    /**
     * Check network connectivity and quality
     *
     * @returns {Promise<Object>} - Network status
     */
    check: async function() {
        try {
            const startTime = performance.now();

            // First, check if we can reach the server
            const isOnline = await this._checkConnectivity();

            if (!isOnline) {
                // Offline
                this._updateStatus({
                    online: false,
                    quality: 'offline',
                    speed: 0,
                    latency: 0,
                    lastCheck: new Date()
                });
                return this.status;
            }

            // Online - measure latency
            const latency = Math.round(performance.now() - startTime);

            // Measure download speed (optional)
            let speed = 0;
            if (this.config.testFileUrl) {
                speed = await this._measureSpeed();
            }

            // Determine quality based on speed and latency
            const quality = this._determineQuality(speed, latency);

            // Update status
            this._updateStatus({
                online: true,
                quality,
                speed,
                latency,
                lastCheck: new Date()
            });

            return this.status;

        } catch (error) {
            console.error('[OfflineDetector] Check failed:', error);

            // Assume offline on error
            this._updateStatus({
                online: false,
                quality: 'offline',
                speed: 0,
                latency: 0,
                lastCheck: new Date()
            });

            return this.status;
        }
    },

    /**
     * Check basic connectivity to server
     *
     * @returns {Promise<boolean>} - True if online
     * @private
     */
    _checkConnectivity: async function() {
        try {
            // Use fetch with short timeout to check connectivity
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);

            const response = await fetch(this.config.testUrl, {
                method: 'HEAD',
                cache: 'no-cache',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            return response.ok;

        } catch (error) {
            // Network error or timeout
            return false;
        }
    },

    /**
     * Measure download speed
     *
     * @returns {Promise<number>} - Speed in Mbps
     * @private
     */
    _measureSpeed: async function() {
        try {
            const startTime = performance.now();

            // Download test file
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);

            const response = await fetch(this.config.testFileUrl, {
                cache: 'no-cache',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                return 0;
            }

            // Read response body
            await response.blob();

            const duration = (performance.now() - startTime) / 1000; // Convert to seconds
            const sizeInBits = this.config.testFileSize * 8;
            const speedBps = sizeInBits / duration;
            const speedMbps = speedBps / (1024 * 1024);

            return Math.round(speedMbps * 100) / 100; // Round to 2 decimals

        } catch (error) {
            console.warn('[OfflineDetector] Speed measurement failed:', error);
            return 0;
        }
    },

    /**
     * Determine network quality based on metrics
     *
     * @param {number} speed - Speed in Mbps
     * @param {number} latency - Latency in ms
     * @returns {string} - Quality ('fast', 'slow', 'offline')
     * @private
     */
    _determineQuality: function(speed, latency) {
        // If we have speed data, use it
        if (speed > 0) {
            if (speed >= this.config.fastThresholdMbps) {
                return 'fast';
            } else if (speed >= this.config.slowThresholdMbps) {
                return 'slow';
            } else {
                return 'slow';
            }
        }

        // Otherwise, use latency as indicator
        if (latency < 200) {
            return 'fast';
        } else if (latency < 1000) {
            return 'slow';
        } else {
            return 'slow';
        }
    },

    // ========================================================================
    // STATUS MANAGEMENT
    // ========================================================================

    /**
     * Update network status and emit events
     *
     * @param {Object} newStatus - New status object
     * @private
     */
    _updateStatus: function(newStatus) {
        const oldStatus = { ...this.status };

        // Update status
        this.status = {
            ...this.status,
            ...newStatus
        };

        // Emit events if status changed
        if (oldStatus.online !== this.status.online) {
            if (this.status.online) {
                console.log('[OfflineDetector] Network online');
                this._emit('online', this.status);
            } else {
                console.log('[OfflineDetector] Network offline');
                this._emit('offline', this.status);
            }
        }

        if (oldStatus.quality !== this.status.quality) {
            console.log('[OfflineDetector] Quality changed:', this.status.quality);
            this._emit('quality-change', this.status);
        }
    },

    /**
     * Get current network status
     *
     * @returns {Object} - Current status
     */
    getStatus: function() {
        return { ...this.status };
    },

    /**
     * Check if currently online
     *
     * @returns {boolean} - True if online
     */
    isOnline: function() {
        return this.status.online;
    },

    /**
     * Get recommended quality based on network
     *
     * @returns {string} - Quality ('high', 'medium', 'low')
     */
    getRecommendedQuality: function() {
        if (!this.status.online) {
            return 'low'; // Use cached content
        }

        if (this.status.quality === 'fast') {
            return 'high';
        } else if (this.status.quality === 'slow') {
            return 'medium';
        } else {
            return 'low';
        }
    },

    // ========================================================================
    // EVENT HANDLING
    // ========================================================================

    /**
     * Handle online event from browser
     *
     * @private
     */
    _handleOnline: function() {
        console.log('[OfflineDetector] Browser reports online');
        // Trigger immediate check
        this.check();
    },

    /**
     * Handle offline event from browser
     *
     * @private
     */
    _handleOffline: function() {
        console.log('[OfflineDetector] Browser reports offline');
        this._updateStatus({
            online: false,
            quality: 'offline',
            speed: 0,
            latency: 0,
            lastCheck: new Date()
        });
    },

    /**
     * Start periodic connectivity checks
     *
     * @private
     */
    _startPeriodicChecks: function() {
        // Clear existing interval
        if (this.checkIntervalId) {
            clearInterval(this.checkIntervalId);
        }

        // Start new interval
        this.checkIntervalId = setInterval(() => {
            this.check();
        }, this.config.checkInterval);

        console.log(`[OfflineDetector] Periodic checks started (${this.config.checkInterval}ms)`);
    },

    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================

    /**
     * Add event listener
     *
     * @param {string} event - Event name (online, offline, quality-change)
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
                    console.error('[OfflineDetector] Event listener error:', error);
                }
            });
        }
    }
};

// ============================================================================
// CONSOLE HELPERS
// ============================================================================

/**
 * Show network status in console
 */
window.showNetworkStatus = function() {
    const status = OfflineDetector.getStatus();
    console.log('Network Status:', {
        online: status.online ? 'ONLINE' : 'OFFLINE',
        quality: status.quality.toUpperCase(),
        speed: status.speed > 0 ? status.speed + ' Mbps' : 'N/A',
        latency: status.latency > 0 ? status.latency + ' ms' : 'N/A',
        lastCheck: status.lastCheck ? status.lastCheck.toLocaleString() : 'Never',
        recommendedQuality: OfflineDetector.getRecommendedQuality()
    });
};

/**
 * Force network check
 */
window.checkNetwork = async function() {
    console.log('[OfflineDetector] Running manual network check...');
    const status = await OfflineDetector.check();
    showNetworkStatus();
    return status;
};

console.log('[OfflineDetector] Loaded (v1.0.0) - Use showNetworkStatus(), checkNetwork()');
