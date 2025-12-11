/**
 * Player Heartbeat Service
 * Sends periodic heartbeat to backend to report device online status
 *
 * @features
 * - Periodic heartbeat every 30 seconds
 * - Reports current playback state
 * - Optimized payload (static data sent via /capabilities)
 * - Viewport change detection (only sends when changed)
 * - Connection drops tracking
 * - Handles heartbeat failures gracefully
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { deviceConfigStorage } from '@shared/storage';
import type { Heartbeat as IHeartbeat } from '@player/types/player.types';
import { ServiceRegistry } from '@shared/services/service-registry';
import { getCachedLocalIP } from '@shared/utils/device-fingerprint';

/**
 * Player Heartbeat Class
 * Singleton pattern for heartbeat management
 */
class PlayerHeartbeatClass implements IHeartbeat {
  private heartbeatInterval: number | null = null;
  private running = false;
  private consecutiveFailures = 0;
  private readonly maxConsecutiveFailures = 5;

  // Viewport change detection
  private lastViewportWidth: number | null = null;
  private lastViewportHeight: number | null = null;

  // Connection drops tracking
  private connectionDropsCount = 0;
  private isOnline = true;
  private onlineListener: (() => void) | null = null;
  private offlineListener: (() => void) | null = null;

  /**
   * Start periodic heartbeat
   */
  start(): void {
    if (this.running) {
      SharedLogger.warn('[PlayerHeartbeat] Already running');
      return;
    }

    const deviceId = SharedDeviceState.getDeviceId();
    if (!deviceId) {
      SharedLogger.error('[PlayerHeartbeat] Cannot start - no device_id');
      return;
    }

    SharedLogger.log('[PlayerHeartbeat] 💓 Starting heartbeat...');
    this.running = true;
    this.consecutiveFailures = 0;

    // Initialize viewport tracking
    this.lastViewportWidth = window.innerWidth;
    this.lastViewportHeight = window.innerHeight;

    // Initialize connection drops tracking
    this.isOnline = navigator.onLine;
    this.setupConnectionTracking();

    // Send immediately
    void this.sendHeartbeat();

    // Then send periodically
    this.heartbeatInterval = window.setInterval(() => {
      void this.sendHeartbeat();
    }, config.device.heartbeatInterval);
  }

  /**
   * Setup connection online/offline tracking
   */
  private setupConnectionTracking(): void {
    // Remove existing listeners if any
    this.removeConnectionTracking();

    this.offlineListener = () => {
      if (this.isOnline) {
        this.connectionDropsCount++;
        this.isOnline = false;
        SharedLogger.warn(`[PlayerHeartbeat] 📴 Connection dropped (total: ${this.connectionDropsCount})`);
      }
    };

    this.onlineListener = () => {
      if (!this.isOnline) {
        this.isOnline = true;
        SharedLogger.log('[PlayerHeartbeat] 📶 Connection restored');
      }
    };

    window.addEventListener('offline', this.offlineListener);
    window.addEventListener('online', this.onlineListener);
  }

  /**
   * Remove connection tracking listeners
   */
  private removeConnectionTracking(): void {
    if (this.offlineListener) {
      window.removeEventListener('offline', this.offlineListener);
      this.offlineListener = null;
    }
    if (this.onlineListener) {
      window.removeEventListener('online', this.onlineListener);
      this.onlineListener = null;
    }
  }

  /**
   * Stop periodic heartbeat
   */
  stop(): void {
    if (!this.running) {
      return;
    }

    if (this.heartbeatInterval !== null) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // Remove connection tracking listeners
    this.removeConnectionTracking();

    this.running = false;
    this.consecutiveFailures = 0;
    SharedLogger.log('[PlayerHeartbeat] ⏹️ Heartbeat stopped');
  }

