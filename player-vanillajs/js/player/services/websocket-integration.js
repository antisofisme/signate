/**
 * Player WebSocket Integration
 *
 * Integrates SignageWebSocket with the Player for real-time updates.
 * Handles playlist updates, content ready events, and admin commands.
 * Provides graceful fallback to HTTP polling when WebSocket fails.
 *
 * Features:
 * - Real-time playlist updates (<1s latency)
 * - Instant content ready notifications
 * - Remote admin commands (reload, refresh, reset)
 * - Automatic fallback to HTTP polling
 * - Connection status monitoring
 *
 * @author Smart TV Digital Signage System
 * @version 1.0.0
 */

window.PlayerWebSocket = {
    // WebSocket client instance
    ws: null,

    // Fallback polling
    pollingEnabled: false,
    pollingInterval: null,

    // Connection status
    isWebSocketActive: false,

    /**
     * Initialize WebSocket connection after device activation
     */
    initialize: function() {
        // ✅ STATE MIGRATION: Get deviceId from PlayerState (runtime param, not migrated to playerState)
        // deviceId is passed via URL params and stored in OLD PlayerState for backward compatibility
        const deviceId = window.PlayerState?.deviceId;

        // ✅ NULL CHECK: Ensure deviceId exists
        if (!deviceId) {
            console.warn('[Player/WebSocket] No device ID - skipping WebSocket initialization');
            return;
        }

        // ✅ STATE MIGRATION: Get API_BASE_URL from Config/ENV (config, not state)
        const apiBaseUrl = window.Config?.API_BASE_URL || window.ENV?.API_BASE_URL;

        // ✅ NULL CHECK: Ensure API_BASE_URL exists
        if (!apiBaseUrl) {
            console.error('[Player/WebSocket] No API_BASE_URL configured');
            return;
        }

        console.log('[Player/WebSocket] Initializing WebSocket for device:', deviceId);

        try {
            // Create WebSocket client
            this.ws = new window.SignageWebSocket(deviceId, apiBaseUrl);

            // Register event handlers
            this._registerHandlers();

            // Connect
            this.ws.connect();

        } catch (error) {
            console.error('[Player/WebSocket] Failed to initialize WebSocket:', error);
            this._enableFallbackPolling();
        }
    },

    /**
     * Register WebSocket event handlers
     * @private
     */
    _registerHandlers: function() {
        // Connection events
        this.ws.on('connected', () => {
            console.log('[Player/WebSocket] ✅ Connected - Real-time updates enabled');
            this.isWebSocketActive = true;

            // Disable fallback polling if active
            if (this.pollingEnabled) {
                this._disableFallbackPolling();
            }

            // Show connection status (optional)
            this._showConnectionStatus('connected');
        });

        this.ws.on('disconnected', () => {
            console.log('[Player/WebSocket] 🔌 Disconnected');
            this.isWebSocketActive = false;
            this._showConnectionStatus('disconnected');
        });

        this.ws.on('reconnecting', (data) => {
            console.log(`[Player/WebSocket] 🔄 Reconnecting (${data.attempt}/${data.maxAttempts})...`);
            this._showConnectionStatus('reconnecting', data);
        });

        this.ws.on('failed', () => {
            console.error('[Player/WebSocket] ⛔ Connection failed - falling back to HTTP polling');
            this.isWebSocketActive = false;
            this._showConnectionStatus('failed');
            this._enableFallbackPolling();
        });

        this.ws.on('error', (error) => {
            console.error('[Player/WebSocket] ❌ Error:', error);
        });

        // Message type handlers
        this.ws.on('playlist_update', (data) => {
            this._handlePlaylistUpdate(data);
        });

        this.ws.on('content_ready', (data) => {
            this._handleContentReady(data);
        });

        this.ws.on('command', (data) => {
            this._handleCommand(data);
        });

        // Generic message handler (for debugging)
        this.ws.on('message', (message) => {
            if (this._isDebugMode()) {
                console.log('[Player/WebSocket] Message received:', message);
            }
        });
    },

    /**
     * Handle playlist update event
     * Reloads playlist immediately
     * @private
     */
    _handlePlaylistUpdate: async function(data) {
        console.log('[Player/WebSocket] 📋 Playlist update received:', data);

        try {
            // Show notification
            this._showNotification('🔄 Playlist updated - reloading...');

            // Reload playlist
            if (window.PlayerAPI && window.PlayerAPI.loadPlaylist) {
                await window.PlayerAPI.loadPlaylist();
                console.log('[Player/WebSocket] ✅ Playlist reloaded successfully');
            }

        } catch (error) {
            console.error('[Player/WebSocket] Failed to reload playlist:', error);
        }
    },

    /**
     * Handle content ready event
     * Content has been uploaded/processed and is ready to display
     * @private
     */
    _handleContentReady: async function(data) {
        console.log('[Player/WebSocket] 📦 Content ready:', data);

        try {
            const { content_id, content_type } = data;

            // Show notification
            this._showNotification(`✅ New ${content_type} content available`);

            // Refresh playlist to include new content
            if (window.PlayerAPI && window.PlayerAPI.checkPlaylistUpdate) {
                await window.PlayerAPI.checkPlaylistUpdate();
            }

        } catch (error) {
            console.error('[Player/WebSocket] Failed to handle content ready:', error);
        }
    },

    /**
     * Handle admin command event
     * Execute commands from web admin (reload, refresh, reset, etc.)
     * @private
     */
    _handleCommand: async function(data) {
        console.log('[Player/WebSocket] 🎮 Command received:', data);

        const { command, params = {} } = data;

        try {
            switch (command) {
                case 'reload':
                    // Reload entire viewer
                    console.log('[Player/WebSocket] Executing: Reload viewer');
                    this._showNotification('🔄 Reloading viewer...');
                    setTimeout(() => window.location.reload(), 1000);
                    break;

                case 'refresh':
                    // Refresh playlist and cache
                    console.log('[Player/WebSocket] Executing: Refresh playlist');
                    this._showNotification('🔄 Refreshing content...');
                    if (window.PlayerAPI && window.PlayerAPI.loadPlaylist) {
                        await window.PlayerAPI.loadPlaylist();
                    }
                    break;

                case 'reset':
                    // Reset device (clear cache and re-register)
                    console.log('[Player/WebSocket] Executing: Reset device');
                    this._showNotification('🔄 Resetting device...');
                    localStorage.clear();
                    setTimeout(() => window.location.reload(), 1000);
                    break;

                case 'clear_cache':
                    // Clear media cache
                    console.log('[Player/WebSocket] Executing: Clear cache');
                    this._showNotification('🗑️ Clearing cache...');
                    if (window.PlayerCache && window.PlayerCache.clearAll) {
                        await window.PlayerCache.clearAll();
                    }
                    break;

                case 'volume':
                    // Set volume
                    const { level = 50 } = params;
                    console.log('[Player/WebSocket] Executing: Set volume to', level);
                    if (window.PlayerPlayback && window.PlayerPlayback.setVolume) {
                        window.PlayerPlayback.setVolume(level);
                    }
                    break;

                default:
                    console.warn('[Player/WebSocket] Unknown command:', command);
            }

        } catch (error) {
            console.error('[Player/WebSocket] Failed to execute command:', error);
        }
    },

    /**
     * Enable fallback HTTP polling
     * Used when WebSocket connection fails
     * @private
     */
    _enableFallbackPolling: function() {
        if (this.pollingEnabled) {
            console.warn('[Player/WebSocket] Polling already enabled');
            return;
        }

        console.log('[Player/WebSocket] 📡 Enabling fallback HTTP polling (60s interval)');
        this.pollingEnabled = true;

        // Poll every 60 seconds (less frequent than original 30s to reduce server load)
        const pollInterval = 60000;

        this.pollingInterval = setInterval(async () => {
            if (!this.pollingEnabled) return;

            try {
                // Check for playlist updates
                if (window.PlayerAPI && window.PlayerAPI.checkPlaylistUpdate) {
                    await window.PlayerAPI.checkPlaylistUpdate();
                }

                // Check for commands
                if (window.ShellCommands && window.ShellCommands.checkAndExecute) {
                    await window.ShellCommands.checkAndExecute();
                }

            } catch (error) {
                console.error('[Player/WebSocket] Polling error:', error);
            }
        }, pollInterval);

        this._showNotification('📡 Using HTTP polling mode');
    },

    /**
     * Disable fallback HTTP polling
     * Called when WebSocket reconnects successfully
     * @private
     */
    _disableFallbackPolling: function() {
        if (!this.pollingEnabled) return;

        console.log('[Player/WebSocket] Disabling fallback HTTP polling');
        this.pollingEnabled = false;

        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    },

    /**
     * Show connection status indicator
     * @private
     */
    _showConnectionStatus: function(status, data = {}) {
        // Check if network status element exists
        const networkStatus = document.getElementById('network-status');
        const networkLabel = document.getElementById('network-label');
        const networkIndicator = document.querySelector('.network-indicator');

        if (!networkStatus || !networkLabel || !networkIndicator) return;

        switch (status) {
            case 'connected':
                networkStatus.classList.add('visible');
                networkLabel.textContent = 'WebSocket Connected';
                networkIndicator.classList.remove('slow', 'poor');

                // Auto-hide after 3 seconds
                setTimeout(() => {
                    networkStatus.classList.remove('visible');
                }, 3000);
                break;

            case 'reconnecting':
                networkStatus.classList.add('visible');
                networkLabel.textContent = `Reconnecting (${data.attempt}/${data.maxAttempts})...`;
                networkIndicator.classList.add('slow');
                networkIndicator.classList.remove('poor');
                break;

            case 'failed':
                networkStatus.classList.add('visible');
                networkLabel.textContent = 'WebSocket Failed - Using Polling';
                networkIndicator.classList.add('poor');
                networkIndicator.classList.remove('slow');
                break;

            case 'disconnected':
                // Don't show anything for normal disconnect
                break;
        }
    },

    /**
     * Show notification message
     * @private
     */
    _showNotification: function(message) {
        // Try to use existing notification element
        const notification = document.getElementById('quality-notification');
        const notificationText = document.getElementById('quality-notification-text');

        if (notification && notificationText) {
            notificationText.textContent = message;
            notification.classList.add('visible');

            // Auto-hide after 3 seconds
            setTimeout(() => {
                notification.classList.remove('visible');
            }, 3000);
        } else {
            // Fallback to console
            console.log('[Player/WebSocket]', message);
        }
    },

    /**
     * Check if WebSocket is active
     */
    isActive: function() {
        return this.isWebSocketActive && this.ws && this.ws.isConnected();
    },

    /**
     * Get connection stats
     */
    getStats: function() {
        if (this.ws) {
            return this.ws.getStats();
        }
        return null;
    },

    /**
     * Disconnect WebSocket
     */
    disconnect: function() {
        if (this.ws) {
            this.ws.disconnect();
        }

        if (this.pollingEnabled) {
            this._disableFallbackPolling();
        }
    },

    /**
     * Check if debug mode is enabled
     * @private
     */
    _isDebugMode: function() {
        try {
            return localStorage.getItem('WS_DEBUG') === 'true' ||
                   localStorage.getItem('API_DEBUG') === 'true';
        } catch (e) {
            return false;
        }
    }
};

console.log('[Player/WebSocket] Integration module loaded (v1.0.0)');
