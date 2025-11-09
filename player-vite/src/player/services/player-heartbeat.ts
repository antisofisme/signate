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
import type { Heartbeat as IHeartbeat, HeartbeatPayload, SystemInfo } from '../types/player.types';

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
      // Prepare heartbeat payload
      const payload: HeartbeatPayload = {
        device_id: parseInt(deviceId, 10),
        status: 'online',
        current_content_id: this.getCurrentContentId(),
        system_info: this.collectSystemInfo(),
      };

      SharedLogger.log('[PlayerHeartbeat] 💓 Sending heartbeat...', {
        deviceId: payload.device_id,
        currentContent: payload.current_content_id,
      });

      // Send heartbeat
      await SharedAPIClient.post(
        `${config.api.baseURL}/api/client/heartbeat`,
        payload
      );

      // Reset failure counter on success
      this.consecutiveFailures = 0;

      SharedLogger.log('[PlayerHeartbeat] ✅ Heartbeat sent successfully');
    } catch (error) {
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
   * Get current content ID being played
   */
  private getCurrentContentId(): number | null {
    try {
      // Try to get from global PlayerHLS state
      if (window.PlayerHLS) {
        const currentItem = window.PlayerHLS.getCurrentItem();
        return currentItem?.content_id || null;
      }

      return null;
    } catch (error) {
      SharedLogger.error('[PlayerHeartbeat] Failed to get current content:', error);
      return null;
    }
  }

  /**
   * Collect system information
   */
  private collectSystemInfo(): SystemInfo {
    const platform = SharedDeviceState.getPlatform() || 'Unknown';

    const systemInfo: SystemInfo = {
      platform,
    };

    // Try to collect memory info (if available)
    try {
      if ('memory' in performance && (performance as any).memory) {
        const memory = (performance as any).memory;
        systemInfo.memory_usage = memory.usedJSHeapSize || undefined;
      }
    } catch (error) {
      // Memory info not available
    }

    // Try to collect uptime (time since page load)
    try {
      if ('timing' in performance && performance.timing) {
        const uptime = Date.now() - performance.timing.navigationStart;
        systemInfo.uptime = Math.floor(uptime / 1000); // Convert to seconds
      }
    } catch (error) {
      // Uptime not available
    }

    return systemInfo;
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
  window.PlayerHeartbeat = PlayerHeartbeat;
}
