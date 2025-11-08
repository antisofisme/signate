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
     * IMPORTANT: Check TV platforms FIRST before browsers
     * (WebOS/Tizen user agents also contain "Chrome" keyword)
     */
    detectPlatform: function() {
        const ua = navigator.userAgent.toLowerCase();

        // TV platforms (CHECK FIRST!)
        if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
        if (ua.includes('tizen')) return 'Tizen';
        if (ua.includes('android tv')) return 'Android TV';

        // Desktop browsers (check after TV platforms)
        if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
        if (ua.includes('firefox')) return 'Firefox';
        if (ua.includes('chrome')) return 'Chrome';
        if (ua.includes('safari')) return 'Safari';

        return 'Browser';
    },

    /**
     * Get device category (tv, browser, or unknown)
     */
    getDeviceCategory: function() {
        const platform = this.detectPlatform();

        // TV platforms
        if (['webOS', 'Tizen', 'Android TV'].includes(platform)) {
            return 'tv';
        }

        // Desktop browsers
        if (['Chrome', 'Firefox', 'Safari', 'Edge', 'Browser'].includes(platform)) {
            return 'browser';
        }

        return 'unknown';
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
            // ✅ Use deviceState (Phase 3)
            const device = window.deviceState.getDevice();
            if (!device || !device.id) return;

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

                // Use APIClient for standardized response handling
                const data = await window.APIClient.post(
                    window.getFullURL(window.API_ENDPOINTS.DEVICES.HEARTBEAT(device.id)),
                    {
                        device_id: parseInt(device.id),
                        platform: this.detectPlatform(),           // 'webOS', 'Chrome', etc (backend schema)
                        ...deviceInfo,
                        // Additional metadata for frontend filtering
                        device_category: this.getDeviceCategory()  // 'tv' or 'browser' (custom field)
                    }
                );

                // ✅ Update last_seen using deviceState (Phase 3)
                window.deviceState.updateLastSeen();

                console.log('[Shell/Heartbeat] ✅ Heartbeat sent');

                // Show WiFi online icon
                if (window.ShellWiFiStatus) {
                    window.ShellWiFiStatus.updateStatus('online');
                }

                // Check for pending commands (reset, refresh, reload)
                if (window.ShellCommands) {
                    await window.ShellCommands.checkAndExecute();
                }

                // Check if display settings changed
                if (window.ShellDisplaySettings) {
                    await window.ShellDisplaySettings.checkAndApplyChanges(data);
                }
            } catch (error) {
                // Handle 403 - Device released (soft delete)
                if (error.status === 403 && error.message?.includes('released')) {
                    console.warn('[Shell/Heartbeat] ⚠️ Device released (403) - Re-registering with saved organization');

                    // Stop heartbeat
                    this.stop();

                    // Clear device_id and device_token (but KEEP organization_id for re-registration)
                    localStorage.removeItem('device_id');
                    localStorage.removeItem('device_token');
                    localStorage.removeItem('device_status');
                    localStorage.removeItem('device_code');
                    // Keep: organization_id (for auto-assign to same org)

                    console.log('[Shell/Heartbeat] 🔄 Triggering re-registration with saved organization_id...');

                    // Delete IndexedDB cache
                    const dbName = 'signage_media_cache';
                    try {
                        await new Promise((resolve) => {
                            const deleteRequest = indexedDB.deleteDatabase(dbName);
                            deleteRequest.onsuccess = () => resolve();
                            deleteRequest.onerror = () => resolve();
                            deleteRequest.onblocked = () => resolve();
                        });
                    } catch (cacheError) {
                        console.error('[Shell/Heartbeat] Error deleting cache:', cacheError);
                    }

                    // Reload to trigger registration with saved organization_id
                    window.location.reload();
                    return;
                }

                // Handle 404 - Device deleted from backend
                if (error.status === 404) {
                    console.warn('[Shell/Heartbeat] ⚠️ Device not found (404) - Device was deleted from backend');
                    console.log('[Shell/Heartbeat] 🔄 Auto-resetting viewer to show new activation code...');

                    // Clear localStorage (preserve organization_id for re-registration)
                    const orgId = localStorage.getItem('organization_id');
                    localStorage.clear();
                    if (orgId) {
                        localStorage.setItem('organization_id', orgId);
                        console.log('[Shell/Heartbeat] 🏢 Preserved organization_id for re-registration');
                    }

                    // Delete IndexedDB cache
                    const dbName = 'signage_media_cache';
                    try {
                        await new Promise((resolve) => {
                            const deleteRequest = indexedDB.deleteDatabase(dbName);
                            deleteRequest.onsuccess = () => resolve();
                            deleteRequest.onerror = () => resolve(); // Continue anyway
                            deleteRequest.onblocked = () => resolve(); // Continue anyway
                        });
                    } catch (cacheError) {
                        console.error('[Shell/Heartbeat] Error deleting cache:', cacheError);
                    }

                    // Reload to show activation screen
                    window.location.reload();
                    return;
                }

                // Network error (server down/unreachable)
                // DON'T clear localStorage or re-register - just show WiFi offline
                console.error('[Shell/Heartbeat] ❌ Network error (server unreachable):', error.message);

                // Show WiFi offline icon
                if (window.ShellWiFiStatus) {
                    window.ShellWiFiStatus.updateStatus('offline');
                }

                // Continue retrying in next heartbeat cycle (don't stop heartbeat)
                console.log('[Shell/Heartbeat] ⏳ Will retry in next heartbeat cycle...');
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
