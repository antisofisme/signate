/**
 * Hard Reset Handler Component
 * Manages device hard reset with password protection and full data clearing
 *
 * @features
 * - Password protected reset
 * - Clear localStorage (all device data)
 * - Clear IndexedDB cache (media cache)
 * - Page reload to complete reset
 */

import { SharedLogger } from '@shared/logger';
import { SharedToast, SharedModal } from '@shared/ui';
import { deviceConfigStorage } from '@shared/storage';
import { SharedAPIClient } from '@shared/api';

/**
 * Hard Reset Handler Manager Class
 * Singleton pattern for hard reset management
 */
class HardResetHandlerManager {
  private static instance: HardResetHandlerManager;
  private isResetting: boolean = false;

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): HardResetHandlerManager {
    if (!HardResetHandlerManager.instance) {
      HardResetHandlerManager.instance = new HardResetHandlerManager();
    }
    return HardResetHandlerManager.instance;
  }

  /**
   * Clear ALL device config and IndexedDB, then reload page
   * Called after backend confirms hard reset
   *
   * Flow (Factory Reset):
   * 1. Clear ALL device config (including org_id)
   * 2. Clear media cache
   * 3. Reload page
   * 4. Device requests code WITHOUT org_id
   * 5. Device appears in GLOBAL pending list
   */
  private async executeReset(): Promise<void> {
    // Set flag to prevent double execution
    this.isResetting = true;
    SharedLogger.log('[HardReset] Backend confirmed, executing hard reset...');

    try {
      // Clear ALL device config (including org_id)
      await deviceConfigStorage.hardReset();
      SharedLogger.log('[HardReset] ✅ Device config cleared (ALL data including org_id)');

      // Clear localStorage for backward compatibility
      localStorage.clear();
      SharedLogger.log('[HardReset] ✅ localStorage cleared');

      // Reload to trigger re-registration WITHOUT org_id
      SharedLogger.log('[HardReset] 🔄 Reloading page to trigger re-registration (global pending)...');
      setTimeout(() => {
        location.replace(location.href);
      }, 500);
    } catch (error) {
      SharedLogger.error('[HardReset] ❌ Failed to clear device config:', error);
      SharedToast.error('Hard reset failed. Please try again.');
      this.isResetting = false;
    }
  }

  /**
   * Validate password via backend API and execute reset if valid
   *
   * Flow:
   * 1. Send password to backend for validation
   * 2. If valid, backend sets status='released'
   * 3. Backend returns success
   * 4. Clear ALL device config (including org_id)
   * 5. Reload → device requests code WITHOUT org_id
   * 6. Device appears in GLOBAL pending list
   */
  private async validatePasswordAndReset(password: string): Promise<void> {
    try {
      // Get device ID
      const deviceConfig = await deviceConfigStorage.getDeviceConfig();
      const deviceId = deviceConfig.device_id;

      if (!deviceId) {
        SharedToast.error('Device not configured. Cannot perform hard reset.');
        SharedLogger.error('[HardReset] No device_id found');
        this.isResetting = false;
        return;
      }

      SharedLogger.log('[HardReset] Validating password with backend...', { deviceId });

      // Step 1: Validate password via backend
      const validation = await SharedAPIClient.post<{ valid: boolean; message: string }>(
        '/api/v1/devices/validate-reset-password',
        {
          password,
          device_id: deviceId,
        }
      );

      if (!validation.valid) {
        SharedToast.error('Incorrect password. Hard reset cancelled.');
        SharedLogger.error('[HardReset] ❌ Password validation failed');
        this.isResetting = false;
        return;
      }

      SharedLogger.log('[HardReset] ✅ Password validated by backend');

      // Step 2: Call backend hard reset endpoint
      await SharedAPIClient.post(`/api/v1/devices/${deviceId}/hard-reset`);
      SharedLogger.log('[HardReset] ✅ Backend hard reset endpoint called');

      // Step 3: Clear ALL local data and reload
      await this.executeReset();
    } catch (error: any) {
      SharedLogger.error('[HardReset] Error during hard reset:', error);

      if (error?.response?.status === 404) {
        SharedToast.error('Device not found. Please contact administrator.');
      } else {
        SharedToast.error('Hard reset failed. Please try again.');
      }

      this.isResetting = false;
    }
  }

  /**
   * Setup hard reset button click handler
   * Prompts for password before executing reset
   */
  private setupResetButton(): void {
    const resetBtn = document.getElementById('factory-reset-btn');

    if (resetBtn) {
      resetBtn.addEventListener('click', async () => {
        // Prevent double-click during reset
        if (this.isResetting) {
          SharedLogger.warn('[HardReset] Hard reset already in progress, ignoring click');
          return;
        }

        SharedLogger.log('[HardReset] Hard reset button clicked');

        // Prompt for password using modal
        let password: string;
        try {
          password = await SharedModal.prompt(
            'Factory Reset Device',
            'This will ERASE ALL DATA and require re-activation. Enter admin password to confirm:'
          );
        } catch (err: any) {
          // User cancelled or didn't enter password
          const errorMsg = err?.message || 'Unknown error';

          if (errorMsg === 'No input provided') {
            SharedToast.warning('Password required for factory reset.');
            SharedLogger.log('[HardReset] Hard reset cancelled - no password provided');
          } else {
            SharedLogger.log('[HardReset] Hard reset cancelled (modal closed)');
          }

          return;
        }

        // Validate password via backend API
        await this.validatePasswordAndReset(password);
      });

      SharedLogger.log('[HardReset] Hard reset button listener attached');
    } else {
      SharedLogger.error('[HardReset] Hard reset button not found!');
    }
  }

  /**
   * Initialize hard reset handler
   * Call once on page load
   */
  public init(): void {
    SharedLogger.log('[HardReset] Initializing Hard Reset Handler');

    this.setupResetButton();

    SharedLogger.log('[HardReset] Hard Reset Handler initialized');
  }
}

// Export singleton instance
export const HardResetHandler = HardResetHandlerManager.getInstance();
