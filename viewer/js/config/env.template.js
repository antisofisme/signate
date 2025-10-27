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
  API_BASE_URL: '${VIEWER_API_URL}',
  WEBSOCKET_URL: '${VIEWER_WEBSOCKET_URL}',

  // Polling & Intervals (in milliseconds)
  POLLING_INTERVAL: ${VIEWER_POLLING_INTERVAL},
  HEARTBEAT_INTERVAL: ${VIEWER_HEARTBEAT_INTERVAL},
  ACTIVATION_POLL_INTERVAL: ${VIEWER_ACTIVATION_POLL_INTERVAL},
  REGISTRATION_RETRY_INTERVAL: ${VIEWER_REGISTRATION_RETRY_INTERVAL},
  CONTENT_REFRESH_INTERVAL: ${VIEWER_CONTENT_REFRESH_INTERVAL},
  SPEEDTEST_INTERVAL: ${VIEWER_SPEEDTEST_INTERVAL},

  // Reset Configuration
  RESET_PASSWORD: '${VIEWER_RESET_PASSWORD}',

  // Build Info
  BUILD_TIME: '${BUILD_TIME}',
  ENVIRONMENT: '${ENVIRONMENT}',
};

// Freeze the config to prevent modifications
Object.freeze(window.ENV);

console.log('[Config] Environment loaded:', window.ENV.ENVIRONMENT);
console.log('[Config] API Base URL:', window.ENV.API_BASE_URL);
