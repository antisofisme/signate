/**
 * Shared Logger Module
 * Centralized logging with levels, filtering, and backend sync
 *
 * @features
 * - Multiple log levels (debug, log, info, warn, error)
 * - Enable/disable logging via localStorage
 * - Automatic backend sync for errors
 * - Console passthrough for development
 * - Structured logging with timestamps
 *
 * @usage
 * ```javascript
 * SharedLogger.debug('Debugging info');
 * SharedLogger.log('Normal log');
 * SharedLogger.info('Information');
 * SharedLogger.warn('Warning');
 * SharedLogger.error('Error occurred');
 *
 * // Configure log level
 * SharedLogger.setLevel('warn'); // Only warn and error
 * SharedLogger.setLevel('debug'); // All logs
 *
 * // Enable/disable
 * SharedLogger.enable();
 * SharedLogger.disable();
 * ```
 */

(function() {
    'use strict';

    // Log levels (higher number = more important)
    const LOG_LEVELS = {
        debug: 0,
        log: 1,
        info: 2,
        warn: 3,
        error: 4,
        silent: 999
    };

    // Private state
    let currentLevel = LOG_LEVELS.log; // Default: show log and above
    let enabled = true;
    let logBuffer = [];
    const MAX_BUFFER_SIZE = 50;

    // Store original console for passthrough
    const originalConsole = {
        debug: console.debug.bind(console),
        log: console.log.bind(console),
        info: console.info.bind(console),
        warn: console.warn.bind(console),
        error: console.error.bind(console)
    };

    /**
     * Check if log level should be displayed
     */
    function shouldLog(level) {
        if (!enabled) return false;
        return LOG_LEVELS[level] >= currentLevel;
    }

    /**
     * Format log arguments to string
     */
    function formatArgs(args) {
        return args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
    }

    /**
     * Add log entry to buffer
     */
    function bufferLog(level, message) {
        logBuffer.push({
            level: level,
            message: message,
            timestamp: new Date().toISOString(),
            source: 'player'
        });

        // Keep buffer size manageable
        if (logBuffer.length > MAX_BUFFER_SIZE) {
            logBuffer = logBuffer.slice(-MAX_BUFFER_SIZE);
        }

        // Auto-send errors to backend
        if (level === 'error' && window.SharedDeviceState) {
            const device = window.SharedDeviceState.getDevice();
            if (device && device.id) {
                sendLogsToBackend();
            }
        }
    }

    /**
     * Send buffered logs to backend
     */
    async function sendLogsToBackend() {
        if (logBuffer.length === 0) return;
        if (!window.SharedAPIClient || !window.SharedDeviceState) return;

        const device = window.SharedDeviceState.getDevice();
        if (!device || !device.id) return;

        const logsToSend = [...logBuffer];
        logBuffer = []; // Clear buffer

        try {
            await window.SharedAPIClient.post(
                `${window.SharedENV.API_BASE_URL}/api/client/logs/batch`,
                {
                    device_id: device.id,
                    logs: logsToSend
                }
            );
        } catch (error) {
            // Silent fail - don't log error to avoid recursion
            originalConsole.error('[SharedLogger] Failed to send logs:', error);
        }
    }

    /**
     * Create log method for specific level
     */
    function createLogMethod(level) {
        return function(...args) {
            // Always passthrough to original console (for development)
            originalConsole[level](...args);

            // Check if should log at this level
            if (!shouldLog(level)) return;

            // Format and buffer
            const message = formatArgs(args);
            bufferLog(level, message);
        };
    }

    /**
     * Shared Logger Public API
     */
    window.SharedLogger = {
        /**
         * Debug level - detailed diagnostic info
         */
        debug: createLogMethod('debug'),

        /**
         * Log level - normal logs
         */
        log: createLogMethod('log'),

        /**
         * Info level - informational messages
         */
        info: createLogMethod('info'),

        /**
         * Warn level - warnings
         */
        warn: createLogMethod('warn'),

        /**
         * Error level - errors
         */
        error: createLogMethod('error'),

        /**
         * Set minimum log level
         * @param {string} level - 'debug', 'log', 'info', 'warn', 'error', 'silent'
         */
        setLevel: function(level) {
            if (LOG_LEVELS[level] === undefined) {
                originalConsole.warn('[SharedLogger] Invalid log level:', level);
                return;
            }
            currentLevel = LOG_LEVELS[level];
            originalConsole.log('[SharedLogger] Log level set to:', level);

            // Save to localStorage
            localStorage.setItem('LOG_LEVEL', level);
        },

        /**
         * Get current log level
         * @returns {string}
         */
        getLevel: function() {
            for (const [name, value] of Object.entries(LOG_LEVELS)) {
                if (value === currentLevel) return name;
            }
            return 'log';
        },

        /**
         * Enable logging
         */
        enable: function() {
            enabled = true;
            localStorage.setItem('LOGGING_ENABLED', 'true');
            originalConsole.log('[SharedLogger] Logging enabled');
        },

        /**
         * Disable logging (only original console will work)
         */
        disable: function() {
            enabled = false;
            localStorage.setItem('LOGGING_ENABLED', 'false');
            originalConsole.log('[SharedLogger] Logging disabled');
        },

        /**
         * Check if logging is enabled
         * @returns {boolean}
         */
        isEnabled: function() {
            return enabled;
        },

        /**
         * Get buffered logs
         * @returns {Array}
         */
        getBuffer: function() {
            return [...logBuffer];
        },

        /**
         * Clear log buffer
         */
        clearBuffer: function() {
            logBuffer = [];
            originalConsole.log('[SharedLogger] Buffer cleared');
        },

        /**
         * Manually send logs to backend
         */
        flush: function() {
            sendLogsToBackend();
        }
    };

    // Initialize from localStorage
    const savedLevel = localStorage.getItem('LOG_LEVEL');
    if (savedLevel && LOG_LEVELS[savedLevel] !== undefined) {
        currentLevel = LOG_LEVELS[savedLevel];
    }

    const savedEnabled = localStorage.getItem('LOGGING_ENABLED');
    if (savedEnabled === 'false') {
        enabled = false;
    }

    // Periodic flush (every 30 seconds)
    setInterval(() => {
        if (logBuffer.length > 0) {
            sendLogsToBackend();
        }
    }, 30000);

    originalConsole.log('[SharedLogger] Loaded - Level:', window.SharedLogger.getLevel());

})();
