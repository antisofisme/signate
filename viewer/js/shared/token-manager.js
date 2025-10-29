/**
 * Token Manager Module
 *
 * Manages JWT authentication tokens for viewer-backend communication.
 * Handles token storage, expiry checking, and automatic refresh.
 *
 * Features:
 * - Secure token storage in localStorage
 * - Automatic token expiry detection
 * - Token refresh before expiration (24h window)
 * - Authorization header injection
 * - Clean token lifecycle management
 *
 * @version 1.0.0
 * @author Smart TV Digital Signage System
 */

window.TokenManager = {
    /**
     * LocalStorage keys
     */
    KEYS: {
        TOKEN: 'device_token',
        REFRESH_TOKEN: 'device_refresh_token',
        EXPIRES_AT: 'device_token_expires_at'
    },

    /**
     * Token refresh window (24 hours before expiry)
     */
    REFRESH_WINDOW_MS: 24 * 60 * 60 * 1000,

    /**
     * Save token data to localStorage
     *
     * @param {Object} tokenData - Token data from backend
     * @param {string} tokenData.token - JWT access token
     * @param {string} tokenData.refresh_token - JWT refresh token
     * @param {string} tokenData.expires_at - ISO 8601 expiry timestamp
     */
    saveToken: function(tokenData) {
        if (!tokenData || !tokenData.token) {
            console.error('[TokenManager] Invalid token data provided');
            return;
        }

        try {
            localStorage.setItem(this.KEYS.TOKEN, tokenData.token);

            if (tokenData.refresh_token) {
                localStorage.setItem(this.KEYS.REFRESH_TOKEN, tokenData.refresh_token);
            }

            if (tokenData.expires_at) {
                localStorage.setItem(this.KEYS.EXPIRES_AT, tokenData.expires_at);
            }

            console.log('[TokenManager] Token saved successfully');
        } catch (error) {
            console.error('[TokenManager] Failed to save token:', error.message);
        }
    },

    /**
     * Get current token from localStorage
     * Returns null if token is missing or expired
     *
     * @returns {string|null} - JWT access token or null
     */
    getToken: function() {
        const token = localStorage.getItem(this.KEYS.TOKEN);

        if (!token) {
            return null;
        }

        // Check if token is expired
        if (this.isTokenExpired()) {
            console.error('[TokenManager] Token is expired');
            return null;
        }

        return token;
    },

    /**
     * Check if token needs refresh (within 24h of expiry)
     *
     * @returns {boolean} - True if token should be refreshed
     */
    isTokenExpired: function() {
        const expiresAt = localStorage.getItem(this.KEYS.EXPIRES_AT);

        if (!expiresAt) {
            // No expiry time stored, assume token is valid
            return false;
        }

        try {
            const expiryTime = new Date(expiresAt).getTime();
            const currentTime = Date.now();

            // Check if token is already expired
            if (currentTime >= expiryTime) {
                return true;
            }

            // Check if token is within refresh window (24h before expiry)
            const timeUntilExpiry = expiryTime - currentTime;
            return timeUntilExpiry <= this.REFRESH_WINDOW_MS;
        } catch (error) {
            console.error('[TokenManager] Error checking token expiry:', error.message);
            return false;
        }
    },

    /**
     * Refresh token using refresh_token
     * Updates localStorage with new token data
     *
     * @returns {Promise<boolean>} - True if refresh successful
     */
    refreshToken: async function() {
        const refreshToken = localStorage.getItem(this.KEYS.REFRESH_TOKEN);

        if (!refreshToken) {
            console.error('[TokenManager] No refresh token available');
            return false;
        }

        try {
            const state = window.ShellState;
            const response = await fetch(`${state.API_BASE_URL}/api/devices/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) {
                // Refresh failed - token may be revoked
                if (response.status === 401 || response.status === 403) {
                    console.error('[TokenManager] Refresh token invalid or revoked');
                    this.clearToken();
                    return false;
                }

                console.error('[TokenManager] Token refresh failed:', response.status);
                return false;
            }

            const data = await response.json();

            // Save new token data
            this.saveToken({
                token: data.token,
                refresh_token: data.refresh_token,
                expires_at: data.token_expires_at
            });

            console.log('[TokenManager] Token refreshed successfully');
            return true;

        } catch (error) {
            console.error('[TokenManager] Error refreshing token:', error.message);
            return false;
        }
    },

    /**
     * Clear all token data from localStorage
     */
    clearToken: function() {
        try {
            localStorage.removeItem(this.KEYS.TOKEN);
            localStorage.removeItem(this.KEYS.REFRESH_TOKEN);
            localStorage.removeItem(this.KEYS.EXPIRES_AT);
            console.log('[TokenManager] Token cleared');
        } catch (error) {
            console.error('[TokenManager] Error clearing token:', error.message);
        }
    },

    /**
     * Add Authorization header to headers object
     * Automatically refreshes token if needed
     *
     * @param {Object} headers - Existing headers object (default: {})
     * @returns {Promise<Object>} - Headers with Authorization added
     */
    addAuthHeader: async function(headers = {}) {
        // Check if token needs refresh
        if (this.isTokenExpired()) {
            console.log('[TokenManager] Token expired or expiring soon, refreshing...');
            const refreshed = await this.refreshToken();

            if (!refreshed) {
                console.error('[TokenManager] Failed to refresh token, request will proceed without auth');
                return headers;
            }
        }

        const token = this.getToken();

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    },

    /**
     * Check if device has valid token
     *
     * @returns {boolean} - True if token exists and not expired
     */
    hasValidToken: function() {
        const token = localStorage.getItem(this.KEYS.TOKEN);
        return token !== null && !this.isTokenExpired();
    },

    /**
     * Handle 401 Unauthorized response
     * Tries to refresh token once, then clears storage and reloads
     *
     * @param {string} apiBaseUrl - Base URL of the API
     * @returns {Promise<boolean>} - True if token refreshed and caller should retry
     */
    handle401: async function(apiBaseUrl) {
        console.warn('[TokenManager] ⚠️ Received 401 Unauthorized - attempting token refresh');

        // Try refresh once
        const refreshed = await this.refreshToken();

        if (refreshed) {
            console.log('[TokenManager] ✅ Token refreshed successfully, caller should retry request');
            return true; // Caller should retry the failed request
        }

        // Refresh failed - clear everything and restart
        console.error('[TokenManager] ❌ Token refresh failed - resetting viewer');

        // Clear localStorage
        localStorage.clear();

        // Delete IndexedDB cache
        try {
            await new Promise((resolve) => {
                const deleteRequest = indexedDB.deleteDatabase('signage_media_cache');
                deleteRequest.onsuccess = () => resolve();
                deleteRequest.onerror = () => resolve();
                deleteRequest.onblocked = () => resolve();
            });
        } catch (error) {
            console.error('[TokenManager] Error deleting cache:', error);
        }

        // Reload to show activation screen
        console.log('[TokenManager] 🔄 Reloading viewer to show activation screen...');
        window.location.reload();

        return false;
    }
};
