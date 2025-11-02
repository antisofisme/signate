/**
 * Player API Module
 * Handles playlist fetching and updates
 */

window.PlayerAPI = {
    /**
     * Load playlist from backend
     */
    loadPlaylist: async function() {
        // ✅ STATE MIGRATION: Prefer NEW reactive state, fallback to OLD for compatibility
        const state = window.PlayerState; // Keep for backward compatibility
        const apiBaseUrl = window.Config?.API_BASE_URL || window.ENV?.API_BASE_URL || state?.API_BASE_URL;
        const deviceId = state?.deviceId;

        // ✅ NULL CHECK: Ensure required config exists
        if (!apiBaseUrl || !deviceId) {
            console.error('[Player/API] Missing API_BASE_URL or deviceId:', {
                API_BASE_URL: apiBaseUrl,
                deviceId: deviceId
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
                `${apiBaseUrl}/api/client/playlist?device_id=${deviceId}`
            );

            if (!data.playlist || data.playlist.length === 0) {
                console.log('[Player] Playlist is empty');
                if (window.PlayerUI) {
                    window.PlayerUI.showWaiting('⏳ No content assigned yet...');
                }

                // Retry after configured interval
                setTimeout(() => this.loadPlaylist(), window.ENV?.RETRY_INTERVAL || 10000);
                return;
            }

            // ✅ STATE MIGRATION: Use NEW playerState for reactive playlist management
            if (window.playerState && window.playerState.setPlaylist) {
                window.playerState.setPlaylist(data.playlist);
                console.log('[Player/API] Playlist set reactively via playerState');
            } else {
                // Fallback to OLD pattern
                if (state) {
                    state.playlist = data.playlist;
                }
                console.log('[Player/API] Playlist loaded (fallback):', data.playlist.length, 'items');
            }

            // Sync cache with playlist (download new, delete old)
            // ✅ NULL CHECK: Ensure PlayerCache exists
            if (window.PlayerCache && window.PlayerCache.syncCacheWithPlaylist) {
                try {
                    // ✅ STATE MIGRATION: Get playlist from playerState
                    const playlist = window.playerState ? window.playerState.getPlaylist() : state?.playlist;
                    if (playlist) {
                        await window.PlayerCache.syncCacheWithPlaylist(playlist.contents || playlist);
                    }
                } catch (error) {
                    console.error('❌ Cache sync error:', error);

                    // ✅ ERROR RECOVERY: Notify user about cache failure
                    if (window.Toast) {
                        window.Toast.warning(
                            'Cache Warning',
                            'Failed to cache content. Offline mode may not work properly.',
                            window.ENV?.TOAST_DURATION || 5000
                        );
                    }

                    // ✅ ERROR RECOVERY: Emit event for monitoring/logging
                    if (window.eventBus) {
                        window.eventBus.emit('cache:sync-failed', {
                            error: error.message,
                            playlist_size: playlist?.length || 0,
                            timestamp: new Date().toISOString()
                        });
                    }

                    // ✅ ERROR RECOVERY: Schedule retry after delay (optional)
                    // Note: Don't retry immediately to avoid blocking playback
                    // Cache will retry on next playlist update
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

                // Retry after configured interval
                setTimeout(() => this.loadPlaylist(), window.ENV?.RETRY_INTERVAL || 10000);
                return;
            }

            console.error('[Player] Failed to load playlist:', error);

            // ✅ ERROR RECOVERY: Show user-friendly error message
            const retryDelay = window.ENV?.RETRY_INTERVAL || 10000;
            const retrySeconds = Math.round(retryDelay / 1000);

            if (window.PlayerUI) {
                window.PlayerUI.showError(`⚠️ Connection Error\n\n${error.message || 'Failed to load playlist'}\n\nRetrying in ${retrySeconds} seconds...`);
            }

            // ✅ ERROR RECOVERY: Emit event for monitoring
            if (window.eventBus) {
                window.eventBus.emit('playlist:load-failed', {
                    error: error.message,
                    status: error.status,
                    retry_in: retryDelay,
                    timestamp: new Date().toISOString()
                });
            }

            // Retry after configured interval
            setTimeout(() => this.loadPlaylist(), retryDelay);
        }
    },

    /**
     * Check for playlist updates (periodic)
     */
    checkPlaylistUpdate: async function() {
        // ✅ STATE MIGRATION: Prefer NEW reactive state, fallback to OLD
        const state = window.PlayerState; // Keep for backward compatibility
        const apiBaseUrl = window.Config?.API_BASE_URL || window.ENV?.API_BASE_URL || state?.API_BASE_URL;
        const deviceId = state?.deviceId;

        // ✅ NULL CHECK: Ensure required config exists
        if (!apiBaseUrl || !deviceId) {
            console.debug('[Player/API] Missing API_BASE_URL or deviceId');
            return;
        }

        // ✅ STATE MIGRATION: Get current playlist from playerState
        const currentPlaylistObj = window.playerState ? window.playerState.getPlaylist() : null;
        const currentPlaylist = currentPlaylistObj ? (currentPlaylistObj.contents || currentPlaylistObj) : state?.playlist;

        // ✅ NULL CHECK: Ensure current playlist exists to compare
        if (!currentPlaylist) {
            console.debug('[Player/API] No current playlist to compare');
            return;
        }

        try {
            // Use APIClient for standardized response handling
            const data = await window.APIClient.get(
                `${apiBaseUrl}/api/client/playlist?device_id=${deviceId}`
            );

            // ✅ NULL CHECK: Ensure response has playlist
            if (!data || !data.playlist) {
                console.debug('[Player/API] No playlist in response');
                return;
            }

            // Compare playlist (simple check - compare length and first item)
            const currentArray = Array.isArray(currentPlaylist) ? currentPlaylist : currentPlaylist.contents || [];
            if (data.playlist.length !== currentArray.length ||
                (data.playlist[0] && currentArray[0] && data.playlist[0].content_id !== currentArray[0].content_id)) {

                console.log('[Player] Playlist updated! Reloading...');
                await this.loadPlaylist();
            }

        } catch (error) {
            // Silently ignore errors (don't spam console during periodic checks)
            console.debug('[Player] Playlist refresh check failed:', error.message);
        }
    }
};
