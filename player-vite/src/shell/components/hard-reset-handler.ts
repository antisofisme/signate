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
   * Flow:
   * 1. Get organization_id from device config
   * 2. Validate PIN via /api/v1/organizations/{org_id}/validate-reset-pin
   * 3. If valid, clear ALL device config (including org_id)
   * 4. Reload → device requests code WITHOUT org_id
   * 5. Device appears in GLOBAL pending list
   *
   * IMPORTANT: If device has no org_id (orphaned), skip PIN validation
   * and just clear local data. This allows recovery of completely orphaned devices.
   */
  private async validatePasswordAndReset(pin: string): Promise<void> {
    try {
      // Get device config
      const deviceConfig = await deviceConfigStorage.getDeviceConfig();
      const deviceId = deviceConfig.device_id;
      const orgId = deviceConfig.organization_id;

      SharedLogger.log('[HardReset] Starting reset validation...', { deviceId, orgId });

      // Scenario 1: Device with org_id → validate with organization PIN
      if (orgId) {
        SharedLogger.log('[HardReset] Validating with organization PIN...', { orgId });

        try {
          const validation = await SharedAPIClient.post<{ valid: boolean; message?: string }>(
            `/api/v1/organizations/${orgId}/validate-reset-pin`,
            { pin }
          );

          if (!validation.valid) {
            SharedToast.error('Invalid organization PIN. Hard reset cancelled.');
            SharedLogger.error('[HardReset] ❌ Organization PIN validation failed');
            this.isResetting = false;
            return;
          }

          SharedLogger.log('[HardReset] ✅ Organization PIN validated');
        } catch (valError: any) {
          // If org not found or network error → proceed with reset anyway
          // This handles edge case where org was deleted but device still has org_id cached
          SharedLogger.warn('[HardReset] Org validation failed (proceeding with reset):', valError?.response?.status);
        }
      } else {
        // Scenario 2: No org_id (orphaned device) → skip PIN validation
        SharedLogger.warn('[HardReset] No org_id - skipping PIN validation (orphaned device recovery)');

        // Still require non-empty PIN to prevent accidental resets
        if (!pin || pin.length === 0) {
          SharedToast.error('PIN required for reset. Hard reset cancelled.');
          this.isResetting = false;
          return;
        }
      }

      // Step 2: Try to call backend hard reset endpoint (optional - may fail for orphaned devices)
      if (deviceId) {
        try {
          await SharedAPIClient.post(`/api/v1/devices/${deviceId}/hard-reset`);
          SharedLogger.log('[HardReset] ✅ Backend hard reset endpoint called');
        } catch (resetError: any) {
          // If device is orphaned (401/403/404), proceed anyway
          if (this.isOrphanedDeviceError(resetError)) {
            SharedLogger.warn('[HardReset] Device orphaned - skipping backend call');
          } else {
            // Log but don't fail - local reset is the important part
            SharedLogger.warn('[HardReset] Backend reset failed (proceeding with local reset):', resetError?.message);
          }
        }
      } else {
        SharedLogger.log('[HardReset] No device_id - skipping backend call');
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
