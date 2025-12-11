/**
 * Player-Vite Entry Point
 * Main initialization for TypeScript + Vite player
 * @version 2025-01-18-v3 - Console interceptor initialized FIRST
 *
 * CRITICAL: Console interceptor MUST be initialized BEFORE SharedLogger
 * to ensure it captures all console.log/info/warn/error calls from SharedLogger.
 * SharedLogger stores original console references at import time, so we must
 * intercept console methods BEFORE SharedLogger is imported.
 */

import './index.css';

// STEP 1: Initialize console interceptor FIRST (before any logging)
// This must happen before SharedLogger is imported to capture all logs
import { ConsoleInterceptor } from './lib/console-interceptor/console-interceptor';
import type { ConsoleInterceptorConfig } from './lib/console-interceptor/console-interceptor.types';

// Create and start console interceptor immediately
// We'll update the deviceId later when device is activated
const earlyInterceptorConfig: ConsoleInterceptorConfig = {
  apiBaseUrl: '', // Will be set later when device is loaded
  deviceId: 0, // Will be set later when device is loaded
  maxBatchSize: 1000, // Buffer size (FIFO)
  enabled: false, // Disabled until device is loaded
  captureLogLevels: ['log', 'info', 'warn', 'error', 'debug'],
  excludeNamespaces: ['[ConsoleInterceptor]'],
  maxMessageLength: 5000,
  debug: true,
};

// Create interceptor instance but don't start yet (enabled: false)
const globalConsoleInterceptor = new ConsoleInterceptor(earlyInterceptorConfig);
globalConsoleInterceptor.start(); // Start intercepting (but won't upload until enabled)

// Expose for later configuration
(window as any).__consoleInterceptor = globalConsoleInterceptor;

// STEP 2: Now import SharedLogger - it will use intercepted console methods
import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { ShellBootstrap, ShellActivationScreen } from '@shell';
import { FullscreenManager, HardResetHandler, ClearCacheHandler } from '@shell/components';
import { DeviceInfoPopup, ConnectionLogPopup } from '@player/components';
import { SharedToast } from '@shared/ui';

// Menu Viewer for public menu display
import { MenuViewer } from './menu';

// Portal Viewer for unified menu portal
import { PortalViewer } from './portal';

// Import connection logging services
import { ConnectionLogger } from '@shared/services/connection-logger';
import { NetworkSpeedTest } from '@shared/services/network-speed-test';
import { VersionChecker } from '@shared/services/version-checker';

// Import media cache for periodic cleanup
import { mediaCache, deviceConfigStorage } from '@shared/storage';

// Import player services to trigger registration
import { PlayerPlaylistSync } from '@player/services';

// Import ServiceRegistry
import { ServiceRegistry } from '@shared/services';

// Import WebSocket client for console streaming
import { consoleWebSocketClient } from '@shared/services/console-websocket-client';

// Log startup information
SharedLogger.log('🎬 Player-Vite Started (Console Interceptor Active)');
SharedLogger.log('📋 Configuration loaded:', config);

// Force evaluation of connection logging services (ensures window.* is set before bootstrap)
void ConnectionLogPopup;
void ConnectionLogger;
void NetworkSpeedTest;
void PlayerPlaylistSync;

/**
 * Check if current URL is a public menu route
 * Format: /menu/{public_url_code}
 */
const isMenuRoute = (): { isMenu: boolean; publicCode: string | null } => {
  const path = window.location.pathname;
  const menuMatch = path.match(/^\/menu\/([a-zA-Z0-9]+)$/);

  if (menuMatch) {
    return { isMenu: true, publicCode: menuMatch[1] };
  }

  return { isMenu: false, publicCode: null };
};

/**
 * Check if current URL is a portal route
 * Format: /portal/{portal_slug}
 * Example: /portal/hotel-signage-demo-22
 */
const isPortalRoute = (): { isPortal: boolean; portalSlug: string | null } => {
  const path = window.location.pathname;
  // Match slug format: lowercase letters, numbers, and dashes
  const portalMatch = path.match(/^\/portal\/([a-z0-9-]+)$/);

  if (portalMatch) {
    return { isPortal: true, portalSlug: portalMatch[1] };
  }

  return { isPortal: false, portalSlug: null };
};

