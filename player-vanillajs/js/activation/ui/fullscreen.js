/**
 * Fullscreen Management
 * Handles fullscreen toggle, button interactions, and display rotation updates
 *
 * Usage:
 *   window.FullscreenManager.init()
 */

(function() {
    'use strict';

    /**
     * Fullscreen management system
     * @type {Object}
     */
    window.FullscreenManager = {
        /**
         * Update fullscreen state in DOM and apply display settings
         * Called when entering or exiting fullscreen
         *
         * @private
         */
        updateFullscreenState: function() {
            const playerContainer = document.getElementById('player-container');

            const isFullscreen = !!document.fullscreenElement;
            console.log('[Shell] Fullscreen state changed:', isFullscreen);

            if (isFullscreen) {
                console.log('[Shell] Entering fullscreen mode');
                playerContainer.classList.add('fullscreen');
                document.body.classList.add('is-fullscreen');

                // Wait for browser to finish fullscreen transition, then update
                setTimeout(() => {
                    // Recalculate rotation with new viewport dimensions
                    console.log('[Shell] Recalculating rotation for fullscreen viewport...');
                    if (window.ShellDisplaySettings && window.ShellDisplaySettings.applyRotation) {
                        window.ShellDisplaySettings.applyRotation();
                    }

                    // Reload player to update viewport size (ONLY if device is activated)
                    if (window.ShellState && window.ShellState.isActivated) {
                        console.log('[Shell] Reloading player for new viewport size...');
                        if (window.ShellUI && window.ShellUI.loadPlayer) {
                            window.ShellUI.loadPlayer();
                        }
                    } else {
                        console.log('[Shell] Device not activated yet, skip player reload');
                    }
                }, 100); // Small delay for browser to complete fullscreen
            } else {
                console.log('[Shell] Exiting fullscreen mode');
                playerContainer.classList.remove('fullscreen');
                document.body.classList.remove('is-fullscreen');

                // Wait for browser to finish fullscreen exit, then update
                setTimeout(() => {
                    // Recalculate rotation with normal viewport dimensions
                    console.log('[Shell] Recalculating rotation for normal viewport...');
                    if (window.ShellDisplaySettings && window.ShellDisplaySettings.applyRotation) {
                        window.ShellDisplaySettings.applyRotation();
                    }

                    // Reload player to restore normal viewport size (ONLY if device is activated)
                    if (window.ShellState && window.ShellState.isActivated) {
                        console.log('[Shell] Reloading player for normal viewport size...');
                        if (window.ShellUI && window.ShellUI.loadPlayer) {
                            window.ShellUI.loadPlayer();
                        }
                    } else {
                        console.log('[Shell] Device not activated yet, skip player reload');
                    }
                }, 100); // Small delay for browser to complete fullscreen exit
            }
        },

        /**
         * Setup mouse movement hover detection for buttons
         * Shows/hides fullscreen and action buttons based on cursor position
         *
         * @private
         */
        setupMouseHover: function() {
            document.addEventListener('mousemove', (e) => {
                const screenWidth = window.innerWidth;
                const screenHeight = window.innerHeight;
                const mouseX = e.clientX;
                const mouseY = e.clientY;

                const enterBtn = document.getElementById('enter-fullscreen-btn');
                const exitBtn = document.getElementById('exit-fullscreen-btn');
                const orgPinBtn = document.getElementById('org-pin-btn');
                const resetBtn = document.getElementById('hard-reset-btn');

                // Define hover area: right 150px, top 220px (increased for more buttons)
                const hoverAreaRight = 150;
                const hoverAreaTop = 220;

                const isInHoverArea = mouseX > (screenWidth - hoverAreaRight) && mouseY < hoverAreaTop;

                if (isInHoverArea) {
                    // Show buttons based on fullscreen state
                    if (document.fullscreenElement) {
                        // In fullscreen - show exit and reset buttons
                        if (exitBtn) exitBtn.classList.add('show');
                        if (enterBtn) enterBtn.classList.remove('show');
                    } else {
                        // Not in fullscreen - show enter and reset buttons
                        if (enterBtn) enterBtn.classList.add('show');
                        if (exitBtn) exitBtn.classList.remove('show');
                    }
                    // Always show org-pin and reset buttons in hover area
                    if (orgPinBtn) orgPinBtn.classList.add('show');
                    if (resetBtn) resetBtn.classList.add('show');
                } else {
                    // Hide all buttons when cursor outside hover area
                    if (enterBtn) enterBtn.classList.remove('show');
                    if (exitBtn) exitBtn.classList.remove('show');
                    if (orgPinBtn) orgPinBtn.classList.remove('show');
                    if (resetBtn) resetBtn.classList.remove('show');
                }
            });
        },

        /**
         * Setup fullscreen change event listeners for different browsers
         *
         * @private
         */
        setupFullscreenListeners: function() {
            document.addEventListener('fullscreenchange', () => this.updateFullscreenState());
            document.addEventListener('webkitfullscreenchange', () => this.updateFullscreenState());
            document.addEventListener('mozfullscreenchange', () => this.updateFullscreenState());
            document.addEventListener('MSFullscreenChange', () => this.updateFullscreenState());
        },

        /**
         * Setup enter fullscreen button click handler
         *
         * @private
         */
        setupEnterButton: function() {
            const enterBtn = document.getElementById('enter-fullscreen-btn');
            if (enterBtn) {
                enterBtn.addEventListener('click', () => {
                    console.log('[Shell] Enter button clicked');
                    if (!document.fullscreenElement) {
                        console.log('[Shell] Entering fullscreen via button...');
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
                            });
                        }
                    } else {
                        console.log('[Shell] Already in fullscreen');
                    }
                });
                console.log('[Shell] Enter button listener attached');
            } else {
                console.error('[Shell] Enter button not found!');
            }
        },

        /**
         * Setup exit fullscreen button click handler
         *
         * @private
         */
        setupExitButton: function() {
            const exitBtn = document.getElementById('exit-fullscreen-btn');
            if (exitBtn) {
                exitBtn.addEventListener('click', () => {
                    console.log('[Shell] Exit button clicked');
                    if (document.fullscreenElement) {
                        console.log('[Shell] Exiting fullscreen via button...');
                        document.exitFullscreen();
                    } else {
                        console.log('[Shell] Already not in fullscreen');
                    }
                });
                console.log('[Shell] Exit button listener attached');
            } else {
                console.error('[Shell] Exit button not found!');
            }
        },

        /**
         * Initialize fullscreen management
         * Call once on page load
         */
        init: function() {
            console.log('[Shell] Initializing Fullscreen Manager');

            // Setup all listeners and handlers
            this.setupMouseHover();
            this.setupFullscreenListeners();
            this.setupEnterButton();
            this.setupExitButton();

            // Set initial state
            this.updateFullscreenState();

            console.log('[Shell] Fullscreen Manager initialized');
        }
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.FullscreenManager;
    }
})();
