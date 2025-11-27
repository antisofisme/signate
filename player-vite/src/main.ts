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

// Import connection logging services
import { ConnectionLogger } from '@shared/services/connection-logger';
import { NetworkSpeedTest } from '@shared/services/network-speed-test';
import { VersionChecker } from '@shared/services/version-checker';

// Import media cache for periodic cleanup
import { mediaCache } from '@shared/storage';

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
 * Initialize application
 */
const initApp = async () => {
  SharedLogger.log('🔍 Initializing app...');

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
