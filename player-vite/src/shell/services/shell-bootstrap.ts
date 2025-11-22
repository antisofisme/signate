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
import { serviceActionAsync, serviceAction } from '@shared/utils';
import { ShellRegistration } from './shell-registration';
import { ShellActivationPoll } from './shell-activation-poll';
import type { ShellBootstrap as IShellBootstrap, VerifyDeviceResponse } from '@shell/types/shell.types';
import { ServiceRegistry, getPlayerHLSCache } from '@shared/services/service-registry';
import { getPlayerMediaCache, getPlayerHeartbeat, getPlayerPlaylistSync, getPlayerCommandExecutor, getPlayerHealthReporter, getSharedWebSocket, getDeviceInfoPopup, getPlayerVideoJS } from '@shared/services';
// Import PlayerVideoJS and PlayerBackgroundAudio to ensure they're registered before use
import '@player/services/player-videojs';
import { PlayerBackgroundAudio } from '@player/services';

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
   * Verify device by fingerprint (for cache clear scenario)
   * Check if device with this fingerprint already exists and is activated
   */
  async verifyDeviceByFingerprint(): Promise<boolean> {
    try {
      // Import fingerprint utility
      const { getOrCreateDeviceUUID } = await import('@shared/utils/device-fingerprint');
      const deviceUUID = getOrCreateDeviceUUID();

      SharedLogger.log('[ShellBootstrap] Device UUID (fingerprint):', deviceUUID);

      // Check backend for device with this UUID
      const response = await SharedAPIClient.get<any>(
        `${config.api.baseURL}/api/v1/devices/verify-fingerprint/${deviceUUID}`
      );

      SharedLogger.log('[ShellBootstrap] Fingerprint verification response:', response);

      if (response.device && response.device.status === 'active') {
        SharedLogger.log('[ShellBootstrap] ✅ Found activated device from fingerprint');

        // Restore device state to localStorage
        SharedDeviceState.setDeviceId(response.device.id);
        SharedDeviceState.setDeviceCode(response.device.unique_code);
        SharedDeviceState.setDeviceStatus(response.device.status);
        SharedDeviceState.setDeviceName(response.device.device_name);
        SharedDeviceState.setOrganizationId(response.device.organization_id);

        if (response.device.organization_pin) {
          SharedDeviceState.setOrganizationPin(response.device.organization_pin);
        }

        if (response.token) {
          SharedDeviceState.setDeviceToken(response.token);
        }

        SharedLogger.log('[ShellBootstrap] ✅ Device state restored from backend');
        return true;
      }

      SharedLogger.log('[ShellBootstrap] No activated device found with this fingerprint');
      return false;
    } catch (error) {
      SharedLogger.warn('[ShellBootstrap] ⚠️ Fingerprint verification failed:', error);
      return false;
    }
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
   * Stop all player services
   */
  private stopPlayerServices(): void {
    try {
      SharedLogger.log('[ShellBootstrap] 🛑 Stopping player services...');

      // Stop services in reverse order
      if (getPlayerHealthReporter()?.stop) {
        getPlayerHealthReporter()?.stop();
        SharedLogger.log('[ShellBootstrap] ✅ HealthReporter stopped');
      }

      if (getPlayerHeartbeat()?.stop) {
        getPlayerHeartbeat()?.stop();
        SharedLogger.log('[ShellBootstrap] ✅ Heartbeat stopped');
      }

      if (getPlayerPlaylistSync()?.stop) {
        getPlayerPlaylistSync()?.stop();
        SharedLogger.log('[ShellBootstrap] ✅ PlaylistSync stopped');
      }

      if (getSharedWebSocket()?.disconnect) {
        getSharedWebSocket()?.disconnect();
        SharedLogger.log('[ShellBootstrap] ✅ WebSocket disconnected');
      }

      // Note: PlayerCommandExecutor doesn't have a destroy() method
      SharedLogger.log('[ShellBootstrap] ✅ CommandExecutor stopped (no destroy needed)');

      // Clear video element
      const videoElement = document.getElementById('player-video') as HTMLVideoElement;
      if (videoElement) {
        videoElement.pause();
        videoElement.src = '';
        videoElement.load();
        SharedLogger.log('[ShellBootstrap] ✅ Video element cleared');
      }

      SharedLogger.log('[ShellBootstrap] 🛑 All player services stopped');
    } catch (error) {
      SharedLogger.error('[ShellBootstrap] ❌ Failed to stop player services:', error);
    }
  }

  /**
   * Initialize all player services
   */
  private async initializePlayerServices(): Promise<void> {
    try {
      // 1. Initialize PlayerVideoJS with video element
      const videoElement = document.getElementById('player-video') as HTMLVideoElement;
      if (videoElement && getPlayerVideoJS()) {
        getPlayerVideoJS()?.init(videoElement);
        SharedLogger.log('[ShellBootstrap] ✅ PlayerVideoJS initialized with video element');
      } else {
        SharedLogger.error('[ShellBootstrap] ❌ Failed to initialize PlayerVideoJS - video element or service not found');
      }

      // 2. Initialize MediaCache
      await serviceActionAsync(
        getPlayerMediaCache,
        async (service) => {
          await service.init();
          SharedLogger.log('[ShellBootstrap] ✅ MediaCache initialized');
        },
        'PlayerMediaCache'
      );

      // 2.5. Initialize Background Audio Player
      PlayerBackgroundAudio.init();
      SharedLogger.log('[ShellBootstrap] ✅ PlayerBackgroundAudio initialized');

      // 3. Initialize HLS Cache
      const PlayerHLSCache = getPlayerHLSCache();
      if (PlayerHLSCache) {
        await PlayerHLSCache.init();
        SharedLogger.log('[ShellBootstrap] ✅ HLS Cache initialized');
      }

      // 4. Register HLS Service Worker for offline playback (HTTPS only)
      if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
        try {
          const registration = await navigator.serviceWorker.register('/hls-service-worker.js', {
            scope: '/',
          });
          SharedLogger.log('[ShellBootstrap] ✅ HLS Service Worker registered:', registration.scope);

          // Wait for Service Worker to activate
          if (registration.active) {
            SharedLogger.log('[ShellBootstrap] Service Worker already active');
          } else {
            SharedLogger.log('[ShellBootstrap] Waiting for Service Worker to activate...');
            await new Promise<void>((resolve) => {
              const checkState = () => {
                if (registration.active) {
                  SharedLogger.log('[ShellBootstrap] Service Worker activated');
                  resolve();
                } else {
                  setTimeout(checkState, 100);
                }
              };
              checkState();
            });
          }
        } catch (error) {
          SharedLogger.error('[ShellBootstrap] ❌ Failed to register Service Worker:', error);
        }
      } else if (window.location.protocol === 'http:') {
        // Running on HTTP - Service Worker not available, but system still works
        SharedLogger.log('[ShellBootstrap] ℹ️ Running on HTTP - Service Worker disabled');
        SharedLogger.log('[ShellBootstrap] HLS streaming and caching enabled, offline playback requires HTTPS');
      } else {
        SharedLogger.log('[ShellBootstrap] ℹ️ Service Worker not supported in this browser');
        SharedLogger.log('[ShellBootstrap] HLS caching enabled, offline playback limited');
      }

      // 5-7. Connection logging services already initialized in main.ts
      // (ConnectionLogger, NetworkSpeedTest, ConnectionLogPopup)

      // 6. Initialize Command Executor
      serviceAction(
        getPlayerCommandExecutor,
        (service) => {
          service.init();
          SharedLogger.log('[ShellBootstrap] ✅ CommandExecutor initialized');
        },
        'PlayerCommandExecutor'
      );

      // 7. Connect WebSocket
      serviceAction(
        getSharedWebSocket,
        (service) => {
          service.connect();
          SharedLogger.log('[ShellBootstrap] ✅ WebSocket connected');
        },
        'SharedWebSocket'
      );

      // 8. Start PlaylistSync
      serviceAction(
        getPlayerPlaylistSync,
        (service) => {
          service.start();
          SharedLogger.log('[ShellBootstrap] ✅ PlaylistSync started');
        },
        'PlayerPlaylistSync'
      );

      // 9. Start Heartbeat
      serviceAction(
        getPlayerHeartbeat,
        (service) => {
          service.start();
          SharedLogger.log('[ShellBootstrap] ✅ Heartbeat started');
        },
        'PlayerHeartbeat'
      );

      // 10. Start Health Reporter (Phase 4)
      serviceAction(
        getPlayerHealthReporter,
        (service) => {
          service.start();
          SharedLogger.log('[ShellBootstrap] ✅ HealthReporter started');
        },
        'PlayerHealthReporter'
      );

      // 11. Initialize Device Info Popup
      serviceAction(
        getDeviceInfoPopup,
        (service) => {
          service.init();
          SharedLogger.log('[ShellBootstrap] ✅ DeviceInfoPopup initialized');
        },
        'DeviceInfoPopup'
      );

      // Note: Rotation is now applied via PlayerPlaylistSync when device_settings are received
      // This ensures rotation is synced together with other device settings (volume, background audio)

      SharedLogger.log('[ShellBootstrap] 🎉 All player services initialized');
    } catch (error) {
      SharedLogger.error('[ShellBootstrap] ❌ Failed to initialize player services:', error);
    }
  }

  /**
   * Reload player services without reloading shell
   * Used for cache clear, playlist refresh, etc.
   */
  async reloadPlayerServices(): Promise<void> {
    SharedLogger.log('[ShellBootstrap] 🔄 Reloading player services...');

    try {
      // 1. Stop all player services
      this.stopPlayerServices();

      // 2. Wait a bit for cleanup
      await new Promise(resolve => setTimeout(resolve, 500));

      // 3. Re-initialize player services
      await this.initializePlayerServices();

      SharedLogger.log('[ShellBootstrap] ✅ Player services reloaded successfully');
    } catch (error) {
      SharedLogger.error('[ShellBootstrap] ❌ Failed to reload player services:', error);
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
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellBootstrap', ShellBootstrap);
}
