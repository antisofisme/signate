/**
 * Player Initialization Module
 * Main entry point for player - orchestrates initialization
 */

window.PlayerInit = {
    /**
     * Initialize player
     */
    init: async function() {
        const state = window.PlayerState;

        state.originalConsole.log('[Player] Initializing...');

        // Get deviceId from URL params (passed by shell)
        const params = new URLSearchParams(window.location.search);
        state.deviceId = params.get('deviceId');

        if (!state.deviceId) {
            window.PlayerUI.showError('No device ID provided');
            return;
        }

        // Initialize logger (after we have deviceId)
        window.PlayerLogger.init();

        console.log('[Player] Device ID:', state.deviceId);

        // Initialize IndexedDB cache
        try {
            await window.PlayerCache.initMediaCache();
            console.log('📦 Media cache initialized');
        } catch (error) {
            console.error('❌ Failed to initialize cache:', error);
        }

        // Initialize keyboard shortcuts
        window.PlayerUI.initKeyboardShortcuts();

        // Load and start playlist
        await window.PlayerAPI.loadPlaylist();

        // Start periodic refresh check
        state.refreshTimer = setInterval(() => window.PlayerAPI.checkPlaylistUpdate(), state.REFRESH_INTERVAL);

        console.log('[Player] Ready ✅');
    }
};

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.PlayerInit.init());
} else {
    window.PlayerInit.init();
}

// Export for debugging
window.playerState = {
    deviceId: () => window.PlayerState.deviceId,
    playlist: () => window.PlayerState.playlist,
    currentIndex: () => window.PlayerState.currentIndex,
    reload: () => window.PlayerAPI.loadPlaylist()
};
