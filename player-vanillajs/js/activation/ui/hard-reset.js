/**
 * Hard Reset Handler
 * Manages device hard reset with password protection and full data clearing
 *
 * Clears:
 *   - localStorage (all device data)
 *   - IndexedDB cache (media cache)
 *   - Page reload to complete reset
 *
 * Usage:
 *   window.HardResetHandler.init()
 */

(function() {
    'use strict';

    /**
     * Hard reset handler system
     * @type {Object}
     */
    window.HardResetHandler = {
        /**
         * Flag to prevent double-click during reset process
         * @private
         * @type {boolean}
         */
        isResetting: false,

        /**
         * Clear localStorage and IndexedDB, then reload page
         * Called after password validation
         *
         * @private
         */
        executeReset: function() {
            // Set flag to prevent double execution
            this.isResetting = true;
            console.log('[Shell] Password verified, executing hard reset...');

            // Log BEFORE clear
            console.log('[Shell] BEFORE clear - localStorage:', {
                deviceId: localStorage.getItem('device_id'),
                status: localStorage.getItem('device_status'),
                code: localStorage.getItem('device_code'),
                organizationId: localStorage.getItem('organization_id')
            });

            // Clear localStorage (includes device data)
            localStorage.clear();

            // Verify cleared
            console.log('[Shell] AFTER clear - localStorage:', {
                deviceId: localStorage.getItem('device_id'),
                status: localStorage.getItem('device_status'),
                code: localStorage.getItem('device_code'),
                organizationId: localStorage.getItem('organization_id')
            });
            console.log('[Shell] localStorage cleared (all device data removed)');

            // Clear IndexedDB cache (if PlayerCache available)
            let reloadExecuted = false; // Prevent multiple reloads

            /**
             * Execute page reload
             * @private
             */
            const executeReload = () => {
                if (!reloadExecuted) {
                    reloadExecuted = true;
                    console.log('[Shell] Reloading page to complete hard reset...');
                    setTimeout(() => location.reload(), 100); // Small delay for logs
                }
            };

            try {
                // Try to open PlayerCache DB and clear it
                const dbName = 'signage_media_cache';
                const deleteRequest = indexedDB.deleteDatabase(dbName);

                deleteRequest.onsuccess = () => {
                    console.log('[Shell] IndexedDB cache deleted');
                    executeReload();
                };

                deleteRequest.onerror = () => {
                    console.error('[Shell] IndexedDB delete failed, reloading anyway');
                    executeReload();
                };

                deleteRequest.onblocked = () => {
                    console.warn('[Shell] IndexedDB delete blocked, reloading anyway');
                    executeReload();
                };

                // Fallback: If nothing happens in 2 seconds, reload anyway
                setTimeout(() => {
                    if (!reloadExecuted) {
                        console.warn('[Shell] IndexedDB delete timeout, reloading...');
                        executeReload();
                    }
                }, 2000);
            } catch (error) {
                console.error('[Shell] Error deleting IndexedDB:', error);
                executeReload();
            }
        },

        /**
         * Validate password via backend API and execute reset if valid
         * @private
         * @param {string} password - Password to validate
         */
        validatePasswordAndReset: async function(password) {
            try {
                // Call backend API to validate password
                const response = await window.APIClient.post(
                    window.getFullURL(window.API_ENDPOINTS.DEVICES.VALIDATE_RESET_PASSWORD),
                    { password: password }
                );

                if (response.valid) {
                    console.log('[Shell] Password validated by backend');
                    this.executeReset();
                } else {
                    window.Toast.error('Incorrect Password', 'Reset cancelled. Please try again.');
                    console.error('[Shell] Hard reset failed - wrong password');
                }
            } catch (error) {
                console.error('[Shell] Error validating password:', error);
                window.Toast.error('Validation Error', 'Could not validate password. Please try again.');
            }
        },

        /**
         * Setup hard reset button click handler
         * Prompts for password before executing reset
         *
         * @private
         */
        setupResetButton: function() {
            const resetBtn = document.getElementById('hard-reset-btn');

            if (resetBtn) {
                resetBtn.addEventListener('click', async () => {
                    // Prevent double-click during reset
                    if (this.isResetting) {
                        console.warn('[Shell] Hard reset already in progress, ignoring click');
                        return;
                    }

                    console.log('[Shell] Hard reset button clicked');

                    // Prompt for password using modal
                    let password;
                    try {
                        password = await window.PasswordModal.show(
                            'Hard Reset Device',
                            'This will ERASE ALL DATA and require re-activation. Enter admin password to confirm:'
                        );
                    } catch (err) {
                        console.log('[Shell] Hard reset cancelled (modal closed)');
                        return;
                    }

                    if (!password) {
                        console.log('[Shell] Hard reset cancelled (no password)');
                        return;
                    }

                    // Validate password via backend API
                    this.validatePasswordAndReset(password);
                });

                console.log('[Shell] Hard reset button listener attached');
            } else {
                console.error('[Shell] Hard reset button not found!');
            }
        },

        /**
         * Initialize hard reset handler
         * Call once on page load
         */
        init: function() {
            console.log('[Shell] Initializing Hard Reset Handler');

            this.setupResetButton();

            console.log('[Shell] Hard Reset Handler initialized');
        }
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.HardResetHandler;
    }
})();
