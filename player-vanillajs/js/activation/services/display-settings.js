/**
 * Shell Display Settings Module
 * Handles display configuration: rotation, volume
 * Manual fullscreen available via F key or exit button
 */

window.ShellDisplaySettings = {
    settings: {
        rotation: 0,
        volume_enabled: true
    },

    /**
     * Fetch device settings from backend
     */
    fetchSettings: async function() {
        // ✅ STATE MIGRATION: Use NEW deviceState, fallback to OLD ShellState
        const device = window.deviceState ? window.deviceState.getDevice() : null;
        const deviceId = device ? device.id : window.ShellState?.deviceId;

        // ✅ NULL CHECK: Ensure deviceId exists
        if (!deviceId) {
            console.warn('[Shell/DisplaySettings] No device ID, using defaults');
            return this.settings;
        }

        // ✅ STATE MIGRATION: Get API_BASE_URL from Config/ENV (config, not state)
        const apiBaseUrl = window.Config?.API_BASE_URL || window.ENV?.API_BASE_URL;

        // ✅ NULL CHECK: Ensure API_BASE_URL exists
        if (!apiBaseUrl) {
            console.error('[Shell/DisplaySettings] No API_BASE_URL configured');
            return this.settings;
        }

        try {
            // ✅ USE APICLIENT: Standardized API calls with automatic error handling
            const device = await window.APIClient.get(`${apiBaseUrl}/api/devices/${deviceId}`);

            // Update settings from backend
            this.settings.rotation = device.rotation || 0;
            this.settings.volume_enabled = device.volume_enabled !== undefined ? device.volume_enabled : true;

            console.log('[Shell/DisplaySettings] Settings fetched:', this.settings);
            return this.settings;

        } catch (error) {
            // Handle 404 - Device deleted from backend
            if (error.status === 404) {
                console.warn('[Shell/DisplaySettings] ⚠️ Device not found (404) - Device was deleted');
                console.log('[Shell/DisplaySettings] 🔄 Resetting viewer...');

                // Clear localStorage (preserve Organization PIN)
                window.clearLocalStoragePreservePIN();

                // Delete IndexedDB cache
                const dbName = 'signage_media_cache';
                try {
                    await new Promise((resolve) => {
                        const deleteRequest = indexedDB.deleteDatabase(dbName);
                        deleteRequest.onsuccess = () => resolve();
                        deleteRequest.onerror = () => resolve();
                        deleteRequest.onblocked = () => resolve();
                    });
                } catch (err) {
                    console.error('[Shell/DisplaySettings] Error deleting cache:', err);
                }

                // Reload to show activation screen
                window.location.reload();
                return;
            }

            // Handle other errors
            console.error('[Shell/DisplaySettings] Failed to fetch settings:', error);
            // Return defaults on error
            return this.settings;
        }
    },

    /**
     * Apply rotation to player container
     */
    applyRotation: function() {
        const rotation = this.settings.rotation;
        const playerContainer = document.getElementById('player-container');

        if (!playerContainer) {
            console.warn('[Shell/DisplaySettings] Player container not found');
            return;
        }

        const screenWidth = window.innerWidth;
        const screenHeight = window.innerHeight;

        // Reset styles first
        playerContainer.style.transform = 'none';
        playerContainer.style.width = '100%';
        playerContainer.style.height = '100%';
        playerContainer.style.transformOrigin = 'center center';

        if (rotation === 0) {
            // Normal landscape - no rotation needed
            console.log('[Shell/DisplaySettings] Rotation: 0° (Landscape)');
        } else if (rotation === 90 || rotation === 270) {
            // Portrait mode - swap dimensions
            // Container needs to be sized for portrait, then rotated

            // Set container to portrait dimensions (swap width/height)
            playerContainer.style.width = screenHeight + 'px';
            playerContainer.style.height = screenWidth + 'px';

            // Position at center and rotate
            if (rotation === 90) {
                playerContainer.style.transform = `translate(${(screenWidth - screenHeight) / 2}px, ${(screenHeight - screenWidth) / 2}px) rotate(90deg)`;
            } else { // 270
                playerContainer.style.transform = `translate(${(screenWidth - screenHeight) / 2}px, ${(screenHeight - screenWidth) / 2}px) rotate(270deg)`;
            }

            console.log('[Shell/DisplaySettings] Rotation:', rotation + '° (Portrait) - Viewport swapped to', screenHeight + 'x' + screenWidth);
        } else if (rotation === 180) {
            // Upside down landscape
            playerContainer.style.transform = 'rotate(180deg)';
            console.log('[Shell/DisplaySettings] Rotation: 180° (Upside Down Landscape)');
        }
    },

    /**
     * Enter fullscreen mode (manual - triggered by F key)
     */
    enterFullscreen: async function() {
        try {
            const element = document.documentElement;

            // Try different fullscreen methods for browser compatibility
            if (element.requestFullscreen) {
                await element.requestFullscreen();
            } else if (element.webkitRequestFullscreen) {
                await element.webkitRequestFullscreen();
            } else if (element.mozRequestFullScreen) {
                await element.mozRequestFullScreen();
            } else if (element.msRequestFullscreen) {
                await element.msRequestFullscreen();
            }

            console.log('[Shell/DisplaySettings] ✅ Fullscreen entered');
            return true;
        } catch (error) {
            // Fullscreen may fail if not user-initiated, log but don't block
            console.warn('[Shell/DisplaySettings] Fullscreen request failed (may need user interaction):', error.message);
            return false;
        }
    },

    /**
     * Get settings to pass to Player via URL
     */
    getPlayerParams: function() {
        return {
            volume_enabled: this.settings.volume_enabled ? '1' : '0'
        };
    },

    /**
     * Check if settings changed and auto-apply
     * Called from heartbeat with response data
     */
    checkAndApplyChanges: async function(heartbeatData) {
        const newRotation = heartbeatData.rotation || 0;
        const newVolumeEnabled = heartbeatData.volume_enabled !== undefined ? heartbeatData.volume_enabled : true;

        let hasChanges = false;
        const changes = [];

        // Check rotation change
        if (newRotation !== this.settings.rotation) {
            changes.push(`rotation: ${this.settings.rotation}° → ${newRotation}°`);
            this.settings.rotation = newRotation;
            this.applyRotation();
            hasChanges = true;
        }

        // Check volume change
        if (newVolumeEnabled !== this.settings.volume_enabled) {
            changes.push(`volume: ${this.settings.volume_enabled ? 'On' : 'Off'} → ${newVolumeEnabled ? 'On' : 'Off'}`);
            this.settings.volume_enabled = newVolumeEnabled;
            hasChanges = true;

            // Reload player with new volume setting
            console.log('[Shell/DisplaySettings] Volume changed, reloading player...');
            if (window.ShellUI && window.ShellUI.loadPlayer) {
                window.ShellUI.loadPlayer();
            }
        }

        if (hasChanges) {
            console.log('[Shell/DisplaySettings] Settings auto-updated:', changes.join(', '));
        }
    },

    /**
     * Initialize display settings
     * Called when device is activated
     */
    init: async function() {
        console.log('[Shell/DisplaySettings] Initializing...');

        // Fetch settings from backend
        await this.fetchSettings();

        // Apply rotation
        this.applyRotation();

        console.log('[Shell/DisplaySettings] ✅ Initialization complete');
        console.log('[Shell/DisplaySettings] Use F key or hover exit button for manual fullscreen');
    },

    /**
     * Refresh settings from backend and reapply
     */
    refresh: async function() {
        console.log('[Shell/DisplaySettings] Refreshing settings...');
        await this.fetchSettings();
        this.applyRotation();
        // Don't re-enter fullscreen on refresh
    }
};
