/**
 * Centralized API Endpoints
 * Single source of truth for all API routes
 *
 * Usage (Vanilla JS):
 *   window.API_ENDPOINTS.DEVICES.ACTIVATE
 *   window.getFullURL(window.API_ENDPOINTS.DEVICES.HEARTBEAT)
 */

(function() {
  'use strict';

  // Base API URL (from env.js)
  const getBaseURL = () => {
    return window.ENV?.API_BASE_URL || 'http://192.168.5.12:8001';
  };

  const API_V1 = '/api/v1';

  // Centralized API Endpoints
  window.API_ENDPOINTS = {
    // Device Management
    DEVICES: {
      REGISTER: `${API_V1}/devices/monitor`,
      HEARTBEAT: (deviceId) => `${API_V1}/devices/${deviceId}/heartbeat`,
      CONTENT_RESOLVED: (deviceId) => `${API_V1}/devices/${deviceId}/content/resolved`,
      COMMANDS_PENDING: (deviceId) => `${API_V1}/devices/${deviceId}/commands/pending`,
      COMMANDS_EXECUTE: (deviceId, commandId) => `${API_V1}/devices/${deviceId}/commands/${commandId}/execute`,
      LOGS: (deviceId) => `${API_V1}/devices/${deviceId}/logs`,
      RELEASE: (deviceId) => `${API_V1}/devices/${deviceId}/release`,
      VALIDATE_RESET_PASSWORD: `${API_V1}/devices/validate-reset-password`,
    },

    // Playlist Management
    PLAYLISTS: {
      GET: (deviceId) => `${API_V1}/playlists?device_id=${deviceId}`,
    },
  };

  /**
   * Get full URL by combining base URL with endpoint
   * @param {string} endpoint - API endpoint path
   * @returns {string} Full URL
   */
  window.getFullURL = function(endpoint) {
    const baseURL = getBaseURL();
    return `${baseURL}${endpoint}`;
  };

  console.log('[API/Endpoints] Centralized endpoints loaded');
})();

