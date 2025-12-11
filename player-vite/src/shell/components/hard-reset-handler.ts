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
   * Check if error indicates orphaned device (device deleted from backend)
   * Orphaned devices should be allowed to reset locally
   */
  private isOrphanedDeviceError(error: any): boolean {
    const status = error?.response?.status;
    // 401 = Unauthorized (invalid/expired token)
    // 403 = Forbidden (device doesn't exist or no permission)
    // 404 = Not found (device deleted)
    return status === 401 || status === 403 || status === 404;
  }

  /**
   * Validate Organization PIN and execute reset if valid
   *
   * Flow (with new /hard-reset-pin endpoint):
   * 1. Get device config (deviceId, orgId)
   * 2. Call /api/v1/devices/{id}/hard-reset-pin with { organization_id, pin }
   * 3. Backend validates PIN and sets device status to 'released'
   * 4. If successful, clear ALL local data (including org_id)
   * 5. Reload → device requests code WITHOUT org_id
   * 6. Device appears in GLOBAL pending list
   *
   * IMPORTANT: If device has no org_id (orphaned), just clear local data.
   * This allows recovery of completely orphaned devices.
   */
  private async validatePasswordAndReset(pin: string): Promise<void> {
    try {
      // Get device config
      const deviceConfig = await deviceConfigStorage.getDeviceConfig();
      const deviceId = deviceConfig.device_id;
      const orgId = deviceConfig.organization_id;

      SharedLogger.log('[HardReset] Starting reset...', { deviceId, orgId });

      // Validate PIN is not empty
      if (!pin || pin.length === 0) {
        SharedToast.error('PIN required for reset. Hard reset cancelled.');
        this.isResetting = false;
        return;
      }

      // Validate PIN AND perform hard reset in one call
      // The endpoint accepts optional device_id to perform hard reset if PIN is valid
      if (orgId) {
        try {
          SharedLogger.log('[HardReset] Validating organization PIN and resetting device...');
          const validation = await SharedAPIClient.post<{ valid: boolean; message?: string; device_reset?: boolean }>(
            `/api/v1/organizations/${orgId}/validate-reset-pin`,
            { pin, device_id: deviceId }  // Include device_id to trigger backend reset
          );

          if (!validation.valid) {
            SharedToast.error('Invalid organization PIN. Hard reset cancelled.');
            SharedLogger.error('[HardReset] ❌ Invalid PIN');
            this.isResetting = false;
            return;
          }

          if (validation.device_reset === true) {
            SharedLogger.log('[HardReset] ✅ PIN validated and device released from backend');
          } else if (validation.device_reset === false) {
            SharedLogger.warn('[HardReset] ⚠️ PIN valid but device not found or org mismatch');
          } else {
            SharedLogger.log('[HardReset] ✅ PIN validated (no device_id provided)');
          }
        } catch (valError: any) {
          const status = valError?.response?.status;
          if (status === 403 || status === 401) {
            SharedToast.error('Invalid organization PIN. Hard reset cancelled.');
            SharedLogger.error('[HardReset] ❌ PIN validation failed');
            this.isResetting = false;
            return;
          }
          // If org not found or network error, proceed with local reset
          SharedLogger.warn('[HardReset] PIN validation failed, proceeding with local reset:', valError?.message);
        }
      }

      // Step 3: Clear ALL local data and reload
      SharedToast.success('Resetting device...');
      await this.executeReset();
    } catch (error: any) {
      SharedLogger.error('[HardReset] Error during hard reset:', error);

      // Check if device is orphaned - if so, still allow local reset
      if (this.isOrphanedDeviceError(error)) {
        SharedLogger.warn('[HardReset] Device orphaned - proceeding with local data clear');
        SharedToast.warning('Device not found in server. Clearing local data...');
        await this.executeReset();
        return;
      }

      SharedToast.error('Hard reset failed. Please try again.');
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

        // Prompt for organization PIN using modal
        let pin: string;
        try {
          pin = await SharedModal.prompt(
            'Factory Reset Device',
            'This will ERASE ALL DATA and require re-activation. Enter organization PIN to confirm:'
          );
        } catch (err: any) {
          // User cancelled or didn't enter PIN
          const errorMsg = err?.message || 'Unknown error';

          if (errorMsg === 'No input provided') {
            SharedToast.warning('Organization PIN required for factory reset.');
            SharedLogger.log('[HardReset] Hard reset cancelled - no PIN provided');
          } else {
            SharedLogger.log('[HardReset] Hard reset cancelled (modal closed)');
          }

          return;
        }

        // Validate PIN via organization API
        await this.validatePasswordAndReset(pin);
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