/**
 * Check if current URL is a device route
 * Format: /device/{device_id}
 * Example: /device/7680
 *
 * This route is used for persistent device identification.
 * After activation, player redirects to /device/{device_id}.
 * IndexedDB stores device credentials that only hard reset can clear.
 */
const isDeviceRoute = (): { isDevice: boolean; deviceId: number | null } => {
  const path = window.location.pathname;
  // Match device ID format: /device/{numeric_id}
  const deviceMatch = path.match(/^\/device\/(\d+)$/);

  if (deviceMatch) {
    return { isDevice: true, deviceId: parseInt(deviceMatch[1], 10) };
  }

  return { isDevice: false, deviceId: null };
};

/**
 * Handle device route validation
 * Validates URL device_id against stored credentials in IndexedDB
 *
 * Security:
 * - If no credentials in IndexedDB → redirect to /
 * - If device_id mismatch → show error and redirect to /
 * - If valid → continue with player bootstrap
 */
const handleDeviceRoute = async (urlDeviceId: number): Promise<boolean> => {
  SharedLogger.log(`[DeviceRoute] Validating device ID from URL: ${urlDeviceId}`);

  // Get stored config from IndexedDB
  const config = await deviceConfigStorage.getDeviceConfig();

  // Check if we have stored device credentials
  if (!config.device_id) {
    SharedLogger.warn('[DeviceRoute] No device credentials in IndexedDB, redirecting to /');
    window.location.href = '/';
    return false;
  }

  // Validate URL device_id against stored device_id
  if (config.device_id !== urlDeviceId) {
    SharedLogger.error(
      `[DeviceRoute] Device ID mismatch! URL: ${urlDeviceId}, Stored: ${config.device_id}`
    );
    SharedLogger.warn('[DeviceRoute] This may be a different device trying to use same URL');
    // Show error toast and redirect
    alert(`Device ID mismatch. This URL is for device ${urlDeviceId}, but this device is ${config.device_id}`);
    window.location.href = '/';
    return false;
  }

  SharedLogger.log('[DeviceRoute] ✅ Device ID validated successfully');
  return true;
};

/**
 * Handle root route - check for existing device and redirect
 * If device exists in IndexedDB, redirect to /device/{device_id}
 */
const handleRootRoute = async (): Promise<boolean> => {
  const path = window.location.pathname;

  // Only handle exact root path
  if (path !== '/') {
    return true; // Not root, continue normally
  }

  SharedLogger.log('[RootRoute] Checking for existing device credentials...');

  // Get stored config from IndexedDB
  const storedConfig = await deviceConfigStorage.getDeviceConfig();

  // If we have a device_id, redirect to /device/{device_id}
  if (storedConfig.device_id) {
    SharedLogger.log(`[RootRoute] Found existing device, redirecting to /device/${storedConfig.device_id}`);
    window.location.href = `/device/${storedConfig.device_id}`;
    return false; // Stop current initialization, redirect will handle it
  }

  SharedLogger.log('[RootRoute] No existing device, continuing with normal bootstrap');
  return true; // Continue with normal bootstrap (show activation screen)
};

/**
 * Initialize Menu Viewer for public menu display
 */
const initMenuViewer = async (publicCode: string) => {
  console.log('[MenuViewer] Initializing for code:', publicCode);

  // Hide other containers
  const shellContainer = document.getElementById('shell-container');
  const playerContainer = document.getElementById('player-container');
  const menuContainer = document.getElementById('menu-container');

  if (shellContainer) shellContainer.style.display = 'none';
  if (playerContainer) playerContainer.style.display = 'none';
  if (menuContainer) menuContainer.style.display = 'block';

  // Hide all floating buttons
  const floatingButtons = document.querySelectorAll(
    '#enter-fullscreen-btn, #exit-fullscreen-btn, #clear-cache-btn, #factory-reset-btn, #device-info-btn, #connection-status'
  );
  floatingButtons.forEach((btn) => {
    (btn as HTMLElement).style.display = 'none';
  });

  // Initialize Menu Viewer
  const viewer = new MenuViewer({
    apiBaseUrl: config.api.baseURL,
    publicCode: publicCode,
  });

  await viewer.init('menu-container');
};

