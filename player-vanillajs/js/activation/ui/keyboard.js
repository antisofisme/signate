/**
 * Keyboard Shortcuts System
 * Handles keyboard events for common shell operations
 *
 * Shortcuts:
 *   's' - Toggle shell debug info
 *   'r' - Reload player
 *   'f' - Toggle fullscreen
 *   'Esc' - Exit fullscreen
 *
 * Usage:
 *   window.KeyboardShortcuts.init()
 */

(function() {
    'use strict';

    /**
     * Keyboard shortcuts system
     * @type {Object}
     */
    window.KeyboardShortcuts = {
        /**
         * Handle 's' key - Toggle shell debug info
         *
         * @private
         */
        handleDebugToggle: function() {
            const info = document.getElementById('shell-info');
            info.style.display = info.style.display === 'none' ? 'block' : 'none';

            // Update debug info
            document.getElementById('debug-device-id').textContent = localStorage.getItem('device_id') || '-';
            document.getElementById('debug-status').textContent = localStorage.getItem('device_status') || '-';
        },

        /**
         * Handle 'r' key - Reload player only
         *
         * @private
         */
        handlePlayerReload: function() {
            if (window.reloadPlayer) {
                window.reloadPlayer();
            }
        },

        /**
         * Handle 'f' key - Toggle fullscreen
         *
         * @private
         */
        handleFullscreenToggle: function() {
            console.log('[Shell] F key pressed, current fullscreen state:', !!document.fullscreenElement);

            if (!document.fullscreenElement) {
                // Enter fullscreen
                console.log('[Shell] Attempting to enter fullscreen...');

                const elem = document.documentElement;
                const requestFullscreen = elem.requestFullscreen ||
                                         elem.webkitRequestFullscreen ||
                                         elem.mozRequestFullScreen ||
                                         elem.msRequestFullscreen;

                if (requestFullscreen) {
                    requestFullscreen.call(elem).then(() => {
                        console.log('[Shell] Fullscreen entered successfully');
                    }).catch(err => {
                        console.error('[Shell] Fullscreen error:', err);
                        if (window.Toast) {
                            window.Toast.error('Fullscreen Failed', err.message);
                        }
                    });
                } else {
                    console.error('[Shell] Fullscreen API not supported');
                    if (window.Toast) {
                        window.Toast.error('Fullscreen Not Supported', 'Your browser does not support fullscreen mode');
                    }
                }
            } else {
                // Exit fullscreen
                console.log('[Shell] Exiting fullscreen...');
                document.exitFullscreen();
            }
        },

        /**
         * Handle 'Esc' key - Exit fullscreen
         *
         * @private
         */
        handleEscapeKey: function() {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            }
        },

        /**
         * Initialize keyboard shortcuts
         * Call once on page load
         */
        init: function() {
            console.log('[Shell] Initializing Keyboard Shortcuts');

            document.addEventListener('keydown', (e) => {
                // Press 's' to toggle shell debug info
                if (e.key === 's' || e.key === 'S') {
                    this.handleDebugToggle();
                }

                // Press 'r' to reload player only (not shell)
                if (e.key === 'r' || e.key === 'R') {
                    this.handlePlayerReload();
                }

                // Press 'f' to toggle fullscreen
                if (e.key === 'f' || e.key === 'F') {
                    this.handleFullscreenToggle();
                }

                // Press 'Esc' to exit fullscreen
                if (e.key === 'Escape' && document.fullscreenElement) {
                    this.handleEscapeKey();
                }
            });

            console.log('[Shell] Keyboard Shortcuts initialized');
        }
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.KeyboardShortcuts;
    }
})();
