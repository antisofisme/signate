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

window.ENV = {
  // API Configuration
  API_BASE_URL: 'http://192.168.5.12:8001',
  WEBSOCKET_URL: 'ws://192.168.5.12:8001',

  // Polling & Intervals (in milliseconds)
  POLLING_INTERVAL: 30000,
  HEARTBEAT_INTERVAL: 30000,
  ACTIVATION_POLL_INTERVAL: 2000,
  REGISTRATION_RETRY_INTERVAL: 60000,
  CONTENT_REFRESH_INTERVAL: 60000,
  SPEEDTEST_INTERVAL: 300000,

  // Reset Configuration
  RESET_PASSWORD: 'admin123',

  // Build Info
  BUILD_TIME: '2025-10-27T11:47:18Z',
  ENVIRONMENT: 'production',
};

// Freeze the config to prevent modifications
Object.freeze(window.ENV);

console.log('[Config] Environment loaded:', window.ENV.ENVIRONMENT);
console.log('[Config] API Base URL:', window.ENV.API_BASE_URL);