/**
 * Initialize Portal Viewer for unified menu portal
 */
const initPortalViewer = async (portalSlug: string) => {
  console.log('[PortalViewer] Initializing for slug:', portalSlug);

  // Hide other containers
  const shellContainer = document.getElementById('shell-container');
  const playerContainer = document.getElementById('player-container');
  const menuContainer = document.getElementById('menu-container');

  if (shellContainer) shellContainer.style.display = 'none';
  if (playerContainer) playerContainer.style.display = 'none';
  if (menuContainer) menuContainer.style.display = 'block';

  // Hide all floating buttons
  const floatingButtons = document.querySelectorAll(
    '#enter-fullscreen-btn, #exit-fullscreen-btn, #clear-cache-btn, #factory-reset-btn, #device-info-btn, #connection-status'
  );
  floatingButtons.forEach((btn) => {
    (btn as HTMLElement).style.display = 'none';
  });

  // Get or create container
  const container = document.getElementById('menu-container');
  if (!container) {
    console.error('[PortalViewer] Container not found');
    return;
  }

  // Initialize Portal Viewer
  const viewer = new PortalViewer(container, {
    apiBaseUrl: config.api.baseURL,
    portalSlug: portalSlug,
  });

  await viewer.load();
};

/**
 * Initialize application
 */
