/**
 * Player-Vite Entry Point
 * Main initialization for TypeScript + Vite player
 */

import './index.css';
import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { ShellBootstrap, ShellActivationScreen } from '@shell';
import { FullscreenManager, HardResetHandler, ClearCacheHandler } from '@shell/components';
import { DeviceInfoPopup, ConnectionLogPopup } from '@player/components';
import { SharedToast } from '@shared/ui';

// Import connection logging services
import { ConnectionLogger } from '@shared/services/connection-logger';
import { NetworkSpeedTest } from '@shared/services/network-speed-test';

// Import ServiceRegistry
import { ServiceRegistry } from '@shared/services';

// Log startup information
SharedLogger.log('🎬 Player-Vite Started');
SharedLogger.log('📋 Configuration loaded:', config);

// Force evaluation of connection logging services (ensures window.* is set before bootstrap)
void ConnectionLogPopup;
void ConnectionLogger;
void NetworkSpeedTest;

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

  // Initialize connection logging services EARLY (before bootstrap needs them)
  SharedLogger.log('📊 Initializing connection logging services...');
  await ConnectionLogger.init();
  NetworkSpeedTest.init();
  ConnectionLogPopup.init();
  SharedLogger.log('[Main] ✅ Connection logging services initialized');

  // Bootstrap device initialization
  SharedLogger.log('🚀 Initializing ShellBootstrap...');
  await ShellBootstrap.init();
};

// Start app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => void initApp());
} else {
  void initApp();
}
