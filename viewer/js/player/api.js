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

            const response = await fetch(`${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`);

            if (!response.ok) {
                // 404 = No content assigned yet (normal, not an error)
                if (response.status === 404) {
                    console.log('[Player] No content assigned yet');
                    window.PlayerUI.showWaiting('⏳ Waiting for content assignment...');

                    // Retry after 10 seconds
                    setTimeout(() => this.loadPlaylist(), 10000);
                    return;
                }

                throw new Error(`Failed to load playlist: ${response.status}`);
            }

            const data = await response.json();

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
            const response = await fetch(`${state.API_BASE_URL}/api/client/playlist?device_id=${state.deviceId}`);

            if (!response.ok) return;

            const data = await response.json();

            // Compare playlist (simple check - compare length and first item)
            if (data.playlist.length !== state.playlist.length ||
                (data.playlist[0] && state.playlist[0] && data.playlist[0].content_id !== state.playlist[0].content_id)) {

                console.log('[Player] Playlist updated! Reloading...');
                await this.loadPlaylist();
            }

        } catch (error) {
            console.error('[Player] Playlist refresh check failed:', error);
        }
    }
};
