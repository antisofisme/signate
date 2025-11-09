/**
 * Player-Vite Entry Point
 * Main initialization for TypeScript + Vite player
 */

import './index.css';
import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { ShellBootstrap, ShellActivationScreen } from '@shell';
import { FullscreenManager, HardResetHandler } from '@shell/components';

// Log startup information
SharedLogger.log('🎬 Player-Vite Started');
SharedLogger.log('📋 Configuration loaded:', config);

/**
 * Initialize application
 */
const initApp = async () => {
  SharedLogger.log('🔍 Initializing app...');

  // Ensure containers exist
  let shellContainer = document.getElementById('shell-container');
  let playerContainer = document.getElementById('player-container');

  if (!shellContainer || !playerContainer) {
    SharedLogger.warn('⚠️ Required containers not found, creating them...');

    // Try to find or create app container
    let app = document.getElementById('app');
    if (!app) {
      SharedLogger.warn('⚠️ App element not found, creating it...');
      app = document.createElement('div');
      app.id = 'app';
      document.body.appendChild(app);
    }

    // Create containers
    app.innerHTML = `
      <div id="shell-container"></div>
      <div id="player-container" style="display: none;">
        <video id="player-video" style="width: 100%; height: 100vh;"></video>
      </div>
    `;

    // Re-query containers after creation
    shellContainer = document.getElementById('shell-container');
    playerContainer = document.getElementById('player-container');

    if (!shellContainer || !playerContainer) {
      SharedLogger.error('❌ Failed to create containers - cannot proceed');
      return;
    }

    SharedLogger.log('✅ Containers created');
  } else {
    SharedLogger.log('✅ Containers found');
  }

  SharedLogger.log('🎨 Rendering activation screen...');

  // Render activation screen (will be shown if device is not activated)
  ShellActivationScreen.render('shell-container');

  // Expose ShellActivationScreen globally for updates after registration
  window.ShellActivationScreen = ShellActivationScreen;

  // Initialize UI components
  SharedLogger.log('🎮 Initializing UI components...');
  FullscreenManager.init();
  HardResetHandler.init();

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
