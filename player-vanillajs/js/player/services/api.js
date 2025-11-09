/**
 * Player API Module
 * Handles playlist fetching and updates
 */

window.PlayerAPI = {
    /**
     * Load playlist from backend
     */
    loadPlaylist: async function() {
        // ✅ STATE MIGRATION: Initialize PlayerState if it doesn't exist
        if (!window.PlayerState) {
            window.PlayerState = {};
        }

        const state = window.PlayerState;
        const apiBaseUrl = window.Config?.API_BASE_URL || window.SharedENV?.API_BASE_URL || state?.API_BASE_URL;
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

            // 🆕 Use resolved content endpoint (3-tier priority system)
            const response = await window.SharedAPIClient.get(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.CONTENT_RESOLVED(deviceId))
            );

            // Unwrap response: backend returns { success: true, data: { ... } }
            const data = response.data || response;

            // Transform backend response to playlist format
            const playlist = {
                id: data.device_id,
                name: `Device ${deviceId} Content`,
                contents: (data.items || []).map(item => ({
                    content_id: item.id,
                    title: item.title,
                    type: item.content_type,
                    url: item.hls_master_playlist_url || item.file_url,
                    duration: item.duration,
                    file_size: item.file_size,
                    thumbnail_url: item.thumbnail_url,
                    width: item.width,
                    height: item.height,
                    metadata: item.metadata || {}
                }))
            };

            if (!playlist.contents || playlist.contents.length === 0) {
                SharedLogger.log('[Player] No content assigned yet');
                if (window.PlayerUI) {
                    window.PlayerUI.showWaiting('⏳ No content assigned yet...');
                }

                // Retry after configured interval
                setTimeout(() => this.loadPlaylist(), window.SharedENV?.RETRY_INTERVAL || 10000);
                return;
            }

            // ✅ STATE MIGRATION: Use NEW playerState for reactive playlist management
            if (window.PlayerState && window.PlayerState.setPlaylist) {
                window.PlayerState.setPlaylist(playlist);
                SharedLogger.log('[Player/API] ✅ Resolved content loaded via playerState:', playlist.contents.length, 'items');
            } else {
                // Fallback to OLD pattern
                if (state) {
                    state.playlist = playlist;
                }
                SharedLogger.log('[Player/API] ✅ Resolved content loaded (fallback):', playlist.contents.length, 'items');
            }

            // Sync cache with playlist (download new, delete old)
            // ✅ NULL CHECK: Ensure PlayerCache exists
            if (window.PlayerCache && window.PlayerCache.syncCacheWithPlaylist) {
                try {
                    // ✅ STATE MIGRATION: Get playlist from playerState
                    const playlist = window.PlayerState ? window.PlayerState.getPlaylist() : state?.playlist;
                    if (playlist) {
                        await window.PlayerCache.syncCacheWithPlaylist(playlist.contents || playlist);
                    }
                } catch (error) {
                    SharedLogger.error('❌ Cache sync error:', error);

                    // ✅ ERROR RECOVERY: Notify user about cache failure
                    if (window.SharedToast) {
                        window.SharedToast.warning(
                            'Cache Warning',
                            'Failed to cache content. Offline mode may not work properly.',
                            window.SharedENV?.TOAST_DURATION || 5000
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
                SharedLogger.error('[Player/API] PlayerPlayback not available');
            }

        } catch (error) {
            // Handle 404 - No content assigned yet (normal, not an error)
            if (error.status === 404) {
                SharedLogger.log('[Player] No content assigned yet (404)');
                if (window.PlayerUI) {
                    window.PlayerUI.showWaiting('⏳ Waiting for content assignment...');
                }

                // Retry after configured interval
                setTimeout(() => this.loadPlaylist(), window.SharedENV?.RETRY_INTERVAL || 10000);
                return;
            }

            SharedLogger.error('[Player] Failed to load playlist:', error);

            // ✅ ERROR RECOVERY: Show user-friendly error message
            const retryDelay = window.SharedENV?.RETRY_INTERVAL || 10000;
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
        const apiBaseUrl = window.Config?.API_BASE_URL || window.SharedENV?.API_BASE_URL || state?.API_BASE_URL;
        const deviceId = state?.deviceId;

        // ✅ NULL CHECK: Ensure required config exists
        if (!apiBaseUrl || !deviceId) {
            console.debug('[Player/API] Missing API_BASE_URL or deviceId');
            return;
        }

        // ✅ STATE MIGRATION: Get current playlist from playerState
        const currentPlaylistObj = window.PlayerState ? window.PlayerState.getPlaylist() : null;
        const currentPlaylist = currentPlaylistObj ? (currentPlaylistObj.contents || currentPlaylistObj) : state?.playlist;

        // ✅ NULL CHECK: Ensure current playlist exists to compare
        if (!currentPlaylist) {
            console.debug('[Player/API] No current playlist to compare');
            return;
        }

        try {
            // 🆕 Use resolved content endpoint
            const response = await window.SharedAPIClient.get(
                window.getFullURL(window.API_ENDPOINTS.DEVICES.CONTENT_RESOLVED(deviceId))
            );

            // Unwrap response: backend returns { success: true, data: { ... } }
            const data = response.data || response;

            // ✅ NULL CHECK: Ensure response has items
            if (!data || !data.items) {
                console.debug('[Player/API] No content items in response');
                return;
            }

            // Compare content (simple check - compare length and first item)
            const currentArray = Array.isArray(currentPlaylist) ? currentPlaylist : currentPlaylist.contents || [];
            if (data.items.length !== currentArray.length ||
                (data.items[0] && currentArray[0] && data.items[0].id !== currentArray[0].content_id)) {

                SharedLogger.log('[Player] Content updated! Reloading...');
                await this.loadPlaylist();
            }

        } catch (error) {
            // Silently ignore errors (don't spam console during periodic checks)
            console.debug('[Player] Content refresh check failed:', error.message);
        }
    }
};
