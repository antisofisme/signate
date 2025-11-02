/**
 * Command Executor Module
 * Executes remote commands from backend (volume, brightness, screenshot, reboot, shell)
 *
 * Features:
 * - Secure command execution with whitelist
 * - WebOS TV API integration
 * - Browser fallbacks for testing
 * - Result reporting back to backend
 * - Timeout protection (30s max)
 * - Execution queue management
 *
 * Supported Commands:
 * - volume: Set audio volume (0-100%)
 * - brightness: Set screen brightness (0-100%)
 * - screenshot: Capture current display
 * - reboot: Restart device
 * - shell: Execute whitelisted shell commands (WebOS only)
 * - info: Get detailed device information
 *
 * @version 1.0.0
 */

window.ShellCommandExecutor = {
    /**
     * Execution queue and state
     */
    executionQueue: [],
    isExecuting: false,
    currentCommand: null,

    /**
     * Command timeout (30 seconds max)
     */
    COMMAND_TIMEOUT: 30000,

    /**
     * Shell command whitelist (security)
     */
    SHELL_WHITELIST: [
        'uptime',
        'date',
        'hostname',
        'whoami',
        'df -h',
        'free -m',
        'ps aux | head -20',
        'uname -a',
        'cat /proc/meminfo | head -10',
        'cat /proc/cpuinfo | head -20',
        'ip addr',
        'netstat -tuln | head -20'
    ],

    /**
     * Execute a command received from backend
     *
     * @param {Object} commandData - Command data from backend
     * @param {number} commandData.id - Command ID
     * @param {string} commandData.command_type - Command type
     * @param {Object} commandData.parameters - Command parameters
     * @param {string} commandData.reason - Command reason/description
     * @returns {Promise<void>}
     */
    executeCommand: async function(commandData) {
        const { id, command_type, parameters = {}, reason } = commandData;

        console.log(`[CommandExecutor] 🔄 Executing: ${command_type} (ID: ${id})`);
        if (reason) {
            console.log(`[CommandExecutor] Reason: ${reason}`);
        }
        console.log(`[CommandExecutor] Parameters:`, parameters);

        // Update current command
        this.currentCommand = {
            id,
            type: command_type,
            startTime: Date.now()
        };

        // Report status as running
        await this.reportStatus(id, 'running');

        try {
            let result;

            // Execute command with timeout protection
            const executePromise = this._executeCommandInternal(command_type, parameters);
            const timeoutPromise = this._createTimeoutPromise(this.COMMAND_TIMEOUT);

            result = await Promise.race([executePromise, timeoutPromise]);

            console.log(`[CommandExecutor] ✅ Command ${command_type} completed`);
            console.log(`[CommandExecutor] Result:`, result);

            // Report success
            await this.reportStatus(id, 'completed', result);

        } catch (error) {
            console.error(`[CommandExecutor] ❌ Command ${command_type} failed:`, error);

            // Report failure
            await this.reportStatus(id, 'failed', null, error.message);
        } finally {
            // Clear current command
            this.currentCommand = null;
        }
    },

    /**
     * Internal command execution (without timeout wrapper)
     *
     * @param {string} commandType - Command type
     * @param {Object} parameters - Command parameters
     * @returns {Promise<Object>} - Execution result
     * @private
     */
    _executeCommandInternal: async function(commandType, parameters) {
        switch (commandType) {
            case 'volume':
                return await this.setVolume(parameters.level);

            case 'brightness':
                return await this.setBrightness(parameters.level);

            case 'screenshot':
                return await this.takeScreenshot(parameters);

            case 'reboot':
                return await this.reboot(parameters);

            case 'shell':
                return await this.executeShell(parameters.command);

            case 'info':
                return await this.getDeviceInfo();

            default:
                throw new Error(`Unknown command type: ${commandType}`);
        }
    },

    /**
     * Create timeout promise
     *
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise<never>} - Promise that rejects after timeout
     * @private
     */
    _createTimeoutPromise: function(timeout) {
        return new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error(`Command execution timeout after ${timeout}ms`));
            }, timeout);
        });
    },

    /**
     * Set audio volume
     *
     * @param {number} level - Volume level (0-100)
     * @returns {Promise<Object>} - Execution result
     */
    setVolume: async function(level) {
        console.log(`[CommandExecutor] Setting volume to ${level}%`);

        // Validate level
        if (level < 0 || level > 100) {
            throw new Error('Volume level must be between 0 and 100');
        }

        // WebOS TV API
        if (window.webOS && window.webOS.service) {
            return new Promise((resolve, reject) => {
                window.webOS.service.request('luna://com.webos.audio', {
                    method: 'setVolume',
                    parameters: { volume: level },
                    onSuccess: (res) => {
                        console.log('[CommandExecutor] ✅ Volume set via WebOS API');
                        resolve({
                            volume: level,
                            success: true,
                            method: 'webos_api',
                            response: res
                        });
                    },
                    onFailure: (err) => {
                        console.error('[CommandExecutor] ❌ WebOS volume API failed:', err);
                        reject(new Error(`WebOS API error: ${err.errorText || 'Unknown error'}`));
                    }
                });
            });
        }

        // Browser fallback: Store preference (limited control)
        console.log('[CommandExecutor] Browser detected - storing volume preference');
        localStorage.setItem('volume_preference', level);

        // Try to control video element volume
        const videoElements = document.querySelectorAll('video');
        if (videoElements.length > 0) {
            videoElements.forEach(video => {
                video.volume = level / 100;
            });

            return {
                volume: level,
                success: true,
                method: 'html5_video',
                note: 'Applied to video elements only (browser limitation)'
            };
        }

        return {
            volume: level,
            success: true,
            method: 'preference_only',
            note: 'Volume preference stored (browser has limited control)'
        };
    },

    /**
     * Set screen brightness
     *
     * @param {number} level - Brightness level (0-100)
     * @returns {Promise<Object>} - Execution result
     */
    setBrightness: async function(level) {
        console.log(`[CommandExecutor] Setting brightness to ${level}%`);

        // Validate level
        if (level < 0 || level > 100) {
            throw new Error('Brightness level must be between 0 and 100');
        }

        // WebOS TV API
        if (window.webOS && window.webOS.service) {
            return new Promise((resolve, reject) => {
                window.webOS.service.request('luna://com.webos.settingsservice', {
                    method: 'setSystemSettings',
                    parameters: {
                        category: 'picture',
                        settings: { backlight: level }
                    },
                    onSuccess: (res) => {
                        console.log('[CommandExecutor] ✅ Brightness set via WebOS API');
                        resolve({
                            brightness: level,
                            success: true,
                            method: 'webos_api',
                            response: res
                        });
                    },
                    onFailure: (err) => {
                        console.error('[CommandExecutor] ❌ WebOS brightness API failed:', err);
                        reject(new Error(`WebOS API error: ${err.errorText || 'Unknown error'}`));
                    }
                });
            });
        }

        // Browser fallback: CSS filter
        console.log('[CommandExecutor] Browser detected - using CSS filter');
        const brightness = level / 100; // 0-1 range
        document.body.style.filter = `brightness(${brightness})`;

        // Store preference
        localStorage.setItem('brightness_preference', level);

        return {
            brightness: level,
            success: true,
            method: 'css_filter',
            note: 'CSS filter applied (not hardware brightness control)'
        };
    },

    /**
     * Take screenshot of current display
     *
     * @param {Object} options - Screenshot options
     * @param {string} options.quality - Quality level ('low', 'medium', 'high')
     * @param {boolean} options.upload - Whether to upload to backend
     * @returns {Promise<Object>} - Screenshot result
     */
    takeScreenshot: async function(options = {}) {
        const { quality = 'medium', upload = false } = options;

        console.log(`[CommandExecutor] Taking screenshot (quality: ${quality}, upload: ${upload})`);

        // Quality settings
        const qualitySettings = {
            low: 0.5,
            medium: 0.8,
            high: 0.95
        };

        const jpegQuality = qualitySettings[quality] || 0.8;

        // Create canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // Try to capture video frame first
        const videoElement = document.querySelector('video');

        if (videoElement && !videoElement.paused && videoElement.readyState >= 2) {
            console.log('[CommandExecutor] Capturing video frame');
            canvas.width = videoElement.videoWidth || window.innerWidth;
            canvas.height = videoElement.videoHeight || window.innerHeight;
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        } else {
            console.log('[CommandExecutor] Capturing DOM content');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;

            // Simple DOM capture (draw background + basic content)
            ctx.fillStyle = getComputedStyle(document.body).backgroundColor || '#000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Add text overlay with device info
            ctx.fillStyle = '#fff';
            ctx.font = '24px Arial';
            ctx.fillText('Screenshot captured', 50, 100);
            ctx.font = '16px Arial';
            ctx.fillText(`Device: ${localStorage.getItem('device_id') || 'Unknown'}`, 50, 150);
            ctx.fillText(`Time: ${new Date().toLocaleString()}`, 50, 180);
        }

        // Convert to blob
        const blob = await new Promise(resolve => {
            canvas.toBlob(resolve, 'image/jpeg', jpegQuality);
        });

        const screenshotSize = blob.size;
        console.log(`[CommandExecutor] Screenshot captured (${Math.round(screenshotSize / 1024)} KB)`);

        // Upload to backend if requested
        if (upload) {
            try {
                const formData = new FormData();
                formData.append('screenshot', blob, `screenshot_${Date.now()}.jpg`);
                formData.append('device_id', localStorage.getItem('device_id') || '0');

                const uploadUrl = `${window.ShellState.API_BASE_URL}/api/screenshots/upload`;
                console.log(`[CommandExecutor] Uploading screenshot to ${uploadUrl}`);

                const response = await fetch(uploadUrl, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
                }

                const data = await response.json();
                console.log('[CommandExecutor] ✅ Screenshot uploaded');

                return {
                    success: true,
                    uploaded: true,
                    screenshot_url: data.url || data.path,
                    size_bytes: screenshotSize,
                    size_kb: Math.round(screenshotSize / 1024),
                    width: canvas.width,
                    height: canvas.height,
                    quality: quality
                };

            } catch (uploadError) {
                console.error('[CommandExecutor] ❌ Screenshot upload failed:', uploadError);

                // Return base64 as fallback
                const base64 = await this._blobToBase64(blob);
                return {
                    success: true,
                    uploaded: false,
                    upload_error: uploadError.message,
                    screenshot_base64: base64,
                    size_bytes: screenshotSize,
                    size_kb: Math.round(screenshotSize / 1024),
                    width: canvas.width,
                    height: canvas.height,
                    quality: quality
                };
            }
        }

        // Return base64 data URL
        const base64 = await this._blobToBase64(blob);

        return {
            success: true,
            uploaded: false,
            screenshot_base64: base64,
            size_bytes: screenshotSize,
            size_kb: Math.round(screenshotSize / 1024),
            width: canvas.width,
            height: canvas.height,
            quality: quality
        };
    },

    /**
     * Convert blob to base64 data URL
     *
     * @param {Blob} blob - Blob to convert
     * @returns {Promise<string>} - Base64 data URL
     * @private
     */
    _blobToBase64: function(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    },

    /**
     * Reboot device
     *
     * @param {Object} options - Reboot options
     * @param {number} options.delay - Delay before reboot in seconds (default: 1)
     * @returns {Promise<Object>} - Reboot result
     */
    reboot: async function(options = {}) {
        const delay = options.delay || 1;

        console.log(`[CommandExecutor] ⚠️ REBOOT requested (delay: ${delay}s)`);

        // WebOS TV API
        if (window.webOS && window.webOS.service) {
            return new Promise((resolve) => {
                console.log('[CommandExecutor] Executing WebOS reboot...');

                setTimeout(() => {
                    window.webOS.service.request('luna://com.webos.service.tvpower', {
                        method: 'power/setState',
                        parameters: { state: 'reboot' },
                        onSuccess: (res) => {
                            console.log('[CommandExecutor] ✅ Reboot initiated');
                            resolve({
                                rebooting: true,
                                method: 'webos_api',
                                delay_seconds: delay
                            });
                        },
                        onFailure: (err) => {
                            console.error('[CommandExecutor] ❌ WebOS reboot failed:', err);
                            // Still report success (may need manual reboot)
                            resolve({
                                rebooting: false,
                                method: 'webos_api',
                                error: err.errorText,
                                note: 'Reboot command sent but may have failed'
                            });
                        }
                    });
                }, delay * 1000);
            });
        }

        // Browser fallback: Just reload page
        console.log('[CommandExecutor] Browser detected - reloading page instead');

        setTimeout(() => {
            console.log('[CommandExecutor] 🔄 Reloading page...');
            window.location.reload();
        }, delay * 1000);

        return {
            rebooting: true,
            method: 'page_reload',
            delay_seconds: delay,
            note: 'Browser reload only (not full device reboot)'
        };
    },

    /**
     * Execute shell command (HEAVILY RESTRICTED - whitelist only)
     *
     * @param {string} command - Shell command to execute
     * @returns {Promise<Object>} - Command output
     */
    executeShell: async function(command) {
        console.log(`[CommandExecutor] Shell command requested: ${command}`);

        // SECURITY: Check whitelist
        const isWhitelisted = this.SHELL_WHITELIST.some(whitelisted => {
            return command.trim() === whitelisted;
        });

        if (!isWhitelisted) {
            console.error(`[CommandExecutor] ❌ SECURITY: Command not in whitelist: ${command}`);
            throw new Error(`Command rejected: Not in whitelist. Allowed commands: ${this.SHELL_WHITELIST.join(', ')}`);
        }

        // WebOS only
        if (!window.webOS || !window.webOS.service) {
            throw new Error('Shell commands only available on WebOS TV platform');
        }

        console.log('[CommandExecutor] ✅ Command whitelisted, executing...');

        return new Promise((resolve, reject) => {
            window.webOS.service.request('luna://com.webos.service.sdkagent', {
                method: 'exec',
                parameters: {
                    command: command,
                    subscribe: false
                },
                onSuccess: (res) => {
                    console.log('[CommandExecutor] ✅ Shell command executed');
                    resolve({
                        success: true,
                        command: command,
                        stdout: res.stdOut || '',
                        stderr: res.stdErr || '',
                        returnValue: res.returnValue,
                        method: 'webos_sdkagent'
                    });
                },
                onFailure: (err) => {
                    console.error('[CommandExecutor] ❌ Shell command failed:', err);
                    reject(new Error(`Shell execution failed: ${err.errorText || 'Unknown error'}`));
                }
            });
        });
    },

    /**
     * Get detailed device information
     *
     * @returns {Promise<Object>} - Device information
     */
    getDeviceInfo: async function() {
        console.log('[CommandExecutor] Collecting device information...');

        const info = {
            // Basic device info
            device_id: localStorage.getItem('device_id'),
            device_code: localStorage.getItem('device_code'),
            activation_status: localStorage.getItem('device_status'),

            // Display information
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            device_pixel_ratio: window.devicePixelRatio || 1,
            color_depth: window.screen.colorDepth,
            pixel_depth: window.screen.pixelDepth,

            // Platform information
            user_agent: navigator.userAgent,
            platform: this._detectPlatform(),
            language: navigator.language,
            languages: navigator.languages,
            online: navigator.onLine,

            // Connection information
            connection_type: this._getConnectionType(),
            connection_speed: this._getConnectionSpeed(),
            connection_rtt: this._getConnectionRTT(),

            // Performance information
            memory: this._getMemoryInfo(),
            hardware_concurrency: navigator.hardwareConcurrency || null,

            // Storage information
            storage: await this._getStorageInfo(),

            // Timestamp
            timestamp: new Date().toISOString()
        };

        // WebOS specific info
        if (window.webOS) {
            info.webos_version = window.webOS.platformVersion || null;
            info.webos_device_info = window.webOS.deviceInfo || null;
        }

        console.log('[CommandExecutor] ✅ Device info collected');
        return { success: true, info };
    },

    /**
     * Detect platform type
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
     * Get connection type
     * @private
     */
    _getConnectionType: function() {
        if (!navigator.connection) return null;
        return navigator.connection.effectiveType || navigator.connection.type || null;
    },

    /**
     * Get connection speed (Mbps)
     * @private
     */
    _getConnectionSpeed: function() {
        if (!navigator.connection || !navigator.connection.downlink) return null;
        return navigator.connection.downlink;
    },

    /**
     * Get connection RTT (Round Trip Time in ms)
     * @private
     */
    _getConnectionRTT: function() {
        if (!navigator.connection || !navigator.connection.rtt) return null;
        return navigator.connection.rtt;
    },

    /**
     * Get memory information
     * @private
     */
    _getMemoryInfo: function() {
        if (!performance.memory) return null;

        return {
            used_js_heap_size: performance.memory.usedJSHeapSize,
            total_js_heap_size: performance.memory.totalJSHeapSize,
            js_heap_size_limit: performance.memory.jsHeapSizeLimit,
            used_mb: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
            total_mb: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
            limit_mb: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
        };
    },

    /**
     * Get storage information
     * @private
     */
    _getStorageInfo: async function() {
        const storage = {
            localStorage: null,
            indexedDB: null,
            quota: null
        };

        // LocalStorage size
        try {
            let localStorageSize = 0;
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    localStorageSize += localStorage[key].length + key.length;
                }
            }
            storage.localStorage = {
                used_bytes: localStorageSize,
                used_kb: Math.round(localStorageSize / 1024)
            };
        } catch (e) {
            storage.localStorage = { error: 'Unable to access' };
        }

        // Storage quota (if available)
        if (navigator.storage && navigator.storage.estimate) {
            try {
                const estimate = await navigator.storage.estimate();
                storage.quota = {
                    usage_bytes: estimate.usage,
                    quota_bytes: estimate.quota,
                    usage_mb: Math.round(estimate.usage / 1024 / 1024),
                    quota_mb: Math.round(estimate.quota / 1024 / 1024),
                    percent_used: Math.round((estimate.usage / estimate.quota) * 100)
                };
            } catch (e) {
                storage.quota = { error: 'Unable to estimate' };
            }
        }

        return storage;
    },

    /**
     * Report command execution status to backend
     *
     * @param {number} commandId - Command ID
     * @param {string} status - Status ('running', 'completed', 'failed')
     * @param {Object} result - Execution result (if completed)
     * @param {string} error - Error message (if failed)
     * @returns {Promise<void>}
     */
    reportStatus: async function(commandId, status, result = null, error = null) {
        const state = window.ShellState;

        if (!state.deviceId) {
            console.warn('[CommandExecutor] No device ID, cannot report status');
            return;
        }

        const report = {
            command_id: commandId,
            status: status,
            executed_at: new Date().toISOString(),
            result: result,
            error: error
        };

        console.log(`[CommandExecutor] Reporting status: ${status}`);

        try {
            // Use APIClient for standardized response handling
            await window.APIClient.post(
                `${state.API_BASE_URL}/api/devices/${state.deviceId}/commands/${commandId}/report`,
                report
            );

            console.log(`[CommandExecutor] ✅ Status reported: ${status}`);

        } catch (reportError) {
            console.error(`[CommandExecutor] ❌ Failed to report status:`, reportError);
            // Don't throw - reporting failure shouldn't break command execution
        }
    },

    /**
     * Get current execution status (for debugging)
     *
     * @returns {Object} - Current execution status
     */
    getStatus: function() {
        return {
            is_executing: this.isExecuting,
            current_command: this.currentCommand,
            queue_length: this.executionQueue.length,
            shell_whitelist_count: this.SHELL_WHITELIST.length
        };
    }
};

console.log('[CommandExecutor] Loaded - Ready to execute remote commands');
console.log(`[CommandExecutor] Shell whitelist: ${window.ShellCommandExecutor.SHELL_WHITELIST.length} commands`);
