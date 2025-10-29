/**
 * Analytics Tracker for Digital Signage Viewer
 *
 * Client-side event tracking with buffered sending for optimal performance.
 * Tracks content playback, device metrics, and user interactions.
 *
 * Features:
 * - Event buffering (100 events or 30 seconds)
 * - Automatic retry on failure
 * - Session tracking
 * - Performance metrics
 * - Network-aware sending
 *
 * Usage:
 *   const tracker = new AnalyticsTracker(deviceId);
 *   tracker.trackContentPlay(contentId, { duration: 120 });
 *   tracker.trackHeartbeat();
 */

class AnalyticsTracker {
    /**
     * Create analytics tracker instance
     * @param {number} deviceId - Device ID from activation
     * @param {object} options - Configuration options
     */
    constructor(deviceId, options = {}) {
        this.deviceId = deviceId;
        this.buffer = [];
        this.bufferSize = options.bufferSize || 100;
        this.flushInterval = options.flushInterval || 30000; // 30 seconds
        this.retryAttempts = options.retryAttempts || 3;
        this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                          options.apiBaseUrl ||
                          'http://localhost:8001';

        // Session tracking
        this.sessionId = this.generateSessionId();
        this.sessionStart = Date.now();

        // State
        this.isEnabled = true;
        this.isFlushing = false;
        this.flushTimer = null;

        // Stats
        this.stats = {
            totalEvents: 0,
            successfulFlushes: 0,
            failedFlushes: 0,
            eventsDropped: 0
        };

        // Current playback tracking
        this.currentPlayback = null;

        // Initialize
        this.startFlushTimer();
        this.setupVisibilityTracking();

        console.log(`[Analytics] Tracker initialized for device ${deviceId}`);
    }

    /**
     * Generate unique session ID
     * @returns {string} Session ID
     */
    generateSessionId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Track generic event
     * @param {string} eventType - Event type
     * @param {object} data - Event data (metrics and metadata)
     */
    track(eventType, data = {}) {
        if (!this.isEnabled) {
            return;
        }

        const event = {
            event_type: eventType,
            device_id: this.deviceId,
            session_id: this.sessionId,
            metrics: data.metrics || {},
            metadata: {
                ...data.metadata || {},
                timestamp_client: new Date().toISOString(),
                user_agent: navigator.userAgent,
                screen_resolution: `${screen.width}x${screen.height}`,
                viewport: `${window.innerWidth}x${window.innerHeight}`,
                connection: this.getConnectionInfo()
            }
        };

        // Add content_id if present
        if (data.content_id) {
            event.content_id = data.content_id;
        }

        this.buffer.push(event);
        this.stats.totalEvents++;

        // Auto-flush if buffer full
        if (this.buffer.length >= this.bufferSize) {
            this.flush();
        }
    }

    /**
     * Track content playback start
     * @param {number} contentId - Content ID
     * @param {object} metadata - Additional metadata
     */
    trackContentPlay(contentId, metadata = {}) {
        this.currentPlayback = {
            contentId: contentId,
            startTime: Date.now(),
            pausedTime: 0,
            totalPauseDuration: 0
        };

        this.track('content_play', {
            content_id: contentId,
            metadata: {
                ...metadata,
                playback_id: this.generateSessionId()
            }
        });
    }

    /**
     * Track content playback pause
     * @param {number} contentId - Content ID
     */
    trackContentPause(contentId) {
        if (this.currentPlayback && this.currentPlayback.contentId === contentId) {
            this.currentPlayback.pausedTime = Date.now();
        }

        this.track('content_pause', {
            content_id: contentId,
            metrics: {
                time_played: this.getPlaybackDuration()
            }
        });
    }

    /**
     * Track content playback resume
     * @param {number} contentId - Content ID
     */
    trackContentResume(contentId) {
        if (this.currentPlayback && this.currentPlayback.pausedTime) {
            const pauseDuration = Date.now() - this.currentPlayback.pausedTime;
            this.currentPlayback.totalPauseDuration += pauseDuration;
            this.currentPlayback.pausedTime = 0;
        }

        this.track('content_resume', {
            content_id: contentId
        });
    }

    /**
     * Track content playback completion
     * @param {number} contentId - Content ID
     * @param {object} metrics - Playback metrics
     */
    trackContentComplete(contentId, metrics = {}) {
        const duration = this.getPlaybackDuration();

        this.track('content_complete', {
            content_id: contentId,
            metrics: {
                duration: duration,
                completion_rate: 1.0,
                ...metrics
            }
        });

        this.currentPlayback = null;
    }

    /**
     * Track content playback error
     * @param {number} contentId - Content ID
     * @param {Error|string} error - Error object or message
     */
    trackContentError(contentId, error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        const errorStack = error instanceof Error ? error.stack : undefined;

        this.track('content_error', {
            content_id: contentId,
            metadata: {
                error_message: errorMessage,
                error_stack: errorStack,
                time_played: this.getPlaybackDuration()
            }
        });

        this.currentPlayback = null;
    }

    /**
     * Track device heartbeat
     * @param {object} metrics - Device metrics (CPU, memory, etc.)
     */
    trackHeartbeat(metrics = {}) {
        const heartbeatMetrics = {
            uptime: this.getUptime(),
            memory_usage: this.getMemoryUsage(),
            connection_speed: this.getConnectionSpeed(),
            ...metrics
        };

        this.track('heartbeat', {
            metrics: heartbeatMetrics,
            metadata: {
                page_visible: !document.hidden,
                battery_level: this.getBatteryLevel()
            }
        });
    }

