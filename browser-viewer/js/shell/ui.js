/**
 * Shell UI Module
 * Handles UI updates for shell (activation screen, player loading)
 */

window.ShellUI = {
    /**
     * Update UI based on status
     */
    updateUI: function(status, code = null) {
        const statusElement = document.getElementById('status-message');
        const codeElement = document.getElementById('activation-code');

        if (status === 'pending') {
            statusElement.textContent = '⏳ Waiting for approval...';
            codeElement.textContent = code;
        } else if (status === 'active') {
            statusElement.textContent = '✅ Activated! Loading player...';
        }
    },

    /**
     * Load player in iframe with cache-busting timestamp
     */
    loadPlayer: function() {
        const state = window.ShellState;
        const timestamp = Date.now();
        const iframe = document.getElementById('player-iframe');

        if (iframe) {
            iframe.src = `player.html?t=${timestamp}&deviceId=${state.deviceId}`;
            console.log('[Shell] Loading player iframe...');

            // Listen for player errors
            iframe.onerror = () => {
                console.error('[Shell] Player iframe failed to load');
                document.getElementById('error-message').textContent =
                    '⚠️ Player failed to load. Retrying...';

                // Retry after 5 seconds
                setTimeout(() => this.loadPlayer(), 5000);
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
        console.log('[Shell] Reloading player...');
        this.loadPlayer();
    }
};

// Expose to global for debugging
window.reloadPlayer = function() {
    window.ShellUI.reloadPlayer();
};
