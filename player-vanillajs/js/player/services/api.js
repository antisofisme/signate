/**
 * Player API Module
 * Handles playlist fetching and updates
 */

window.PlayerAPI = {
    /**
     * Load playlist from backend
     */
    loadPlaylist: async function() {
        const state = window.PlayerState;

        try {
            window.PlayerUI.hideError();
            window.PlayerUI.showLoading('Loading playlist...');

            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`
            );

            if (!data.playlist || data.playlist.length === 0) {
                console.log('[Player] Playlist is empty');
                window.PlayerUI.showWaiting('⏳ No content assigned yet...');

                // Retry after 10 seconds
                setTimeout(() => this.loadPlaylist(), 10000);
                return;
            }

            state.playlist = data.playlist;
            console.log('[Player] Playlist loaded:', state.playlist.length, 'items');

            // Sync cache with playlist (download new, delete old)
            try {
                await window.PlayerCache.syncCacheWithPlaylist(state.playlist);
            } catch (error) {
                console.error('❌ Cache sync error:', error);
            }

            // Start playback
            window.PlayerUI.hideLoading();
            window.PlayerPlayback.playContent(0);

        } catch (error) {
            // Handle 404 - No content assigned yet (normal, not an error)
            if (error.status === 404) {
                console.log('[Player] No content assigned yet (404)');
                window.PlayerUI.showWaiting('⏳ Waiting for content assignment...');

                // Retry after 10 seconds
                setTimeout(() => this.loadPlaylist(), 10000);
                return;
            }

            console.error('[Player] Failed to load playlist:', error);
            window.PlayerUI.showError(`⚠️ Connection Error\n\nRetrying in 10 seconds...`);

            // Retry after 10 seconds
            setTimeout(() => this.loadPlaylist(), 10000);
        }
    },

    /**
     * Check for playlist updates (periodic)
     */
    checkPlaylistUpdate: async function() {
        const state = window.PlayerState;

        try {
            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`
            );

            // Compare playlist (simple check - compare length and first item)
            if (data.playlist.length !== state.playlist.length ||
                (data.playlist[0] && state.playlist[0] && data.playlist[0].content_id !== state.playlist[0].content_id)) {

                console.log('[Player] Playlist updated! Reloading...');
                await this.loadPlaylist();
            }

        } catch (error) {
            // Silently ignore errors (don't spam console during periodic checks)
            console.debug('[Player] Playlist refresh check failed:', error.message);
        }
    }
};