  /**
   * Send heartbeat to backend
   *
   * OPTIMIZED PAYLOAD (Phase 2):
   * - Static fields (screen, user_agent, pixel_ratio) now sent via /capabilities endpoint
   * - Viewport only included when changed from last heartbeat
   * - Added connection_drops_count tracking
   */
  async sendHeartbeat(): Promise<void> {
    const deviceId = SharedDeviceState.getDeviceId();

    if (!deviceId) {
      SharedLogger.error('[PlayerHeartbeat] Cannot send heartbeat - no device_id');
      this.stop();
      return;
    }

    try {
      // Get unique_code from localStorage (simpler and more reliable)
      const uniqueCode = SharedDeviceState.getDeviceCode();

      if (!uniqueCode) {
        SharedLogger.error('[PlayerHeartbeat] Cannot send heartbeat - no unique_code');
        return;
      }

      // Check if viewport changed
      const currentViewportWidth = window.innerWidth;
      const currentViewportHeight = window.innerHeight;
      const viewportChanged =
        this.lastViewportWidth !== currentViewportWidth ||
        this.lastViewportHeight !== currentViewportHeight;

      // Prepare OPTIMIZED heartbeat payload
      // Static fields (screen_width, screen_height, device_pixel_ratio, user_agent)
      // are now sent ONCE via /capabilities endpoint on startup
      const payload: Record<string, any> = {
        // Required identification
        unique_code: uniqueCode,
        device_uuid: '', // WebOS device UUID if available

        // Dynamic connection data (changes frequently)
        connection_type: (navigator as any).connection?.effectiveType || null,
        connection_speed: (navigator as any).connection?.downlink || null,

        // Connection reliability tracking
        connection_drops_count: this.connectionDropsCount,

        // Local IP address for device identification (from WebRTC)
        local_ip: getCachedLocalIP() || null,
      };

      // Only include viewport if changed (semi-static data)
      if (viewportChanged) {
        payload.viewport_width = currentViewportWidth;
        payload.viewport_height = currentViewportHeight;

        // Update last known viewport
        this.lastViewportWidth = currentViewportWidth;
        this.lastViewportHeight = currentViewportHeight;

        SharedLogger.log('[PlayerHeartbeat] 📐 Viewport changed, including in payload', {
          width: currentViewportWidth,
          height: currentViewportHeight,
        });
      }

      SharedLogger.log('[PlayerHeartbeat] 💓 Sending heartbeat...', {
        deviceId,
        connectionDrops: this.connectionDropsCount,
        viewportChanged,
      });

      // Send heartbeat using correct endpoint
      await SharedAPIClient.post(
        `${config.api.baseURL}/api/v1/devices/${deviceId}/heartbeat`,
        payload
      );

      // Reset failure counter on success
      this.consecutiveFailures = 0;

      SharedLogger.log('[PlayerHeartbeat] ✅ Heartbeat sent successfully');
    } catch (error: any) {
      const status = error?.response?.status || error?.status;

      // Check if device has been hard-deleted (404 error)
      if (status === 404) {
        SharedLogger.warn('[PlayerHeartbeat] 🔴 Device hard-deleted (404) - Full reset and re-register');
        this.stop();
        await this.handleDeviceHardDeleted();
        return;
      }

      // Check if device has been released (403 error)
      if (status === 403) {
        SharedLogger.warn('[PlayerHeartbeat] ⚠️ Device has been released (403) - Triggering re-registration');
        this.stop();
        await this.handleDeviceReleased();
        return;
      }

      this.consecutiveFailures++;

      SharedLogger.error('[PlayerHeartbeat] ❌ Heartbeat failed:', error, {
        consecutiveFailures: this.consecutiveFailures,
        maxFailures: this.maxConsecutiveFailures,
      });

      // Stop heartbeat if too many consecutive failures
      if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
        SharedLogger.error(
          `[PlayerHeartbeat] ⛔ Max consecutive failures (${this.maxConsecutiveFailures}) reached - Stopping heartbeat`
        );
        this.stop();

        // Optionally trigger reconnection logic
        this.handleConnectionLost();
      }
    }
  }

  /**
   * Check if heartbeat is running
   */
  isRunning(): boolean {
    return this.running;
  }

  /**
   * Handle device released by CMS admin (soft release)
   * Triggered when heartbeat returns 403
   *
   * Flow:
   * 1. Clear tokens but KEEP org_id
   * 2. Clear media cache
   * 3. Reload to trigger re-registration
   * 4. Device will request code WITH org_id
   * 5. Device appears in SAME organization's pending list
   */
  private async handleDeviceReleased(): Promise<void> {
    try {
      SharedLogger.log('[PlayerHeartbeat] 🔄 Handling device release (CMS admin)...');

      // Clear tokens but keep org_id (soft release)
      await deviceConfigStorage.clearTokens();

      SharedLogger.log('[PlayerHeartbeat] ✅ Tokens cleared, org_id preserved');

      // Emit event via SharedEventBus
      SharedEventBus.emit('device:released', {
        timestamp: new Date().toISOString(),
        releaseType: 'cms_release',
      });

      // Reload to show activation screen
      // Device will request new code WITH org_id parameter
      SharedLogger.log('[PlayerHeartbeat] 🔄 Reloading to trigger re-registration...');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      SharedLogger.error('[PlayerHeartbeat] ❌ Failed to handle device released:', error);
    }
  }

  /**
   * Handle device hard-deleted by CMS admin (from Unsigned Pool)
   * Triggered when heartbeat returns 404
   *
   * Flow:
   * 1. Clear ALL data including org_id
   * 2. Clear media cache
   * 3. Reload to trigger re-registration
   * 4. Device will request code WITHOUT org_id
   * 5. Device appears in GLOBAL pending list
   */
  private async handleDeviceHardDeleted(): Promise<void> {
    try {
      SharedLogger.log('[PlayerHeartbeat] 🔴 Handling device hard delete...');

      // Clear ALL data including org_id (hard reset)
      await deviceConfigStorage.hardReset();

      SharedLogger.log('[PlayerHeartbeat] ✅ All data cleared (hard reset)');

      // Also clear localStorage
      localStorage.clear();

      // Emit event via SharedEventBus
      SharedEventBus.emit('device:hardDeleted', {
        timestamp: new Date().toISOString(),
        releaseType: 'hard_delete',
      });

      // Reload to show activation screen
      // Device will request new code WITHOUT org_id parameter (global pending)
      SharedLogger.log('[PlayerHeartbeat] 🔄 Reloading for global re-registration...');
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      SharedLogger.error('[PlayerHeartbeat] ❌ Failed to handle device hard delete:', error);
    }
  }

  /**
   * Handle connection lost
   * Triggered after max consecutive heartbeat failures
   */
  private handleConnectionLost(): void {
    SharedLogger.warn('[PlayerHeartbeat] ⚠️ Connection lost - Attempting recovery...');

    // Emit event via SharedEventBus
    SharedEventBus.emit('connection:lost', {
      consecutiveFailures: this.consecutiveFailures,
      timestamp: new Date().toISOString(),
    });

    // Optionally attempt to restart heartbeat after delay
    setTimeout(() => {
      if (!this.running) {
        SharedLogger.log('[PlayerHeartbeat] 🔄 Attempting to restart heartbeat...');
        this.start();
      }
    }, 30000); // Retry after 30 seconds
  }

  /**
   * Get heartbeat status
   */
  getStatus() {
    return {
      running: this.running,
      consecutiveFailures: this.consecutiveFailures,
      maxFailures: this.maxConsecutiveFailures,
      connectionDropsCount: this.connectionDropsCount,
      isOnline: this.isOnline,
    };
  }

  /**
   * Get connection drops count
   */
  getConnectionDropsCount(): number {
    return this.connectionDropsCount;
  }

  /**
   * Reset connection drops count (e.g., on device restart)
   */
  resetConnectionDropsCount(): void {
    this.connectionDropsCount = 0;
    SharedLogger.log('[PlayerHeartbeat] Connection drops count reset');
  }

  /**
   * Force send heartbeat immediately (manual trigger)
   */
  async sendNow(): Promise<void> {
    await this.sendHeartbeat();
  }
}

// Export singleton instance
export const PlayerHeartbeat = new PlayerHeartbeatClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('PlayerHeartbeat', PlayerHeartbeat);
}
