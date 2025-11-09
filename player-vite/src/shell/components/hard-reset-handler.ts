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
import { SharedDeviceState } from '@shared/device';

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
   * Clear localStorage and IndexedDB, then reload page
   * Called after password validation
   */
  private executeReset(): void {
    // Set flag to prevent double execution
    this.isResetting = true;
    SharedLogger.log('[HardReset] Password verified, executing hard reset...');

    // Log BEFORE clear
    console.log('[HardReset] BEFORE clear - localStorage:', {
      deviceId: localStorage.getItem('device_id'),
      status: localStorage.getItem('device_status'),
      code: localStorage.getItem('device_code'),
      organizationId: localStorage.getItem('organization_id'),
    });

    // Clear localStorage (includes device data)
    localStorage.clear();

    // Verify cleared
    console.log('[HardReset] AFTER clear - localStorage:', {
      deviceId: localStorage.getItem('device_id'),
      status: localStorage.getItem('device_status'),
      code: localStorage.getItem('device_code'),
      organizationId: localStorage.getItem('organization_id'),
    });
    SharedLogger.log('[HardReset] localStorage cleared (all device data removed)');

    // Clear IndexedDB cache
    let reloadExecuted = false; // Prevent multiple reloads

    const executeReload = (): void => {
      if (!reloadExecuted) {
        reloadExecuted = true;
        SharedLogger.log('[HardReset] Reloading page to complete hard reset...');
        // Use location.replace() to prevent browser from restoring localStorage from cache
        setTimeout(() => location.replace(location.href), 100); // Small delay for logs
      }
    };

    try {
      // Try to open PlayerCache DB and clear it
      const dbName = 'signage_media_cache';
      const deleteRequest = indexedDB.deleteDatabase(dbName);

      deleteRequest.onsuccess = () => {
        SharedLogger.log('[HardReset] IndexedDB cache deleted');
        executeReload();
      };

      deleteRequest.onerror = () => {
        SharedLogger.error('[HardReset] IndexedDB delete failed, reloading anyway');
        executeReload();
      };

      deleteRequest.onblocked = () => {
        SharedLogger.warn('[HardReset] IndexedDB delete blocked, reloading anyway');
        executeReload();
      };

      // Fallback: If nothing happens in 2 seconds, reload anyway
      setTimeout(() => {
        if (!reloadExecuted) {
          SharedLogger.warn('[HardReset] IndexedDB delete timeout, reloading...');
          executeReload();
        }
      }, 2000);
    } catch (error) {
      SharedLogger.error('[HardReset] Error deleting IndexedDB:', error);
      executeReload();
    }
  }

  /**
   * Validate password locally and execute reset if valid
   *
   * Logic:
   * - If device has organization_pin → use organization PIN (6 digits)
   * - If no organization_pin → use default password 'admin123'
   */
  private async validatePasswordAndReset(password: string): Promise<void> {
    try {
      // Get organization PIN from localStorage
      const organizationPin = SharedDeviceState.getOrganizationPin();

      // Determine correct password
      const correctPassword = organizationPin || 'admin123';

      SharedLogger.log('[HardReset] Validating password...', {
        hasOrgPin: !!organizationPin,
        expectedPasswordType: organizationPin ? 'Organization PIN' : 'Default (admin123)'
      });

      // Validate password
      if (password === correctPassword) {
        SharedLogger.log('[HardReset] ✅ Password validated locally');
        this.executeReset();
      } else {
        SharedToast.error('Incorrect Password. Reset cancelled. Please try again.');
        SharedLogger.error('[HardReset] ❌ Hard reset failed - wrong password');
        this.isResetting = false; // Reset flag
      }
    } catch (error) {
      SharedLogger.error('[HardReset] Error validating password:', error);
      SharedToast.error('Could not validate password. Please try again.');
      this.isResetting = false; // Reset flag
    }
  }

  /**
   * Setup hard reset button click handler
   * Prompts for password before executing reset
   */
  private setupResetButton(): void {
    const resetBtn = document.getElementById('hard-reset-btn');

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
            'Hard Reset Device',
            'This will ERASE ALL DATA and require re-activation. Enter admin password to confirm:'
          );
        } catch (err) {
          SharedLogger.log('[HardReset] Hard reset cancelled (modal closed)');
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
