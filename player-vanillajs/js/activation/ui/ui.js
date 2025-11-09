/**
 * Shell UI Module
 * Handles UI updates for shell (activation screen, player loading)
 */

window.ShellUI = {
    /**
     * Update UI based on status
     */
    updateUI: function(status, code = null) {
        SharedLogger.log('[Shell/UI] updateUI called - status:', status, 'code:', code);

        const statusElement = document.getElementById('status-message');
        const codeElement = document.getElementById('activation-code');
        const instructionElement = document.getElementById('activation-instruction');
        const activationScreen = document.getElementById('activation-screen');
        const playerContainer = document.getElementById('player-container');

        // ✅ NULL CHECK: Defensive programming to prevent crashes
        if (!statusElement) {
            SharedLogger.error('[Shell/UI] Status element not found');
            return;
        }

        if (status === 'pending') {
            statusElement.textContent = '⏳ Waiting for approval...';

            // ✅ NULL CHECK: Only update if element exists
            if (codeElement) {
                codeElement.textContent = code;
            }

            // Update instruction based on organization_id
            if (instructionElement) {
                const organizationId = localStorage.getItem('organization_id');
                SharedLogger.log('[Shell/UI] Updating instruction text - organization_id:', organizationId, 'type:', typeof organizationId);

                // Check if organization_id exists AND is not string "null"
                if (organizationId && organizationId !== 'null' && organizationId !== 'undefined') {
                    // Re-registration (device sudah punya organization)
                    const newText = 'Admin will approve this device in the Web Admin panel';
                    instructionElement.textContent = newText;
                    SharedLogger.log('[Shell/UI] Set instruction (re-registration):', newText);
                } else {
                    // First-time registration (device belum punya organization)
                    const newText = 'Daftarkan kode ini di CMS untuk menambahkan device ke organisasi Anda';
                    instructionElement.textContent = newText;
                    SharedLogger.log('[Shell/UI] Set instruction (first-time):', newText);
                }
            } else {
                SharedLogger.error('[Shell/UI] activation-instruction element not found!');
            }

            // Ensure activation screen is visible and player is hidden
            if (activationScreen) {
                activationScreen.style.display = 'flex';
            }
            if (playerContainer) {
                playerContainer.style.display = 'none';
            }
        } else if (status === 'active') {
            statusElement.textContent = '✅ Activated! Loading player...';

            // Keep activation screen visible until player loads
            if (activationScreen) {
                activationScreen.style.display = 'flex';
            }
            if (playerContainer) {
                playerContainer.style.display = 'none';
            }
        }
    },

    /**
     * Show activation success message
     */
    showActivationSuccess: function(deviceName) {
        SharedLogger.log(`[Shell/UI] 🎉 Activation successful! Device: ${deviceName}`);
        const statusElement = document.getElementById('status-message');
        if (statusElement) {
            statusElement.textContent = `✅ Activated as: ${deviceName}`;
        }
    },

    /**
     * Load player in iframe with cache-busting timestamp
     */
    loadPlayer: function() {
        // ✅ STATE MIGRATION: Use NEW deviceState instead of OLD ShellState
        const device = window.SharedDeviceState ? window.SharedDeviceState.getDevice() : null;
        const deviceId = device ? device.id : window.ShellState?.deviceId; // Fallback for backward compatibility

        const timestamp = Date.now();
        const iframe = document.getElementById('player-iframe');

        if (iframe) {
            // Get display settings to pass to Player
            const playerParams = window.ShellDisplaySettings.getPlayerParams();
            const volumeParam = playerParams.volume_enabled;

            iframe.src = `player.html?t=${timestamp}&deviceId=${deviceId}&volume=${volumeParam}`;
            SharedLogger.log('[Shell] Loading player iframe with deviceId:', deviceId, 'volume:', volumeParam);

            // Listen for player errors
            iframe.onerror = () => {
                SharedLogger.error('[Shell] Player iframe failed to load');

                // ✅ NULL CHECK: Ensure error element exists before updating
                const errorElement = document.getElementById('error-message');
                if (errorElement) {
                    errorElement.textContent = 'Player failed to load. Retrying...';
                }

                // Show toast notification
                if (window.SharedToast) {
                    window.SharedToast.error('Player Error', 'Player failed to load. Retrying in 5 seconds...', 4000);
                }

                // Retry after configured interval
                setTimeout(() => this.loadPlayer(), window.SharedENV?.PLAYER_RETRY_INTERVAL || 5000);
            };

            // Hide activation screen, show player
            document.getElementById('activation-screen').style.display = 'none';
            document.getElementById('player-container').style.display = 'block';
        }
    },

    /**
     * Reload player (force refresh without clearing shell)
     */
    reloadPlayer: function() {
        SharedLogger.log('[Shell] Reloading player...');
        this.loadPlayer();
    }
};

// Expose to global for debugging
window.reloadPlayer = function() {
    window.ShellUI.reloadPlayer();
};
