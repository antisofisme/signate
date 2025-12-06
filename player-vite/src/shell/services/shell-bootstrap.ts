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
import { getPlayerMediaCache, getPlayerHeartbeat, getPlayerPlaylistSync, getPlayerCommandExecutor, getPlayerHealthReporter, getPlayerCapabilitiesReporter, getSharedWebSocket, getDeviceInfoPopup, getPlayerVideoJS, getPlayerBackgroundAudio } from '@shared/services';
import { registerPWA, getPWAState } from '@pwa/pwa-registration';
// Side-effect imports to ensure services are registered before use
import '@player/services/player-videojs';
import '@player/services/player-background-audio';
import '@player/services/player-health-reporter';
import '@player/services/player-capabilities-reporter'; // Report device capabilities on startup
import '@player/services/player-command-executor'; // Loads SharedWebSocket as dependency
import '@shared/websocket/shared-websocket'; // Ensure WebSocket is registered before any getSharedWebSocket() calls

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

      // Always refresh token on startup to ensure WebSocket can connect
      // This handles: missing token, expired token, or invalid token
      SharedLogger.log('[ShellBootstrap] 🔄 Refreshing device token on startup...');
      await this.refreshDeviceToken();

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
   * Refresh device token from server
   * Used when device is active but missing token (activated before token feature)
   * Uses device fingerprint UUID to get token (always available, unlike device_code)
   *
   * Handles device lifecycle:
   * - 404: Device hard-deleted from backend → full reset and re-register
   * - 403: Device soft-released from backend → keep org_id, re-register to same org
   */
  private async refreshDeviceToken(): Promise<void> {
    try {
      // Use fingerprint-based verification which always works
      // (device_code might not be in localStorage for old devices)
      const { getOrCreateDeviceUUID } = await import('@shared/utils/device-fingerprint');
      const deviceUUID = getOrCreateDeviceUUID();

      SharedLogger.log('[ShellBootstrap] Refreshing token via fingerprint:', deviceUUID);

      // Call verify-fingerprint API which returns device_token
      const response = await SharedAPIClient.get<any>(
        `${config.api.baseURL}/api/v1/devices/verify-fingerprint/${deviceUUID}`
      );

      if (response.device && response.token) {
        SharedDeviceState.setDeviceToken(response.token);
        SharedLogger.log('[ShellBootstrap] ✅ Device token refreshed successfully');

        // Also restore device_code if missing (for future use)
        if (response.device.unique_code && !SharedDeviceState.getDeviceCode()) {
          SharedDeviceState.setDeviceCode(response.device.unique_code);
          SharedLogger.log('[ShellBootstrap] ✅ Device code also restored');
        }

        // Update organization PIN if available
        if (response.device.organization_pin) {
          SharedDeviceState.setOrganizationPin(response.device.organization_pin);
        }
      } else {
        SharedLogger.warn('[ShellBootstrap] ⚠️ Token refresh failed - no device or token in response');
        // Device not found in backend - likely deleted
        await this.handleDeviceNotFoundOnRefresh();
      }
    } catch (error: any) {
      const status = error?.response?.status || error?.status;
      SharedLogger.error('[ShellBootstrap] ❌ Failed to refresh device token:', error);

      if (status === 404) {
        // Device hard-deleted from backend → full reset and re-register
        SharedLogger.warn('[ShellBootstrap] 🔴 Device 404 - hard deleted from backend');
        await this.handleDeviceHardDeleted();
        return;
      }

      if (status === 403) {
        // Device soft-released from backend → keep org_id, re-register to same org
        SharedLogger.warn('[ShellBootstrap] 🟡 Device 403 - soft released from backend');
        await this.handleDeviceSoftReleased();
        return;
      }

      // Other errors - don't block player startup, WebSocket just won't connect
    }
  }

  /**
   * Handle device not found during token refresh (device likely deleted)
   */
  private async handleDeviceNotFoundOnRefresh(): Promise<void> {
    SharedLogger.warn('[ShellBootstrap] Device not found during token refresh, triggering re-registration');
    await this.handleDeviceHardDeleted();
  }

  /**
   * Handle device hard deleted (404)
   * Clear ALL data including org_id, re-register to global pending
   */
  private async handleDeviceHardDeleted(): Promise<void> {
    const { deviceConfigStorage } = await import('@shared/storage/device-config-storage');

    SharedLogger.warn('[ShellBootstrap] 🔴 Handling hard delete - clearing ALL data');

    // Clear ALL data including organization_id
    await deviceConfigStorage.hardReset();

    // Also clear localStorage device state
    SharedDeviceState.clearDeviceData();

    // Clear any remaining localStorage items
    localStorage.clear();

    SharedLogger.log('[ShellBootstrap] ✅ All data cleared, reloading for re-registration...');

    // Reload to trigger fresh registration (to global pending)
    location.reload();
  }

  /**
   * Handle device soft released (403)
   * Clear tokens but KEEP org_id, re-register to same organization
   */
  private async handleDeviceSoftReleased(): Promise<void> {
    const { deviceConfigStorage } = await import('@shared/storage/device-config-storage');

    SharedLogger.warn('[ShellBootstrap] 🟡 Handling soft release - keeping org_id');

    // Clear tokens but keep organization_id
    await deviceConfigStorage.clearTokens();

    // Clear localStorage device state (but org_id is in IndexedDB, preserved)
    SharedDeviceState.clearDeviceData();

    SharedLogger.log('[ShellBootstrap] ✅ Tokens cleared, org_id preserved, reloading for re-registration...');

    // Reload to trigger fresh registration (to same organization)
    location.reload();
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

      // Stop PlayerVideoJS (revokes blob URLs to prevent memory leaks)
      if (getPlayerVideoJS()?.stop) {
        getPlayerVideoJS()?.stop();
        SharedLogger.log('[ShellBootstrap] ✅ PlayerVideoJS stopped');
      }

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

      // 2.5. Initialize Background Audio Player (via ServiceRegistry to maintain Shell-Player separation)
      const PlayerBackgroundAudio = getPlayerBackgroundAudio();
      if (PlayerBackgroundAudio) {
        PlayerBackgroundAudio.init();
        SharedLogger.log('[ShellBootstrap] ✅ PlayerBackgroundAudio initialized');
      }

      // 3. Initialize HLS Cache
      const PlayerHLSCache = getPlayerHLSCache();
      if (PlayerHLSCache) {
        await PlayerHLSCache.init();
        SharedLogger.log('[ShellBootstrap] ✅ HLS Cache initialized');
      }

      // 4. Register PWA Service Worker for offline app shell and HLS playback
      // PWA SW handles app shell caching (index.html, JS, CSS) and passes HLS requests through
      // to the existing IndexedDB caching in player-hls-cache.ts
      if ('serviceWorker' in navigator) {
        try {
          const deviceId = SharedDeviceState.getDeviceId() || undefined;
          const pwaRegistered = await registerPWA(deviceId);

          if (pwaRegistered) {
            SharedLogger.log('[ShellBootstrap] ✅ PWA Service Worker registered');
            SharedLogger.log('[ShellBootstrap] PWA State:', getPWAState());
          } else {
            SharedLogger.log('[ShellBootstrap] ℹ️ PWA not registered (disabled or unsupported)');
          }
        } catch (error) {
          SharedLogger.error('[ShellBootstrap] ❌ Failed to register PWA Service Worker:', error);
        }
      } else {
        SharedLogger.log('[ShellBootstrap] ℹ️ Service Worker not supported in this browser');
        SharedLogger.log('[ShellBootstrap] Offline reload capability limited');
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

      // 11. Report Device Capabilities (sent ONCE on startup)
      await serviceActionAsync(
        getPlayerCapabilitiesReporter,
        async (service) => {
          await service.report();
          SharedLogger.log('[ShellBootstrap] ✅ CapabilitiesReporter reported');
        },
        'PlayerCapabilitiesReporter'
      );

      // 12. Initialize Device Info Popup
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
