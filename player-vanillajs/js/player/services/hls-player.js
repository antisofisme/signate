/**
 * HLS Player Module
 * Handles HLS adaptive bitrate streaming with HLS.js
 */

window.HLSPlayer = class {
    constructor(videoElement) {
        this.video = videoElement;
        this.hls = null;
        this.currentQuality = 'auto';
        this.analytics = {
            qualityChanges: 0,
            bufferingEvents: 0,
            errors: 0,
            startTime: Date.now()
        };
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000; // Start with 1 second
        this.levels = [];
        this.isDestroyed = false;
        this.bufferCheckInterval = null;
    }

    /**
     * Check if HLS is supported
     */
    static isSupported() {
        return typeof Hls !== 'undefined' && Hls.isSupported();
    }

    /**
     * Check if native HLS is supported (Safari, iOS)
     */
    static isNativeSupported() {
        const video = document.createElement('video');
        return video.canPlayType('application/vnd.apple.mpegurl') !== '';
    }

    /**
     * Load HLS stream
     * @param {String} masterPlaylistUrl - URL to master.m3u8
     * @param {Object} options - Player options
     */
    loadSource(masterPlaylistUrl, options = {}) {
        console.log('[HLS] Loading source:', masterPlaylistUrl);

        // Clean up existing instance
        this.destroy();
        this.isDestroyed = false;

        const {
            autoplay = true,
            muted = false,
            startLevel = -1 // -1 = auto quality
        } = options;

        // Try HLS.js first
        if (HLSPlayer.isSupported()) {
            this._loadWithHLSjs(masterPlaylistUrl, { autoplay, muted, startLevel });
        }
        // Fallback to native HLS (Safari, iOS)
        else if (HLSPlayer.isNativeSupported()) {
            this._loadWithNativeHLS(masterPlaylistUrl, { autoplay, muted });
        }
        // No HLS support
        else {
            const error = 'HLS playback is not supported in this browser';
            console.error('[HLS]', error);
            throw new Error(error);
        }
    }

    /**
     * Load with HLS.js library
     */
    _loadWithHLSjs(url, options) {
        console.log('[HLS] Using HLS.js for playback');

        // Get saved quality preference
        const savedQuality = localStorage.getItem('preferredQuality');
        const startLevel = savedQuality === 'auto' || !savedQuality ? -1 : parseInt(savedQuality);

        // Create HLS instance with optimized config
        this.hls = new Hls({
            // Buffer configuration
            maxBufferLength: 30,           // 30 seconds of buffer
            maxMaxBufferLength: 60,        // Max 60 seconds buffer
            maxBufferSize: 60 * 1000 * 1000, // 60 MB buffer size
            maxBufferHole: 0.5,            // Max hole in buffer to skip

            // Quality selection
            startLevel: startLevel,        // Start quality (-1 = auto)
            capLevelToPlayerSize: true,    // Don't load higher than display size
            capLevelOnFPSDrop: true,       // Reduce quality on FPS drops

            // ABR (Adaptive Bitrate) tuning
            abrEwmaDefaultEstimate: 500000, // Conservative initial estimate (500 Kbps)
            abrEwmaFastLive: 3.0,          // Fast adaptation to bandwidth changes
            abrEwmaSlowLive: 9.0,          // Slow adaptation for stability
            abrBandWidthFactor: 0.95,      // Use 95% of estimated bandwidth
            abrBandWidthUpFactor: 0.7,     // Be more conservative when upgrading

            // Error recovery
            manifestLoadingTimeOut: 10000,
            manifestLoadingMaxRetry: 3,
            manifestLoadingRetryDelay: 1000,
            levelLoadingTimeOut: 10000,
            levelLoadingMaxRetry: 4,
            fragLoadingTimeOut: 20000,
            fragLoadingMaxRetry: 6,

            // Debug
            debug: false
        });

        // Load source and attach to video
        this.hls.loadSource(url);
        this.hls.attachMedia(this.video);

        // Set video attributes
        this.video.autoplay = options.autoplay;
        this.video.muted = options.muted;

        // Attach event handlers
        this._attachEventHandlers();

        // Update debug stats
        this._updateDebugStats('HLS.js');
    }

    /**
     * Load with native HLS support (Safari, iOS)
     */
    _loadWithNativeHLS(url, options) {
        console.log('[HLS] Using native HLS playback');

        this.video.src = url;
        this.video.autoplay = options.autoplay;
        this.video.muted = options.muted;

        // Native HLS doesn't provide quality control
        // Hide quality selector
        console.log('[HLS] Quality selection not available in native mode');

        // Basic event handlers
        this.video.addEventListener('loadedmetadata', () => {
            console.log('[HLS] Native HLS loaded');
        });

        this.video.addEventListener('error', (e) => {
            console.error('[HLS] Native HLS error:', e);
            this.analytics.errors++;
        });

        // Update debug stats
        this._updateDebugStats('Native HLS');
    }

    /**
     * Attach HLS.js event handlers
     */
    _attachEventHandlers() {
        if (!this.hls) return;

        // Manifest loaded - quality levels available
        this.hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
            console.log(`[HLS] Manifest loaded: ${data.levels.length} quality levels`);

            this.levels = data.levels;

            // Log available qualities
            data.levels.forEach((level, index) => {
                console.log(`[HLS] Level ${index}: ${level.width}x${level.height} @ ${(level.bitrate / 1000000).toFixed(2)} Mbps`);
            });

            // Populate quality selector
            if (window.QualitySelector) {
                window.QualitySelector.populateLevels(data.levels, (quality) => {
                    this.setQuality(quality);
                });
            }

            // Apply saved quality preference
            const savedQuality = localStorage.getItem('preferredQuality');
            if (savedQuality && savedQuality !== 'auto') {
                this.setQuality(parseInt(savedQuality));
            }
        });

        // Quality level switching
        this.hls.on(Hls.Events.LEVEL_SWITCHING, (event, data) => {
            const level = this.levels[data.level];
            console.log(`[HLS] Switching to quality: ${level.height}p @ ${(level.bitrate / 1000000).toFixed(2)} Mbps`);
        });

        // Quality level switched
        this.hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
            const level = this.levels[data.level];
            const qualityText = window.QualitySelector.getQualityLabel(level.height);

            console.log(`[HLS] Quality switched: ${qualityText} (${level.width}x${level.height})`);

            this.analytics.qualityChanges++;

            // Update quality selector UI
            if (window.QualitySelector) {
                window.QualitySelector.updateCurrentQuality(level);
                window.QualitySelector.showQualityNotification(qualityText);
            }

            // Update debug stats
            this._updateDebugStats();
        });

        // Fragment loading started
        this.hls.on(Hls.Events.FRAG_LOADING, (event, data) => {
            // Hide buffering indicator when loading starts
            this._hideBufferingIndicator();
        });

        // Fragment loaded successfully
        this.hls.on(Hls.Events.FRAG_LOADED, (event, data) => {
            const loadTime = data.stats.loading.end - data.stats.loading.start;
            const bandwidth = (data.frag.loaded * 8000) / loadTime; // bits per second

            // Update bandwidth display
            if (window.QualitySelector) {
                window.QualitySelector.updateBandwidth(bandwidth);
            }
        });

        // Buffer stalled - show loading
        this.hls.on(Hls.Events.BUFFER_STALLED, () => {
            console.warn('[HLS] Buffer stalled');
            this.analytics.bufferingEvents++;
            this._showBufferingIndicator();
            this._updateDebugStats();
        });

        // Buffer flushing (quality change)
        this.hls.on(Hls.Events.BUFFER_FLUSHING, () => {
            console.log('[HLS] Buffer flushing (quality change)');
        });

        // FPS drop detected
        this.hls.on(Hls.Events.FPS_DROP, (event, data) => {
            console.warn('[HLS] FPS drop detected:', data.currentDropped, 'frames');
        });

        // Error handling
        this.hls.on(Hls.Events.ERROR, (event, data) => {
            this._handleError(data);
        });

        // Start buffer monitoring
        this._startBufferMonitoring();
    }

    /**
     * Handle HLS errors with recovery
     */
    _handleError(data) {
        if (this.isDestroyed) return;

        console.error('[HLS] Error:', data.type, data.details, data.fatal);
        this.analytics.errors++;
        this._updateDebugStats();

        if (data.fatal) {
            switch(data.type) {
                case Hls.ErrorTypes.NETWORK_ERROR:
                    this._handleNetworkError(data);
                    break;
                case Hls.ErrorTypes.MEDIA_ERROR:
                    this._handleMediaError(data);
                    break;
                default:
                    this._handleFatalError(data);
                    break;
            }
        } else {
            // Non-fatal error, log and continue
            console.warn('[HLS] Non-fatal error, continuing playback');
        }
    }

    /**
     * Handle network errors with retry
     */
    _handleNetworkError(data) {
        console.error('[HLS] Fatal network error:', data.details);

        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            const delay = this.retryDelay * Math.pow(2, this.retryCount - 1); // Exponential backoff

            console.log(`[HLS] Retry ${this.retryCount}/${this.maxRetries} in ${delay}ms...`);

            setTimeout(() => {
                if (!this.isDestroyed && this.hls) {
                    console.log('[HLS] Attempting to recover from network error...');
                    this.hls.startLoad();
                }
            }, delay);
        } else {
            console.error('[HLS] Max retries reached for network error');
            this._handleFatalError(data);
        }
    }

    /**
     * Handle media errors with recovery
     */
    _handleMediaError(data) {
        console.error('[HLS] Fatal media error:', data.details);

        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            console.log(`[HLS] Attempting to recover from media error (${this.retryCount}/${this.maxRetries})...`);

            if (this.hls) {
                this.hls.recoverMediaError();
            }
        } else {
            console.error('[HLS] Max retries reached for media error');
            this._handleFatalError(data);
        }
    }

    /**
     * Handle unrecoverable fatal errors
     */
    _handleFatalError(data) {
        console.error('[HLS] Unrecoverable error:', data.type, data.details);

        // Show error to user
        if (window.PlayerUI) {
            window.PlayerUI.showError(`HLS Playback Error: ${data.details}`);
        }

        // Try to fallback to direct MP4 if available
        this._fallbackToDirectPlayback();
    }

    /**
     * Fallback to direct MP4 playback
     */
    _fallbackToDirectPlayback() {
        console.log('[HLS] Attempting fallback to direct MP4 playback...');

        // This will be handled by the playback module
        // Emit custom event for fallback
        const event = new CustomEvent('hls-fallback', {
            detail: { player: this }
        });
        window.dispatchEvent(event);
    }

    /**
     * Set quality level
     * @param {Number|String} quality - Quality index or 'auto'
     */
    setQuality(quality) {
        if (!this.hls) {
            console.warn('[HLS] Cannot set quality: HLS.js not initialized');
            return;
        }

        if (quality === 'auto' || quality === -1) {
            console.log('[HLS] Setting quality to AUTO');
            this.hls.currentLevel = -1;
            this.currentQuality = 'auto';
        } else {
            const levelIndex = parseInt(quality);
            if (levelIndex >= 0 && levelIndex < this.levels.length) {
                const level = this.levels[levelIndex];
                console.log(`[HLS] Setting quality to level ${levelIndex}: ${level.height}p`);
                this.hls.currentLevel = levelIndex;
                this.currentQuality = levelIndex;
            } else {
                console.warn('[HLS] Invalid quality level:', quality);
                return;
            }
        }

        // Save preference
        localStorage.setItem('preferredQuality', quality.toString());
    }

    /**
     * Get current quality level
     */
    getCurrentQuality() {
        if (!this.hls) return null;

        const currentLevel = this.hls.currentLevel;
        if (currentLevel === -1) return 'auto';

        return this.levels[currentLevel] || null;
    }

    /**
     * Show buffering indicator
     */
    _showBufferingIndicator() {
        const buffering = document.getElementById('buffering');
        if (buffering) {
            buffering.style.display = 'block';
        }
    }

    /**
     * Hide buffering indicator
     */
    _hideBufferingIndicator() {
        const buffering = document.getElementById('buffering');
        if (buffering) {
            buffering.style.display = 'none';
        }
    }

    /**
     * Start monitoring buffer level
     */
    _startBufferMonitoring() {
        // Stop existing interval
        if (this.bufferCheckInterval) {
            clearInterval(this.bufferCheckInterval);
        }

        // Check buffer every second
        this.bufferCheckInterval = setInterval(() => {
            if (this.isDestroyed || !this.video) return;

            const buffered = this.video.buffered;
            if (buffered.length > 0) {
                const currentTime = this.video.currentTime;
                const bufferEnd = buffered.end(buffered.length - 1);
                const bufferLength = bufferEnd - currentTime;

                // Update buffer display
                if (window.QualitySelector) {
                    window.QualitySelector.updateBuffer(bufferLength);
                }
            }
        }, 1000);
    }

    /**
     * Update debug stats overlay
     */
    _updateDebugStats(mode) {
        if (window.QualitySelector) {
            window.QualitySelector.updateHLSStats({
                mode: mode || (this.hls ? 'HLS.js' : 'Native'),
                qualityChanges: this.analytics.qualityChanges,
                bufferingEvents: this.analytics.bufferingEvents,
                errors: this.analytics.errors
            });
        }
    }

    /**
     * Destroy HLS instance and cleanup
     */
    destroy() {
        console.log('[HLS] Destroying player...');

        this.isDestroyed = true;

        // Stop buffer monitoring
        if (this.bufferCheckInterval) {
            clearInterval(this.bufferCheckInterval);
            this.bufferCheckInterval = null;
        }

        // Destroy HLS instance
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }

        // Reset state
        this.levels = [];
        this.retryCount = 0;
        this.currentQuality = 'auto';

        // Hide buffering indicator
        this._hideBufferingIndicator();

        console.log('[HLS] Player destroyed');
    }

    /**
     * Get analytics data
     */
    getAnalytics() {
        return {
            ...this.analytics,
            uptime: Date.now() - this.analytics.startTime,
            currentQuality: this.getCurrentQuality(),
            retryCount: this.retryCount
        };
    }
};
