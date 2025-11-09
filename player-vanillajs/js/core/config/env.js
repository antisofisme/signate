/**
 * Environment Configuration Template for Viewer
 * ==============================================
 * This file is a template that gets populated with actual values during build/deployment.
 *
 * To generate actual env.js:
 * 1. From project root, run: ./viewer/generate-config.sh
 * 2. Or manually: envsubst < viewer/js/config/env.template.js > viewer/js/config/env.js
 *
 * The generated env.js file will be loaded by the viewer application.
 */

window.SharedENV = {
  // API Configuration
  API_BASE_URL: 'http://192.168.5.12:8001',
  WEBSOCKET_URL: 'ws://192.168.5.12:8001',

  // Polling & Intervals (in milliseconds)
  POLLING_INTERVAL: 30000,
  HEARTBEAT_INTERVAL: 30000,
  ACTIVATION_POLL_INTERVAL: 2000,
  ACTIVATION_POLL_FAST_INTERVAL: 5000,
  REGISTRATION_RETRY_INTERVAL: 60000,
  CONTENT_REFRESH_INTERVAL: 60000,
  PLAYLIST_CHECK_INTERVAL: 60000,
  SPEEDTEST_INTERVAL: 300000,

  // Retry & Timeout (in milliseconds)
  RETRY_INTERVAL: 10000,           // Default retry interval
  PLAYER_RETRY_INTERVAL: 5000,     // Player loading retry
  TOAST_DURATION: 5000,             // Toast notification duration
  COMMAND_TIMEOUT: 30000,           // Command execution timeout
  HLS_MANIFEST_TIMEOUT: 10000,      // HLS manifest loading timeout
  HLS_LEVEL_TIMEOUT: 10000,         // HLS level loading timeout

  // WebSocket Configuration (in milliseconds)
  WEBSOCKET_MAX_RECONNECT_DELAY: 30000,
  WEBSOCKET_HEARTBEAT_INTERVAL: 30000,

  // Build Info
  BUILD_TIME: '2025-10-27T11:47:18Z',
  ENVIRONMENT: 'production',
};

// Freeze the config to prevent modifications
Object.freeze(window.SharedENV);

SharedLogger.log('[Config] Environment loaded:', window.SharedENV.ENVIRONMENT);
SharedLogger.log('[Config] API Base URL:', window.SharedENV.API_BASE_URL);
