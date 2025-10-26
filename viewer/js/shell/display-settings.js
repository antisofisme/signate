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
        const state = window.ShellState;

        if (!state.deviceId) {
            console.warn('[Shell/DisplaySettings] No device ID, using defaults');
            return this.settings;
        }

        try {
            const response = await fetch(`${state.API_BASE_URL}/api/devices/${state.deviceId}`);

            if (response.status === 404) {
                // Device deleted from backend - reset viewer
                console.warn('[Shell/DisplaySettings] ⚠️ Device not found (404) - Device was deleted');
                console.log('[Shell/DisplaySettings] 🔄 Resetting viewer...');

                // Clear localStorage
                localStorage.clear();

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

            if (!response.ok) {
                throw new Error(`Failed to fetch settings: ${response.status}`);
            }

            const device = await response.json();

            // Update settings from backend
            this.settings.rotation = device.rotation || 0;
            this.settings.volume_enabled = device.volume_enabled !== undefined ? device.volume_enabled : true;

            console.log('[Shell/DisplaySettings] Settings fetched:', this.settings);
            return this.settings;

        } catch (error) {
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
