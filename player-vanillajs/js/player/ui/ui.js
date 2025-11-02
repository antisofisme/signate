/**
 * Player UI Module
 * Handles UI updates, loading states, and keyboard shortcuts
 */

window.PlayerUI = {
    /**
     * Show loading screen
     */
    showLoading: function(message = 'Loading...') {
        this.hideError();
        const loading = document.getElementById('loading');
        if (loading) {
            // ✅ NULL CHECK: Ensure paragraph element exists
            const paragraph = loading.querySelector('p');
            if (paragraph) {
                paragraph.textContent = message;
            }
            loading.style.display = 'block';
        }
    },

    /**
     * Hide loading screen
     */
    hideLoading: function() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    },

    /**
     * Show waiting state (yellow spinner)
     */
    showWaiting: function(message) {
        console.log('[Player] Waiting:', message);

        this.hideError();
        const loading = document.getElementById('loading');
        if (loading) {
            // Change spinner color to yellow/orange for waiting state
            const spinner = loading.querySelector('.spinner');
            if (spinner) {
                spinner.style.borderTopColor = '#ffa500';
            }

            // ✅ NULL CHECK: Ensure paragraph element exists
            const paragraph = loading.querySelector('p');
            if (paragraph) {
                paragraph.textContent = message;
                paragraph.style.color = '#ffa500';
            }

            loading.style.display = 'block';
        }
    },

    /**
     * Show error message
     */
    showError: function(message) {
        console.error('[Player] Error:', message);

        this.hideLoading();
        const error = document.getElementById('error');
        const errorMessage = document.getElementById('error-message');

        if (error && errorMessage) {
            errorMessage.textContent = message;
            error.style.display = 'block';
        }
    },

    /**
     * Hide error message
     */
    hideError: function() {
        const error = document.getElementById('error');
        if (error) {
            error.style.display = 'none';
        }
    },

    /**
     * Update debug info overlay
     */
    updateDebugInfo: function(content, index, isCached) {
        // ✅ NULL CHECK: Ensure content exists
        if (!content) {
            console.debug('[Player/UI] Cannot update debug info - missing content');
            return;
        }

        // ✅ STATE MIGRATION: Get playlist from playerState
        const playlistObj = window.playerState ? window.playerState.getPlaylist() : null;
        const playlist = playlistObj ? (playlistObj.contents || playlistObj) : window.PlayerState?.playlist;

        // ✅ NULL CHECK: Update debug elements only if they exist
        const debugContent = document.getElementById('debug-content');
        const debugIndex = document.getElementById('debug-index');
        const debugTotal = document.getElementById('debug-total');
        const debugType = document.getElementById('debug-type');
        const debugCache = document.getElementById('debug-cache');

        if (debugContent) debugContent.textContent = content.title || content.name || 'Unknown';
        if (debugIndex) debugIndex.textContent = index + 1;
        if (debugTotal && playlist) {
            const totalCount = Array.isArray(playlist) ? playlist.length : (playlistObj?.getContentCount?.() || 0);
            debugTotal.textContent = totalCount;
        }
        if (debugType) debugType.textContent = content.content_type || 'unknown';
        if (debugCache) debugCache.textContent = isCached ? 'Cached ✅' : 'Downloading...';
    },

    /**
     * Initialize keyboard shortcuts
     */
    initKeyboardShortcuts: function() {
        document.addEventListener('keydown', (e) => {
            // Press 'p' to toggle player info
            if (e.key === 'p' || e.key === 'P') {
                const info = document.getElementById('player-info');
                if (info) {
                    info.style.display = info.style.display === 'none' ? 'block' : 'none';
                }
            }

            // Press 'n' to skip to next content
            if (e.key === 'n' || e.key === 'N') {
                // ✅ NULL CHECK: Ensure PlayerPlayback exists
                if (window.PlayerPlayback && window.PlayerPlayback.playContent) {
                    console.log('[Player] Manual skip to next');

                    // ✅ STATE MIGRATION: Get current index from playerState
                    const currentIndex = window.playerState ? window.playerState.getCurrentIndex() :
                                        (window.PlayerState?.currentIndex || 0);
                    window.PlayerPlayback.playContent(currentIndex + 1);
                }
            }

            // Press 'r' to reload playlist
            if (e.key === 'r' || e.key === 'R') {
                // ✅ NULL CHECK: Ensure PlayerAPI exists
                if (window.PlayerAPI && window.PlayerAPI.loadPlaylist) {
                    console.log('[Player] Manual reload playlist');
                    window.PlayerAPI.loadPlaylist();
                }
            }
        });
    }
};
