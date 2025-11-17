/**
 * Player Heartbeat Service
 * Sends periodic heartbeat to backend to report device online status
 *
 * @features
 * - Periodic heartbeat every 30 seconds
 * - Reports current playback state
 * - Collects system information
 * - Handles heartbeat failures gracefully
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import { deviceConfigStorage } from '@shared/storage';
import type { Heartbeat as IHeartbeat } from '../types/player.types';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Player Heartbeat Class
 * Singleton pattern for heartbeat management
 */
class PlayerHeartbeatClass implements IHeartbeat {
  private heartbeatInterval: number | null = null;
  private running = false;
  private consecutiveFailures = 0;
  private readonly maxConsecutiveFailures = 5;

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

    // Send immediately
    void this.sendHeartbeat();

    // Then send periodically
    this.heartbeatInterval = window.setInterval(() => {
      void this.sendHeartbeat();
    }, config.device.heartbeatInterval);
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

    this.running = false;
    this.consecutiveFailures = 0;
    SharedLogger.log('[PlayerHeartbeat] ⏹️ Heartbeat stopped');
  }

  /**
   * Send heartbeat to backend
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

      // Prepare heartbeat payload
      const payload = {
        unique_code: uniqueCode,
        device_uuid: '', // WebOS device UUID if available
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        device_pixel_ratio: window.devicePixelRatio,
        user_agent: navigator.userAgent,
        connection_type: (navigator as any).connection?.effectiveType || null,
        connection_speed: (navigator as any).connection?.downlink || null,
      };

      SharedLogger.log('[PlayerHeartbeat] 💓 Sending heartbeat...', {
        deviceId: deviceId,
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
      // Check if device has been released (403 error)
      if (error?.response?.status === 403) {
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

      // Dispatch custom event for UI
      const event = new CustomEvent('device-released', {
        detail: {
          timestamp: new Date().toISOString(),
          releaseType: 'cms_release',
        },
      });
      window.dispatchEvent(event);

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
   * Handle connection lost
   * Triggered after max consecutive heartbeat failures
   */
  private handleConnectionLost(): void {
    SharedLogger.warn('[PlayerHeartbeat] ⚠️ Connection lost - Attempting recovery...');

    // Dispatch custom event for UI to handle
    const event = new CustomEvent('connection-lost', {
      detail: {
        consecutiveFailures: this.consecutiveFailures,
        timestamp: new Date().toISOString(),
      },
    });
    window.dispatchEvent(event);

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
    };
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
