/**
 * Shell Activation Poll Service
 * Polls backend to check if pending activation code has been activated
 *
 * @features
 * - Automatic polling every 5 seconds
 * - Handles code expiration with auto-reset
 * - Manages device ID transitions
 * - Type-safe with TypeScript
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';
import { SharedDeviceState } from '@shared/device';
import type { ShellActivationPoll as IShellActivationPoll, ActivationCheckResponse } from '../types/shell.types';

/**
 * Shell Activation Poll Class
 * Singleton pattern for activation polling
 */
class ShellActivationPollClass implements IShellActivationPoll {
  private pollInterval: number | null = null;
  private readonly pollIntervalMs = 5000; // Check every 5 seconds

  /**
   * Start polling for activation status
   */
  startPolling(): void {
    // Get activation code
    const activationCode = SharedDeviceState.getDeviceCode();

    // Only poll if we have activation code but device is not activated yet
    if (!activationCode || SharedDeviceState.isActivated()) {
      SharedLogger.log('[ShellActivationPoll] Skipping poll - no code or already activated');
      return;
    }

    SharedLogger.log(`[ShellActivationPoll] 🔄 Starting activation polling for code: ${activationCode}`);

    // Clear existing interval if any
    this.stopPolling();

    // Check immediately
    void this.checkActivation();

    // Then check every 5 seconds
    this.pollInterval = window.setInterval(() => {
      void this.checkActivation();
    }, this.pollIntervalMs);
  }

  /**
   * Stop polling
   */
  stopPolling(): void {
    if (this.pollInterval !== null) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
      SharedLogger.log('[ShellActivationPoll] ⏹️ Stopped activation polling');
    }
  }

  /**
   * Check if activation code has been activated
   */
  async checkActivation(): Promise<void> {
    const activationCode = SharedDeviceState.getDeviceCode();

    if (!activationCode) {
      this.stopPolling();
      return;
    }

    try {
      // Check activation status
      const data = await SharedAPIClient.get<ActivationCheckResponse>(
        `${config.api.baseURL}/api/v1/devices/check-activation/${activationCode}`
      );

      SharedLogger.log('[ShellActivationPoll] 📊 Activation status:', data);

      // Handle expired code - clear localStorage and re-register
      if (data.expired) {
        SharedLogger.warn('[ShellActivationPoll] ⚠️ Activation code expired - Auto-resetting viewer');

        // Stop polling
        this.stopPolling();

        // Clear device data (preserve auth)
        SharedDeviceState.clearDeviceData({ preserveAuth: true });

        // Delete IndexedDB cache
        await this.clearMediaCache();

        // Verify device data was cleared
        const deviceIdAfterClear = SharedDeviceState.getDeviceId();
        if (deviceIdAfterClear) {
          SharedLogger.error(
            '[ShellActivationPoll] CRITICAL: device_id still exists after clear!',
            deviceIdAfterClear
          );
          // Force removal
          SharedDeviceState.clearDeviceData({ preserveAuth: true });
        }

        // Re-register device
        SharedLogger.log('[ShellActivationPoll] 🔄 Re-registering device with preserved token & org_id...');
        if (window.ShellRegistration) {
          await window.ShellRegistration.registerDevice();
        }
        return;
      }

      // Handle activation success
      if (data.activated && data.device_id) {
        SharedLogger.log(
          `[ShellActivationPoll] ✅ Code activated! Device ID: ${data.device_id}, Name: ${data.device_name}`
        );

        // Handle device ID change (replace scenario)
        const oldDeviceId = SharedDeviceState.getDeviceId();
        const newDeviceId = data.device_id;

        if (oldDeviceId && oldDeviceId !== String(newDeviceId)) {
          SharedLogger.warn(
            `[ShellActivationPoll] ⚠️ Device ID changed: ${oldDeviceId} → ${newDeviceId} (Replace scenario)`
          );
        }

        // Stop polling
        this.stopPolling();

        // Stop old heartbeat (if running) and wait for pending requests
        if (window.ShellHeartbeat?.stop) {
          window.ShellHeartbeat.stop();
          SharedLogger.log('[ShellActivationPoll] Stopped old heartbeat, waiting for pending requests...');
          await new Promise((resolve) => setTimeout(resolve, 200));
        }

        // Delete old device cache (force reload)
        await this.clearMediaCache();

        // Mark device as activated using atomic operation
        SharedDeviceState.markAsActivated(
          newDeviceId,
          data.device_name || null,
          data.organization_id || null
        );

        // Save organization PIN for hard reset (if provided)
        if (data.organization_pin) {
          SharedDeviceState.setOrganizationPin(data.organization_pin);
          SharedLogger.log(`[ShellActivationPoll] Organization PIN saved: ${data.organization_pin}`);
        }

        // Clear pending code
        if (window.ShellRegistration) {
          window.ShellRegistration.setPendingCode(null);
        }

        // Reload to player context
        SharedLogger.log('[ShellActivationPoll] 🔄 Reloading to player context...');
        window.location.reload();
      }
    } catch (error) {
      SharedLogger.error('[ShellActivationPoll] ❌ Activation check failed:', error);
      // Continue polling - network might be temporarily down
    }
  }

  /**
   * Clear media cache from IndexedDB
   */
  private async clearMediaCache(): Promise<void> {
    const dbName = 'signage_media_cache';
    try {
      await new Promise<void>((resolve) => {
        const deleteRequest = indexedDB.deleteDatabase(dbName);
        deleteRequest.onsuccess = () => resolve();
        deleteRequest.onerror = () => resolve();
        deleteRequest.onblocked = () => resolve();
      });
      SharedLogger.log('[ShellActivationPoll] Media cache cleared');
    } catch (error) {
      SharedLogger.error('[ShellActivationPoll] Error deleting cache:', error);
    }
  }
}

// Export singleton instance
export const ShellActivationPoll = new ShellActivationPollClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.ShellActivationPoll = ShellActivationPoll;
}
