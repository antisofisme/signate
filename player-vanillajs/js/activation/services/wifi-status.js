/**
 * Shell WiFi Status Module
 * Manages WiFi icon indicator for online/offline status
 */

window.ShellWiFiStatus = {
    /**
     * Update WiFi status icon
     * @param {string} status - 'online' or 'offline'
     */
    updateStatus: function(status) {
        const icon = document.getElementById('wifi-icon');
        if (!icon) {
            console.warn('[Shell/WiFiStatus] WiFi icon element not found');
            return;
        }

        if (status === 'online') {
            icon.className = 'online';
            // Lucide WiFi icon
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M2 8.82a15 15 0 0 1 20 0"/></svg>';
            console.log('[Shell/WiFiStatus] ✅ Status: ONLINE');
        } else if (status === 'offline') {
            icon.className = 'offline';
            // Lucide WiFi-Off icon
            icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M2 2 22 22"/></svg>';
            console.log('[Shell/WiFiStatus] ❌ Status: OFFLINE');
        } else {
            console.warn('[Shell/WiFiStatus] Invalid status:', status);
        }
    },

    /**
     * Get current WiFi status
     * @returns {string} 'online' or 'offline'
     */
    getStatus: function() {
        const icon = document.getElementById('wifi-icon');
        if (!icon) return 'offline';
        return icon.classList.contains('online') ? 'online' : 'offline';
    },

    /**
     * Initialize WiFi status (called on page load)
     */
    init: function() {
        console.log('[Shell/WiFiStatus] Initializing WiFi status indicator...');

        // Start as online by default
        this.updateStatus('online');
    }
};