    /**
     * Track device boot/initialization
     */
    trackDeviceBoot() {
        this.track('device_boot', {
            metadata: {
                platform: this.detectPlatform(),
                device_info: this.getDeviceInfo()
            }
        });
    }

    /**
     * Track device shutdown/unload
     */
    trackDeviceShutdown() {
        this.track('device_shutdown', {
            metrics: {
                session_duration: this.getSessionDuration()
            }
        });

        // Force immediate flush
        this.flush(true);
    }

    /**
     * Flush event buffer to server
     * @param {boolean} sync - Use synchronous request (for unload)
     */
    async flush(sync = false) {
        if (this.buffer.length === 0 || this.isFlushing) {
            return;
        }

        this.isFlushing = true;

        // Copy and clear buffer
        const events = [...this.buffer];
        this.buffer = [];

        try {
            if (sync) {
                // Synchronous flush for page unload
                this.flushSync(events);
            } else {
                // Async flush (normal operation)
                await this.flushAsync(events);
            }

            this.stats.successfulFlushes++;
            console.log(`[Analytics] Flushed ${events.length} events`);

        } catch (error) {
            console.error('[Analytics] Flush failed:', error);
            this.stats.failedFlushes++;

            // Re-add events to buffer (up to buffer size limit)
            const keepCount = Math.min(events.length, this.bufferSize - this.buffer.length);
            if (keepCount > 0) {
                this.buffer.unshift(...events.slice(0, keepCount));
            }
            this.stats.eventsDropped += (events.length - keepCount);
        } finally {
            this.isFlushing = false;
        }
    }

    /**
     * Async flush using fetch API
     * @param {Array} events - Events to send
     */
    async flushAsync(events) {
        const response = await fetch(`${this.apiBaseUrl}/api/analytics/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ events })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    }

    /**
     * Sync flush using sendBeacon (for page unload)
     * @param {Array} events - Events to send
     */
    flushSync(events) {
        const data = JSON.stringify({ events });
        const blob = new Blob([data], { type: 'application/json' });

        const sent = navigator.sendBeacon(
            `${this.apiBaseUrl}/api/analytics/events`,
            blob
        );

        if (!sent) {
            throw new Error('sendBeacon failed');
        }
    }

    /**
     * Start automatic flush timer
     */
    startFlushTimer() {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }

        this.flushTimer = setInterval(() => {
            this.flush();
        }, this.flushInterval);
    }

    /**
     * Stop flush timer
     */
    stopFlushTimer() {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
            this.flushTimer = null;
        }
    }

    /**
     * Setup page visibility tracking
     */
    setupVisibilityTracking() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page hidden - flush immediately
                this.flush();
            }
        });

        // Flush on page unload
        window.addEventListener('beforeunload', () => {
            this.trackDeviceShutdown();
        });
    }

    // ========================================================================
    // HELPER METHODS
    // ========================================================================

    /**
     * Get current playback duration in seconds
     */
    getPlaybackDuration() {
        if (!this.currentPlayback) {
            return 0;
        }

        const elapsed = Date.now() - this.currentPlayback.startTime;
        const active = elapsed - this.currentPlayback.totalPauseDuration;
        return Math.floor(active / 1000);
    }

    /**
     * Get session duration in seconds
     */
    getSessionDuration() {
        return Math.floor((Date.now() - this.sessionStart) / 1000);
    }

    /**
     * Get device uptime (approximation)
     */
    getUptime() {
        if (performance && performance.timing) {
            return Math.floor((Date.now() - performance.timing.navigationStart) / 1000);
        }
        return this.getSessionDuration();
    }

    /**
     * Get memory usage (if available)
     */
    getMemoryUsage() {
        if (performance && performance.memory) {
            const used = performance.memory.usedJSHeapSize;
            const total = performance.memory.totalJSHeapSize;
            return Math.round((used / total) * 100);
        }
        return null;
    }

    /**
     * Get connection information
     */
    getConnectionInfo() {
        if (navigator.connection) {
            return {
                type: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
        }
        return null;
    }

    /**
     * Get connection speed (Mbps estimate)
     */
    getConnectionSpeed() {
        if (navigator.connection && navigator.connection.downlink) {
            return navigator.connection.downlink;
        }
        return null;
    }

    /**
     * Get battery level (if available)
     */
    getBatteryLevel() {
        // Battery API is async and deprecated, skip for now
        return null;
    }

    /**
     * Detect platform (WebOS, Browser, etc.)
     */
    detectPlatform() {
        const ua = navigator.userAgent.toLowerCase();

        if (ua.includes('web0s')) {
            return 'webos';
        } else if (ua.includes('tizen')) {
            return 'tizen';
        } else if (ua.includes('android')) {
            return 'android';
        } else {
            return 'browser';
        }
    }

    /**
     * Get device information
     */
    getDeviceInfo() {
        return {
            user_agent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                pixelRatio: window.devicePixelRatio
            },
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        };
    }

    /**
     * Get tracker statistics
     */
    getStats() {
        return {
            ...this.stats,
            buffer_size: this.buffer.length,
            session_duration: this.getSessionDuration(),
            is_enabled: this.isEnabled
        };
    }

    /**
     * Enable tracking
     */
    enable() {
        this.isEnabled = true;
        console.log('[Analytics] Tracking enabled');
    }

    /**
     * Disable tracking
     */
    disable() {
        this.isEnabled = false;
        console.log('[Analytics] Tracking disabled');
    }

    /**
     * Destroy tracker instance
     */
    destroy() {
        this.stopFlushTimer();
        this.flush(true);
        console.log('[Analytics] Tracker destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsTracker;
}
