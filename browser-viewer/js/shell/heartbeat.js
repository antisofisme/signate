/**
 * Shell Heartbeat Module
 * Sends periodic heartbeat to keep device online
 */

window.ShellHeartbeat = {
    /**
     * Collect device information
     */
    getDeviceInfo: function() {
        const info = {
            // Display information
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            device_pixel_ratio: window.devicePixelRatio || 1,

            // Platform information
            user_agent: navigator.userAgent,
            platform: this.detectPlatform(),

            // Connection information
            connection_type: this.getConnectionType(),
            connection_speed: this.getConnectionSpeed()
        };

        return info;
    },

    /**
     * Detect platform type
     */
    detectPlatform: function() {
        const ua = navigator.userAgent.toLowerCase();

        if (ua.includes('webos')) return 'webOS';
        if (ua.includes('tizen')) return 'Tizen';
        if (ua.includes('android tv')) return 'Android TV';
        if (ua.includes('chrome')) return 'Chrome';
        if (ua.includes('firefox')) return 'Firefox';
        if (ua.includes('safari')) return 'Safari';
        if (ua.includes('edge')) return 'Edge';

        return 'Browser';
    },

    /**
     * Get connection type
     */
    getConnectionType: function() {
        if (!navigator.connection) return null;

        const conn = navigator.connection;
        return conn.effectiveType || conn.type || null;
    },

    /**
     * Get connection speed (Mbps)
     */
    getConnectionSpeed: function() {
        if (!navigator.connection || !navigator.connection.downlink) return null;

        return navigator.connection.downlink;
    },

    /**
     * Start heartbeat loop (keep device online)
     */
    start: function() {
        const state = window.ShellState;

        console.log('[Shell/Heartbeat] ⏰ Starting heartbeat (every 30 seconds)');

        state.heartbeatInterval = setInterval(async () => {
            if (!state.deviceId) return;

            try {
                // Collect device info
                const deviceInfo = this.getDeviceInfo();

                // Add ping latency if network diagnostics available
                if (window.ShellNetworkDiagnostics && window.ShellNetworkDiagnostics.quickPing) {
                    const ping = await window.ShellNetworkDiagnostics.quickPing();
                    if (ping !== null) {
                        deviceInfo.ping_ms = ping;
                    }
                }

                const response = await fetch(`${state.API_BASE_URL}/api/devices/heartbeat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: parseInt(state.deviceId),
                        device_type: 'monitor',
                        ...deviceInfo
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('[Shell] Heartbeat sent ✅');

                    // Check for pending commands (reset, refresh, reload)
                    if (window.ShellCommands) {
                        await window.ShellCommands.checkAndExecute();
                    }

                    // Check if display settings changed
                    if (window.ShellDisplaySettings) {
                        await window.ShellDisplaySettings.checkAndApplyChanges(data);
                    }
                } else if (response.status === 404) {
                    // Device deleted from backend - reset viewer
                    console.warn('[Shell] ⚠️ Device not found (404) - Device was deleted from backend');
                    console.log('[Shell] 🔄 Auto-resetting viewer to show new activation code...');

                    // Clear localStorage
                    localStorage.clear();

                    // Delete IndexedDB cache
                    const dbName = 'signage_media_cache';
                    try {
                        await new Promise((resolve) => {
                            const deleteRequest = indexedDB.deleteDatabase(dbName);
                            deleteRequest.onsuccess = () => resolve();
                            deleteRequest.onerror = () => resolve(); // Continue anyway
                            deleteRequest.onblocked = () => resolve(); // Continue anyway
                        });
                    } catch (error) {
                        console.error('[Shell] Error deleting cache:', error);
                    }

                    // Reload to show activation screen
                    window.location.reload();
                }
            } catch (error) {
                console.error('[Shell] Heartbeat error:', error);
            }
        }, state.HEARTBEAT_INTERVAL);
    },

    /**
     * Stop heartbeat
     */
    stop: function() {
        const state = window.ShellState;

        if (state.heartbeatInterval) {
            clearInterval(state.heartbeatInterval);
            state.heartbeatInterval = null;
            console.log('[Shell/Heartbeat] ⏹️ Heartbeat stopped');
        }
    }
};
