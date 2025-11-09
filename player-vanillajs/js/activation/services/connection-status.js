/**
 * Connection Status Module
 * Manages 2 status indicators:
 * 1. Internet Status - WiFi icon (online/offline)
 * 2. Server Status - Database/Server icon (connected/disconnected)
 */

window.ShellConnectionStatus = {
    /**
     * Update Internet (WiFi) status icon
     * @param {string} status - 'online' or 'offline'
     */
    updateInternet: function(status) {
        const icon = document.getElementById('internet-icon');
        if (!icon) {
            SharedLogger.warn('[ConnectionStatus] Internet icon element not found');
            return;
        }

        if (status === 'online') {
            icon.className = 'status-icon online';
            // Lucide WiFi icon
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M2 8.82a15 15 0 0 1 20 0"/></svg>';
            icon.title = 'Internet: Online';
            SharedLogger.log('[ConnectionStatus] ✅ Internet: ONLINE');
        } else if (status === 'offline') {
            icon.className = 'status-icon offline';
            // Lucide WiFi-Off icon
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M2 2 22 22"/></svg>';
            icon.title = 'Internet: Offline';
            SharedLogger.log('[ConnectionStatus] ❌ Internet: OFFLINE');
        } else {
            SharedLogger.warn('[ConnectionStatus] Invalid internet status:', status);
        }
    },

    /**
     * Update Server status icon
     * @param {string} status - 'connected' or 'disconnected'
     */
    updateServer: function(status) {
        const icon = document.getElementById('server-icon');
        if (!icon) {
            SharedLogger.warn('[ConnectionStatus] Server icon element not found');
            return;
        }

        if (status === 'connected') {
            icon.className = 'status-icon connected';
            // Lucide Server (connected) icon
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg>';
            icon.title = 'Server: Connected';
            SharedLogger.log('[ConnectionStatus] ✅ Server: CONNECTED');
        } else if (status === 'disconnected') {
            icon.className = 'status-icon disconnected';
            // Lucide Server-Off (disconnected) icon with X
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2h13a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-5"/><path d="M10 10 2.5 2.5C2 2 2 2.5 2 3v3a2 2 0 0 0 2 2h6z"/><path d="M22 17v-1a2 2 0 0 0-2-2h-1"/><path d="M4 14a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h16.5l1-.5.5.5-8-8H4z"/><path d="M6 18h.01"/><path d="m2 2 20 20"/></svg>';
            icon.title = 'Server: Disconnected';
            SharedLogger.log('[ConnectionStatus] ❌ Server: DISCONNECTED');
        } else {
            SharedLogger.warn('[ConnectionStatus] Invalid server status:', status);
        }
    },

    /**
     * Get current internet status
     * @returns {string} 'online' or 'offline'
     */
    getInternetStatus: function() {
        const icon = document.getElementById('internet-icon');
        if (!icon) return 'offline';
        return icon.classList.contains('online') ? 'online' : 'offline';
    },

    /**
     * Get current server status
     * @returns {string} 'connected' or 'disconnected'
     */
    getServerStatus: function() {
        const icon = document.getElementById('server-icon');
        if (!icon) return 'disconnected';
        return icon.classList.contains('connected') ? 'connected' : 'disconnected';
    },

    /**
     * Initialize connection status icons (called on page load)
     */
    init: function() {
        SharedLogger.log('[ConnectionStatus] Initializing connection status indicators...');

        // Start both as online/connected by default
        this.updateInternet('online');
        this.updateServer('connected');

        // Listen to online/offline events for internet status
        window.addEventListener('online', () => {
            SharedLogger.log('[ConnectionStatus] Browser detected internet connection restored');
            this.updateInternet('online');
        });

        window.addEventListener('offline', () => {
            SharedLogger.log('[ConnectionStatus] Browser detected internet connection lost');
            this.updateInternet('offline');
        });
    }
};

// BACKWARD COMPATIBILITY: Alias to old ShellWiFiStatus
// This allows old code to continue working without modification
window.ShellWiFiStatus = {
    updateStatus: function(status) {
        // Map old 'online/offline' to server status
        if (status === 'online') {
            window.ShellConnectionStatus.updateServer('connected');
        } else if (status === 'offline') {
            window.ShellConnectionStatus.updateServer('disconnected');
        }
    },
    getStatus: function() {
        return window.ShellConnectionStatus.getServerStatus() === 'connected' ? 'online' : 'offline';
    },
    init: function() {
        window.ShellConnectionStatus.init();
    }
};
