/**
 * Device Controls Module
 * Low-level device control utilities for WebOS TV and browsers
 *
 * Provides hardware control APIs:
 * - Volume control
 * - Brightness control
 * - Power management
 * - System information
 * - Network controls
 *
 * Detects platform and uses appropriate APIs:
 * - WebOS TV: luna:// service APIs
 * - Browser: HTML5 APIs with fallbacks
 *
 * @version 1.0.0
 */

window.ShellDeviceControls = {
    /**
     * Platform detection
     */
    platform: null,
    isWebOS: false,
    isBrowser: false,

    /**
     * Initialize device controls
     */
    init: function() {
        this.platform = this._detectPlatform();
        this.isWebOS = ['webOS'].includes(this.platform);
        this.isBrowser = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Browser'].includes(this.platform);

        console.log('[DeviceControls] Platform detected:', this.platform);
        console.log('[DeviceControls] WebOS:', this.isWebOS);
        console.log('[DeviceControls] Browser:', this.isBrowser);
    },

    /**
     * Detect platform
     * @private
     */
    _detectPlatform: function() {
        const ua = navigator.userAgent.toLowerCase();
        if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
        if (ua.includes('tizen')) return 'Tizen';
        if (ua.includes('android tv')) return 'Android TV';
        if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
        if (ua.includes('firefox')) return 'Firefox';
        if (ua.includes('chrome')) return 'Chrome';
        if (ua.includes('safari')) return 'Safari';
        return 'Browser';
    },

    /**
     * Volume Controls
     */
    volume: {
        /**
         * Set volume level
         *
         * @param {number} level - Volume level (0-100)
         * @returns {Promise<Object>} - Result
         */
        set: async function(level) {
            // Validate
            if (level < 0 || level > 100) {
                throw new Error('Volume level must be between 0 and 100');
            }

            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.audio', {
                        method: 'setVolume',
                        parameters: { volume: level },
                        onSuccess: (res) => resolve({ level, success: true, api: 'webos' }),
                        onFailure: (err) => reject(new Error(err.errorText || 'WebOS volume API failed'))
                    });
                });
            }

            // Browser fallback
            localStorage.setItem('volume_preference', level);

            // Control video elements
            const videos = document.querySelectorAll('video');
            if (videos.length > 0) {
                videos.forEach(v => v.volume = level / 100);
                return { level, success: true, api: 'html5_video', affected_elements: videos.length };
            }

            return { level, success: true, api: 'preference_only' };
        },

        /**
         * Get current volume level
         *
         * @returns {Promise<number>} - Volume level (0-100)
         */
        get: async function() {
            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.audio', {
                        method: 'getVolume',
                        onSuccess: (res) => resolve(res.volume || 50),
                        onFailure: (err) => reject(new Error(err.errorText || 'Failed to get volume'))
                    });
                });
            }

            // Browser fallback
            const saved = localStorage.getItem('volume_preference');
            if (saved) return parseInt(saved);

            const video = document.querySelector('video');
            if (video) return Math.round(video.volume * 100);

            return 50; // Default
        },

        /**
         * Mute/unmute
         *
         * @param {boolean} mute - True to mute, false to unmute
         * @returns {Promise<Object>} - Result
         */
        setMute: async function(mute) {
            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.audio', {
                        method: 'setMute',
                        parameters: { mute: mute },
                        onSuccess: (res) => resolve({ muted: mute, success: true }),
                        onFailure: (err) => reject(new Error(err.errorText || 'Failed to set mute'))
                    });
                });
            }

            // Browser fallback
            const videos = document.querySelectorAll('video');
            videos.forEach(v => v.muted = mute);

            return { muted: mute, success: true, api: 'html5_video' };
        }
    },

    /**
     * Brightness Controls
     */
    brightness: {
        /**
         * Set brightness level
         *
         * @param {number} level - Brightness level (0-100)
         * @returns {Promise<Object>} - Result
         */
        set: async function(level) {
            // Validate
            if (level < 0 || level > 100) {
                throw new Error('Brightness level must be between 0 and 100');
            }

            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.settingsservice', {
                        method: 'setSystemSettings',
                        parameters: {
                            category: 'picture',
                            settings: { backlight: level }
                        },
                        onSuccess: (res) => resolve({ level, success: true, api: 'webos' }),
                        onFailure: (err) => reject(new Error(err.errorText || 'WebOS brightness API failed'))
                    });
                });
            }

            // Browser fallback: CSS filter
            const brightness = level / 100;
            document.body.style.filter = `brightness(${brightness})`;
            localStorage.setItem('brightness_preference', level);

            return { level, success: true, api: 'css_filter' };
        },

        /**
         * Get current brightness level
         *
         * @returns {Promise<number>} - Brightness level (0-100)
         */
        get: async function() {
            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.settingsservice', {
                        method: 'getSystemSettings',
                        parameters: { category: 'picture', keys: ['backlight'] },
                        onSuccess: (res) => resolve(res.settings.backlight || 50),
                        onFailure: (err) => reject(new Error(err.errorText || 'Failed to get brightness'))
                    });
                });
            }

            // Browser fallback
            const saved = localStorage.getItem('brightness_preference');
            return saved ? parseInt(saved) : 100;
        }
    },

    /**
     * Power Controls
     */
    power: {
        /**
         * Reboot device
         *
         * @param {number} delay - Delay in seconds before reboot
         * @returns {Promise<Object>} - Result
         */
        reboot: async function(delay = 1) {
            console.log(`[DeviceControls] Reboot requested (delay: ${delay}s)`);

            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve) => {
                    setTimeout(() => {
                        window.webOS.service.request('luna://com.webos.service.tvpower', {
                            method: 'power/setState',
                            parameters: { state: 'reboot' },
                            onSuccess: (res) => resolve({ rebooting: true, api: 'webos' }),
                            onFailure: (err) => resolve({ rebooting: false, error: err.errorText })
                        });
                    }, delay * 1000);
                });
            }

            // Browser fallback: reload page
            setTimeout(() => window.location.reload(), delay * 1000);
            return { rebooting: true, api: 'page_reload' };
        },

        /**
         * Power off device
         *
         * @returns {Promise<Object>} - Result
         */
        powerOff: async function() {
            console.log('[DeviceControls] Power off requested');

            // WebOS TV only
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.service.tvpower', {
                        method: 'power/turnOff',
                        onSuccess: (res) => resolve({ powering_off: true }),
                        onFailure: (err) => reject(new Error(err.errorText || 'Failed to power off'))
                    });
                });
            }

            throw new Error('Power off only available on WebOS TV');
        }
    },

    /**
     * System Information
     */
    system: {
        /**
         * Get system information
         *
         * @returns {Promise<Object>} - System info
         */
        getInfo: async function() {
            const info = {
                platform: window.ShellDeviceControls.platform,
                user_agent: navigator.userAgent,
                screen: {
                    width: window.screen.width,
                    height: window.screen.height,
                    color_depth: window.screen.colorDepth
                },
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                device_pixel_ratio: window.devicePixelRatio || 1,
                language: navigator.language,
                online: navigator.onLine,
                hardware_concurrency: navigator.hardwareConcurrency || null
            };

            // WebOS specific
            if (window.ShellDeviceControls.isWebOS && window.webOS) {
                info.webos = {
                    platform_version: window.webOS.platformVersion || null,
                    device_info: window.webOS.deviceInfo || null
                };
            }

            return info;
        },

        /**
         * Get memory info
         *
         * @returns {Object|null} - Memory info (Chrome only)
         */
        getMemoryInfo: function() {
            if (!performance.memory) return null;

            return {
                used_js_heap_size: performance.memory.usedJSHeapSize,
                total_js_heap_size: performance.memory.totalJSHeapSize,
                js_heap_size_limit: performance.memory.jsHeapSizeLimit,
                used_mb: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total_mb: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit_mb: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
        }
    },

    /**
     * Network Controls
     */
    network: {
        /**
         * Get network information
         *
         * @returns {Object} - Network info
         */
        getInfo: function() {
            const info = {
                online: navigator.onLine,
                connection: null
            };

            if (navigator.connection) {
                info.connection = {
                    effective_type: navigator.connection.effectiveType || null,
                    downlink: navigator.connection.downlink || null,
                    rtt: navigator.connection.rtt || null,
                    save_data: navigator.connection.saveData || false
                };
            }

            return info;
        },

        /**
         * Get WiFi info (WebOS only)
         *
         * @returns {Promise<Object>} - WiFi info
         */
        getWiFiInfo: async function() {
            // WebOS TV
            if (window.ShellDeviceControls.isWebOS && window.webOS && window.webOS.service) {
                return new Promise((resolve, reject) => {
                    window.webOS.service.request('luna://com.webos.connectionmanager', {
                        method: 'getStatus',
                        onSuccess: (res) => resolve(res),
                        onFailure: (err) => reject(new Error(err.errorText || 'Failed to get WiFi info'))
                    });
                });
            }

            throw new Error('WiFi info only available on WebOS TV');
        },

        /**
         * Ping test
         *
         * @param {string} url - URL to ping
         * @returns {Promise<number>} - Latency in ms
         */
        ping: async function(url = window.Config?.API_BASE_URL || window.ENV?.API_BASE_URL || 'http://localhost:8001') {
            const startTime = performance.now();

            try {
                await fetch(`${url}/api/health`, { method: 'HEAD', cache: 'no-cache' });
                const latency = Math.round(performance.now() - startTime);
                return latency;
            } catch (error) {
                throw new Error('Ping failed: ' + error.message);
            }
        }
    },

    /**
     * Display Controls
     */
    display: {
        /**
         * Enter fullscreen
         *
         * @returns {Promise<void>}
         */
        enterFullscreen: async function() {
            const elem = document.documentElement;
            const requestFullscreen = elem.requestFullscreen ||
                                     elem.webkitRequestFullscreen ||
                                     elem.mozRequestFullScreen ||
                                     elem.msRequestFullscreen;

            if (requestFullscreen) {
                await requestFullscreen.call(elem);
            } else {
                throw new Error('Fullscreen API not supported');
            }
        },

        /**
         * Exit fullscreen
         *
         * @returns {Promise<void>}
         */
        exitFullscreen: async function() {
            if (document.exitFullscreen) {
                await document.exitFullscreen();
            } else {
                throw new Error('Cannot exit fullscreen');
            }
        },

        /**
         * Check if fullscreen
         *
         * @returns {boolean}
         */
        isFullscreen: function() {
            return !!document.fullscreenElement;
        },

        /**
         * Get display orientation
         *
         * @returns {string} - Orientation ('portrait' or 'landscape')
         */
        getOrientation: function() {
            return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
        }
    }
};

// Auto-initialize
window.ShellDeviceControls.init();

console.log('[DeviceControls] Loaded - Platform:', window.ShellDeviceControls.platform);
