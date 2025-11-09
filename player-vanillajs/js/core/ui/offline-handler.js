/**
 * Offline Handler Module
 *
 * @module OfflineHandler
 * @description
 * Handles offline page functionality including connection retry and status updates.
 * Auto-retries connection every 10 seconds and redirects when connection restored.
 *
 * @features
 * - Auto-retry connection every 10 seconds
 * - Manual retry button
 * - Status message updates
 * - Online/offline event listeners
 * - Auto-redirect when connection restored
 *
 * @usage
 * ```javascript
 * // Auto-initializes when page loads
 * // No manual initialization needed
 * ```
 */

(function() {
    'use strict';

    /**
     * Offline Handler
     */
    const OfflineHandler = {
        /**
         * Retry counter
         * @type {number}
         */
        retryCount: 0,

        /**
         * DOM elements
         */
        elements: {
            statusText: null,
            lastAttempt: null
        },

        /**
         * Initialize offline handler
         */
        init: function() {
            // Get DOM elements
            this.elements.statusText = document.getElementById('status-text');
            this.elements.lastAttempt = document.getElementById('last-attempt');

            // Check connection on load (after 2 seconds)
            setTimeout(() => this.checkConnection(), 2000);

            // Auto-retry every 10 seconds
            setInterval(() => this.checkConnection(), 10000);

            // Listen for online/offline events
            window.addEventListener('online', () => this.handleOnline());
            window.addEventListener('offline', () => this.handleOffline());

            SharedLogger.log('[OfflineHandler] Initialized');
        },

        /**
         * Check connection to server
         */
        checkConnection: function() {
            this.retryCount++;
            this.updateStatus('Checking connection...');

            fetch('/', { method: 'HEAD', cache: 'no-store' })
                .then(response => {
                    if (response.ok) {
                        this.updateStatus('Connection restored! Redirecting...');
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 1000);
                    } else {
                        this.updateStatus('Server unreachable. Retrying...');
                    }
                })
                .catch(() => {
                    this.updateStatus(`Offline - Attempt ${this.retryCount}`);
                    this.updateLastAttempt();
                });
        },

        /**
         * Update status message
         * @param {string} message - Status message
         */
        updateStatus: function(message) {
            if (this.elements.statusText) {
                this.elements.statusText.innerHTML = `<span class="spinner"></span>${message}`;
            }
        },

        /**
         * Update last attempt timestamp
         */
        updateLastAttempt: function() {
            if (this.elements.lastAttempt) {
                const now = new Date();
                this.elements.lastAttempt.textContent = now.toLocaleTimeString();
            }
        },

        /**
         * Handle online event
         */
        handleOnline: function() {
            this.updateStatus('Connection restored! Redirecting...');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        },

        /**
         * Handle offline event
         */
        handleOffline: function() {
            this.updateStatus('Network connection lost');
        }
    };

    /**
     * Manual retry function (called by button onclick)
     * @global
     */
    window.retryConnection = function() {
        OfflineHandler.checkConnection();
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => OfflineHandler.init());
    } else {
        OfflineHandler.init();
    }

    // Export for module usage
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = OfflineHandler;
    }

    // Export to window
    window.OfflineHandler = OfflineHandler;

    SharedLogger.log('[OfflineHandler] Module loaded');

})();
