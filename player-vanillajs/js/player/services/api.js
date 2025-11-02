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

        // ✅ NULL CHECK: Ensure PlayerState exists
        if (!state) {
            console.error('[Player/API] PlayerState not initialized');
            return;
        }

        // ✅ NULL CHECK: Ensure required state properties exist
        if (!state.API_BASE_URL || !state.deviceId) {
            console.error('[Player/API] Missing API_BASE_URL or deviceId:', {
                API_BASE_URL: state.API_BASE_URL,
                deviceId: state.deviceId
            });
            return;
        }

        try {
            // ✅ NULL CHECK: Ensure PlayerUI exists
            if (window.PlayerUI) {
                window.PlayerUI.hideError();
                window.PlayerUI.showLoading('Loading playlist...');
            }

            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`
            );

            if (!data.playlist || data.playlist.length === 0) {
                console.log('[Player] Playlist is empty');
                if (window.PlayerUI) {
                    window.PlayerUI.showWaiting('⏳ No content assigned yet...');
                }

                // Retry after 10 seconds
                setTimeout(() => this.loadPlaylist(), 10000);
                return;
            }

            state.playlist = data.playlist;
            console.log('[Player] Playlist loaded:', state.playlist.length, 'items');

            // Sync cache with playlist (download new, delete old)
            // ✅ NULL CHECK: Ensure PlayerCache exists
            if (window.PlayerCache && window.PlayerCache.syncCacheWithPlaylist) {
                try {
                    await window.PlayerCache.syncCacheWithPlaylist(state.playlist);
                } catch (error) {
                    console.error('❌ Cache sync error:', error);
                }
            }

            // Start playback
            // ✅ NULL CHECK: Ensure PlayerUI and PlayerPlayback exist
            if (window.PlayerUI) {
                window.PlayerUI.hideLoading();
            }

            if (window.PlayerPlayback && window.PlayerPlayback.playContent) {
                window.PlayerPlayback.playContent(0);
            } else {
                console.error('[Player/API] PlayerPlayback not available');
            }

        } catch (error) {
            // Handle 404 - No content assigned yet (normal, not an error)
            if (error.status === 404) {
                console.log('[Player] No content assigned yet (404)');
                if (window.PlayerUI) {
                    window.PlayerUI.showWaiting('⏳ Waiting for content assignment...');
                }

                // Retry after 10 seconds
                setTimeout(() => this.loadPlaylist(), 10000);
                return;
            }

            console.error('[Player] Failed to load playlist:', error);
            if (window.PlayerUI) {
                window.PlayerUI.showError(`⚠️ Connection Error\n\nRetrying in 10 seconds...`);
            }

            // Retry after 10 seconds
            setTimeout(() => this.loadPlaylist(), 10000);
        }
    },

    /**
     * Check for playlist updates (periodic)
     */
    checkPlaylistUpdate: async function() {
        const state = window.PlayerState;

        // ✅ NULL CHECK: Ensure PlayerState exists
        if (!state) {
            console.debug('[Player/API] PlayerState not initialized');
            return;
        }

        // ✅ NULL CHECK: Ensure required state properties exist
        if (!state.API_BASE_URL || !state.deviceId) {
            console.debug('[Player/API] Missing API_BASE_URL or deviceId');
            return;
        }

        // ✅ NULL CHECK: Ensure current playlist exists to compare
        if (!state.playlist) {
            console.debug('[Player/API] No current playlist to compare');
            return;
        }

        try {
            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`
            );

            // ✅ NULL CHECK: Ensure response has playlist
            if (!data || !data.playlist) {
                console.debug('[Player/API] No playlist in response');
                return;
            }

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
