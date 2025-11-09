/**
 * Shell UI Component
 * Handles UI updates for shell (activation screen, player loading)
 *
 * @features
 * - Update UI based on device status
 * - Show activation success message
 * - Load player in iframe
 * - Reload player
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device/shared-device-state';
import { SharedToast } from '@shared/ui';

/**
 * Device status type
 */
export type DeviceStatus = 'pending' | 'active' | 'inactive';

/**
 * Shell UI Manager Class
 * Singleton pattern for shell UI management
 */
class ShellUIManager {
  private static instance: ShellUIManager;
  private displaySettings: any = null;

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): ShellUIManager {
    if (!ShellUIManager.instance) {
      ShellUIManager.instance = new ShellUIManager();
    }
    return ShellUIManager.instance;
  }

  /**
   * Set display settings reference
   */
  public setDisplaySettings(settings: any): void {
    this.displaySettings = settings;
  }

  /**
   * Update UI based on status
   */
  public updateUI(status: DeviceStatus, code?: string | null): void {
    SharedLogger.log('[ShellUI] updateUI called - status:', status, 'code:', code);

    const statusElement = document.getElementById('status-message');
    const codeElement = document.getElementById('activation-code');
    const instructionElement = document.getElementById('activation-instruction');
    const activationScreen = document.getElementById('activation-screen');
    const playerContainer = document.getElementById('player-container');

    // Null check: Defensive programming to prevent crashes
    if (!statusElement) {
      SharedLogger.error('[ShellUI] Status element not found');
      return;
    }

    if (status === 'pending') {
      statusElement.textContent = '⏳ Waiting for approval...';

      // Update code if element exists
      if (codeElement && code) {
        codeElement.textContent = code;
      }

      // Update instruction based on organization_id
      if (instructionElement) {
        const device = SharedDeviceState.getDevice();
        const organizationId = device?.organization_id;

        SharedLogger.log(
          '[ShellUI] Updating instruction text - organization_id:',
          organizationId,
          'type:',
          typeof organizationId
        );

        // Check if organization_id exists AND is not null/undefined
        if (organizationId && String(organizationId) !== 'null' && String(organizationId) !== 'undefined') {
          // Re-registration (device already has organization)
          const newText = 'Admin will approve this device in the Web Admin panel';
          instructionElement.textContent = newText;
          SharedLogger.log('[ShellUI] Set instruction (re-registration):', newText);
        } else {
          // First-time registration (device doesn't have organization)
          const newText =
            'Daftarkan kode ini di CMS untuk menambahkan device ke organisasi Anda';
          instructionElement.textContent = newText;
          SharedLogger.log('[ShellUI] Set instruction (first-time):', newText);
        }
      } else {
        SharedLogger.error('[ShellUI] activation-instruction element not found!');
      }

      // Ensure activation screen is visible and player is hidden
      if (activationScreen) {
        activationScreen.style.display = 'flex';
      }
      if (playerContainer) {
        playerContainer.style.display = 'none';
      }
    } else if (status === 'active') {
      statusElement.textContent = '✅ Activated! Loading player...';

      // Keep activation screen visible until player loads
      if (activationScreen) {
        activationScreen.style.display = 'flex';
      }
      if (playerContainer) {
        playerContainer.style.display = 'none';
      }
    }
  }

  /**
   * Show activation success message
   */
  public showActivationSuccess(deviceName: string): void {
    SharedLogger.log(`[ShellUI] 🎉 Activation successful! Device: ${deviceName}`);
    const statusElement = document.getElementById('status-message');
    if (statusElement) {
      statusElement.textContent = `✅ Activated as: ${deviceName}`;
    }
  }

  /**
   * Load player in iframe with cache-busting timestamp
   */
  public loadPlayer(): void {
    const device = SharedDeviceState.getDevice();
    const deviceId = device?.id;

    const timestamp = Date.now();
    const iframe = document.getElementById('player-iframe') as HTMLIFrameElement;

    if (iframe) {
      // Get display settings to pass to Player
      const volumeParam = this.displaySettings?.getPlayerParams().volume_enabled ?? true;

      iframe.src = `player.html?t=${timestamp}&deviceId=${deviceId}&volume=${volumeParam}`;
      SharedLogger.log(
        '[ShellUI] Loading player iframe with deviceId:',
        deviceId,
        'volume:',
        volumeParam
      );

      // Listen for player errors
      iframe.onerror = () => {
        SharedLogger.error('[ShellUI] Player iframe failed to load');

        // Ensure error element exists before updating
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
          errorElement.textContent = 'Player failed to load. Retrying...';
        }

        // Show toast notification
        SharedToast.error('Player failed to load. Retrying in 5 seconds...', 4000);

        // Retry after configured interval
        const retryInterval = 5000;
        setTimeout(() => this.loadPlayer(), retryInterval);
      };

      // Hide activation screen, show player
      const activationScreen = document.getElementById('activation-screen');
      const playerContainer = document.getElementById('player-container');

      if (activationScreen) {
        activationScreen.style.display = 'none';
      }
      if (playerContainer) {
        playerContainer.style.display = 'block';
      }
    }
  }

  /**
   * Reload player (force refresh without clearing shell)
   */
  public reloadPlayer(): void {
    SharedLogger.log('[ShellUI] Reloading player...');
    this.loadPlayer();
  }
}

// Export singleton instance
export const ShellUI = ShellUIManager.getInstance();