const initApp = async () => {
  SharedLogger.log('🔍 Initializing app...');

  // Check if this is a portal route - if so, show PortalViewer
  const { isPortal, portalSlug } = isPortalRoute();
  if (isPortal && portalSlug) {
    SharedLogger.log('🏨 Portal route detected, initializing Portal Viewer...');
    await initPortalViewer(portalSlug);
    return; // Exit early, don't initialize player
  }

  // Check if this is a menu route - if so, show MenuViewer instead of Player
  const { isMenu, publicCode } = isMenuRoute();
  if (isMenu && publicCode) {
    SharedLogger.log('🍽️ Menu route detected, initializing Menu Viewer...');
    await initMenuViewer(publicCode);
    return; // Exit early, don't initialize player
  }

  // Check if this is a device route - validate device ID
  const { isDevice, deviceId: urlDeviceId } = isDeviceRoute();
  if (isDevice && urlDeviceId) {
    SharedLogger.log(`📺 Device route detected: /device/${urlDeviceId}`);
    const isValid = await handleDeviceRoute(urlDeviceId);
    if (!isValid) {
      return; // Redirect will happen, stop initialization
    }
    // Device validated, continue with player bootstrap
    SharedLogger.log('[DeviceRoute] Continuing with validated device...');
  } else {
    // Check if root route needs redirect to /device/{id}
    const shouldContinue = await handleRootRoute();
    if (!shouldContinue) {
      return; // Redirect will happen, stop initialization
    }
  }

  // Verify containers exist (should already be in index.html)
  const shellContainer = document.getElementById('shell-container');
  const playerContainer = document.getElementById('player-container');

  if (!shellContainer || !playerContainer) {
    SharedLogger.error('❌ Required containers not found in index.html - cannot proceed');
    SharedLogger.error('   Make sure #shell-container and #player-container exist in index.html');
    return;
  }

  SharedLogger.log('✅ Containers found in DOM');

  SharedLogger.log('🎨 Rendering activation screen...');

  // Render activation screen (will be shown if device is not activated)
  // Now async to load activation code from IndexedDB
  await ShellActivationScreen.render('shell-container');

  // Register ShellActivationScreen to ServiceRegistry
  ServiceRegistry.register('ShellActivationScreen', ShellActivationScreen);

  // Initialize UI components
  SharedLogger.log('🎮 Initializing UI components...');

  // Initialize toast system FIRST (other components depend on it)
  SharedToast.init();

  FullscreenManager.init();
  HardResetHandler.init();
  ClearCacheHandler.init();
  DeviceInfoPopup.init();

  // Register UI popups to ServiceRegistry
  ServiceRegistry.register('DeviceInfoPopup', DeviceInfoPopup);
  ServiceRegistry.register('ConnectionLogPopup', ConnectionLogPopup);

  // Initialize version checker FIRST (auto-reload on new build)
  SharedLogger.log('🔄 Initializing version checker...');
  await VersionChecker.init();

  // Initialize connection logging services EARLY (before bootstrap needs them)
  SharedLogger.log('📊 Initializing connection logging services...');
  await ConnectionLogger.init();
  NetworkSpeedTest.init();
  ConnectionLogPopup.init();
  SharedLogger.log('[Main] ✅ Connection logging services initialized');

  // Start periodic cache cleanup (runs every 24 hours)
  SharedLogger.log('🧹 Starting periodic cache cleanup...');
  mediaCache.startPeriodicCleanup(24 * 60 * 60 * 1000); // 24 hours
  SharedLogger.log('[Main] ✅ Periodic cache cleanup scheduled');

  // Bootstrap device initialization FIRST (loads device from storage)
  SharedLogger.log('🚀 Initializing ShellBootstrap...');
  await ShellBootstrap.init();

  // Configure console interceptor with deviceId now that device is loaded
  SharedLogger.log('🔍 Configuring console interceptor with device info...');

  // Get the global interceptor we created at startup
  const interceptor = (window as any).__consoleInterceptor as ConsoleInterceptor;

  if (interceptor) {
    // Import device state to get deviceId
    const { SharedDeviceState } = await import('@shared/device');
    const deviceIdStr = SharedDeviceState.getDeviceId();

    if (deviceIdStr) {
      const deviceId = parseInt(deviceIdStr, 10);

      // Update interceptor config with device info
      const updatedConfig: ConsoleInterceptorConfig = {
        apiBaseUrl: config.api.baseURL + '/api/v1',
        deviceId: deviceId,
        maxBatchSize: 1000, // Buffer size (FIFO)
        enabled: true, // NOW ENABLE IT!
        captureLogLevels: ['log', 'info', 'warn', 'error', 'debug'],
        excludeNamespaces: ['[ConsoleInterceptor]'],
        maxMessageLength: 5000,
        debug: true,
      };

      // Stop and restart with new config
      interceptor.stop();
      const newInterceptor = new ConsoleInterceptor(updatedConfig);
      newInterceptor.start();
      (window as any).__consoleInterceptor = newInterceptor;

      SharedLogger.log('[Main] ✅ Console interceptor enabled', {
        deviceId,
        apiBaseUrl: config.api.baseURL,
      });

      // Initialize SharedWebSocket for real-time updates (playlist/content changes)
      SharedLogger.log('[Main] Initializing SharedWebSocket for real-time updates...');
      try {
        const { SharedWebSocket } = await import('@shared/websocket');
        SharedWebSocket.connect();
        SharedLogger.log('[Main] ✅ SharedWebSocket connection initiated');
      } catch (wsError) {
        SharedLogger.warn('[Main] ⚠️ SharedWebSocket connection failed:', wsError);
      }

      // Initialize WebSocket control client for console streaming
      SharedLogger.log('[Main] Initializing console WebSocket client...');

      try {
        consoleWebSocketClient.connect();

        // Listen for streaming commands from backend
        consoleWebSocketClient.on('start_streaming', () => {
          SharedLogger.log('[Main] Backend requested streaming start');

          // Send all buffered logs (historical)
          const buffered = newInterceptor.getBufferedLogs();
          if (buffered.length > 0) {
            consoleWebSocketClient.sendLogs(buffered, 'historical');
            SharedLogger.log(`[Main] Sent ${buffered.length} historical logs`);
          }

          // Start real-time streaming
          newInterceptor.startStreaming();
        });

        consoleWebSocketClient.on('stop_streaming', () => {
          SharedLogger.log('[Main] Backend requested streaming stop');
          newInterceptor.stopStreaming();
        });

        // Forward interceptor events to WebSocket
        newInterceptor.addEventListener((log) => {
          consoleWebSocketClient.sendLogs([log], 'realtime');
        });

        SharedLogger.log('[Main] ✅ Console streaming system initialized');
      } catch (error) {
        SharedLogger.error('[Main] ❌ Failed to initialize console WebSocket client:', error);
      }
    } else {
      SharedLogger.warn('[Main] ⚠️ Device not activated, console interceptor remains disabled');
    }
  } else {
    SharedLogger.error('[Main] ❌ Console interceptor not found!');
  }
};

// Start app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => void initApp());
} else {
  void initApp();
}
