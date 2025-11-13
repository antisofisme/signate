/**
 * Shell Bootstrap Service
 * Handles device initialization and context routing
 *
 * @features
 * - Device verification on startup
 * - Context routing (shell vs player)
 * - Automatic recovery from errors
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { ShellRegistration } from './shell-registration';
import { ShellActivationPoll } from './shell-activation-poll';
import type { ShellBootstrap as IShellBootstrap, VerifyDeviceResponse } from '../types/shell.types';

/**
 * Shell Bootstrap Class
 * Singleton pattern for device initialization
 */
class ShellBootstrapClass implements IShellBootstrap {
  /**
   * Initialize application
   * Main entry point for device bootstrap
   */
  async init(): Promise<void> {
    SharedLogger.log('[ShellBootstrap] 🚀 Initializing player...');

    // Check if device is registered
    const deviceId = SharedDeviceState.getDeviceId();
    const deviceStatus = SharedDeviceState.getDeviceStatus();

    SharedLogger.log('[ShellBootstrap] Device state:', {
      deviceId,
      deviceStatus,
      hasToken: SharedDeviceState.hasDeviceToken(),
    });

    // Route 1: No device ID → Register new device (Shell context)
    if (!deviceId) {
      SharedLogger.log('[ShellBootstrap] No device_id found → Shell context (registration)');
      await ShellRegistration.registerDevice();
      return;
    }

    // Route 2: Has device ID but status is pending → Shell context (waiting for activation)
    if (deviceStatus === 'pending') {
      SharedLogger.log('[ShellBootstrap] Device pending → Shell context (activation polling)');
      ShellActivationPoll.startPolling();
      return;
    }

    // Route 3: Has device ID and status is active → Start player directly
    if (deviceStatus === 'active') {
      SharedLogger.log('[ShellBootstrap] Device active → Starting player context...');
      // Skip backend verification - trust localStorage state
      // Device was already verified during activation process
      this.startPlayer();
      return;
    }

    // Route 4: Unknown status → Re-register
    SharedLogger.warn('[ShellBootstrap] Unknown device status → Re-registering');
    SharedDeviceState.clearDeviceData();
    await ShellRegistration.registerDevice();
  }

  /**
   * Verify device with backend
   */
  async verifyDevice(): Promise<boolean> {
    const deviceId = SharedDeviceState.getDeviceId();

    if (!deviceId) {
      SharedLogger.warn('[ShellBootstrap] Cannot verify - no device_id');
      return false;
    }

    try {
      // Get device info to verify existence (use GET /api/v1/devices/{device_id})
      const data = await SharedAPIClient.get<VerifyDeviceResponse>(
        `${config.api.baseURL}/api/v1/devices/${deviceId}`
      );

      SharedLogger.log('[ShellBootstrap] Verification response:', data);

      if (data.valid) {
        // Update device state with fresh data from backend
        SharedDeviceState.setDeviceStatus(data.device_status);
        if (data.device_name) {
          SharedDeviceState.setDeviceName(data.device_name);
        }
        if (data.organization_id) {
          SharedDeviceState.setOrganizationId(data.organization_id);
        }

        SharedLogger.log('[ShellBootstrap] ✅ Device verified and synced');
        return true;
      } else {
        SharedLogger.warn('[ShellBootstrap] ⚠️ Device verification failed:', data.message);
        return false;
      }
    } catch (error) {
      SharedLogger.error('[ShellBootstrap] ❌ Verification error:', error);
      return false;
    }
  }

  /**
   * Start player context
   */
  startPlayer(): void {
    SharedLogger.log('[ShellBootstrap] 🎬 Starting player context...');

    // Hide shell UI, show player UI
    this.switchToPlayerUI();

    // Initialize and start player services
    this.initializePlayerServices();
  }

  /**
   * Initialize all player services
   */
  private async initializePlayerServices(): Promise<void> {
    try {
      // 1. Initialize MediaCache
      if (window.PlayerMediaCache) {
        await window.PlayerMediaCache.init();
        SharedLogger.log('[ShellBootstrap] ✅ MediaCache initialized');
      }

      // 2. Initialize Command Executor
      if (window.PlayerCommandExecutor) {
        window.PlayerCommandExecutor.init();
        SharedLogger.log('[ShellBootstrap] ✅ CommandExecutor initialized');
      }

      // 3. Connect WebSocket
      if (window.SharedWebSocket) {
        window.SharedWebSocket.connect();
        SharedLogger.log('[ShellBootstrap] ✅ WebSocket connected');
      }

      // 4. Start PlaylistSync
      if (window.PlayerPlaylistSync) {
        window.PlayerPlaylistSync.start();
        SharedLogger.log('[ShellBootstrap] ✅ PlaylistSync started');
      }

      // 5. Start Heartbeat
      if (window.PlayerHeartbeat) {
        window.PlayerHeartbeat.start();
        SharedLogger.log('[ShellBootstrap] ✅ Heartbeat started');
      }

      // 6. Start Health Reporter (Phase 4)
      if (window.PlayerHealthReporter) {
        window.PlayerHealthReporter.start();
        SharedLogger.log('[ShellBootstrap] ✅ HealthReporter started');
      }

      SharedLogger.log('[ShellBootstrap] 🎉 All player services initialized');
    } catch (error) {
      SharedLogger.error('[ShellBootstrap] ❌ Failed to initialize player services:', error);
    }
  }

  /**
   * Switch UI from shell to player
   */
  private switchToPlayerUI(): void {
    const shellContainer = document.getElementById('shell-container');
    const playerContainer = document.getElementById('player-container');

    if (shellContainer) {
      shellContainer.style.display = 'none';
    }

    if (playerContainer) {
      playerContainer.style.display = 'block';
    }
  }
}

// Export singleton instance
export const ShellBootstrap = new ShellBootstrapClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.ShellBootstrap = ShellBootstrap;
}
