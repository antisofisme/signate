/**
 * Waiting for Content Component
 * Displays minimalist professional screen when no playlist is assigned
 *
 * @features
 * - Elegant dark gradient background
 * - Animated film icon with pulse effect
 * - Device information display
 * - Online status indicator
 * - Smooth fade-in animation
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';

/**
 * Waiting for Content Manager Class
 * Singleton pattern for waiting screen management
 */
class WaitingForContentManager {
  private static instance: WaitingForContentManager;
  private waitingElement: HTMLElement | null = null;

  private constructor() {
    SharedLogger.log('[WaitingForContent] Initializing...');
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): WaitingForContentManager {
    if (!WaitingForContentManager.instance) {
      WaitingForContentManager.instance = new WaitingForContentManager();
    }
    return WaitingForContentManager.instance;
  }

  /**
   * Create and inject waiting screen HTML
   */
  private createWaitingScreen(): HTMLElement {
    const div = document.createElement('div');
    div.id = 'waiting-for-content';
    div.innerHTML = `
      <style>
        #waiting-for-content {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #e2e8f0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          opacity: 0;
          animation: fadeIn 0.8s ease forwards;
          z-index: 100;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
        }

        .waiting-icon {
          width: 80px;
          height: 80px;
          margin-bottom: 2rem;
          color: #64748b;
          animation: pulse 2s ease-in-out infinite;
        }

        .waiting-title {
          font-size: 2rem;
          font-weight: 300;
          margin: 0 0 1rem 0;
          color: #f1f5f9;
          letter-spacing: 0.05em;
        }

        .waiting-subtitle {
          font-size: 1.125rem;
          font-weight: 300;
          margin: 0 0 3rem 0;
          color: #94a3b8;
        }

        .waiting-device-info {
          text-align: center;
          margin-bottom: 2rem;
        }

        .waiting-device-line {
          font-size: 0.9375rem;
          margin: 0.5rem 0;
          color: #cbd5e1;
          font-weight: 300;
        }

        .waiting-device-line strong {
          color: #f1f5f9;
          font-weight: 400;
        }

        .waiting-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.9375rem;
          color: #94a3b8;
          margin-top: 0.5rem;
        }

        .waiting-status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
        }

        .waiting-instruction {
          font-size: 0.875rem;
          color: #64748b;
          margin-top: 2rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .waiting-instruction svg {
          width: 16px;
          height: 16px;
        }
      </style>

      <svg class="waiting-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5" />
      </svg>

      <h1 class="waiting-title">Waiting for Content</h1>
      <p class="waiting-subtitle">No playlist assigned to this device</p>

      <div class="waiting-device-info">
        <div class="waiting-device-line">
          <strong>Device:</strong> <span id="waiting-device-name">-</span>
        </div>
        <div class="waiting-device-line">
          <strong>Room:</strong> <span id="waiting-room-number">-</span>
        </div>
        <div class="waiting-status">
          <span class="waiting-status-dot"></span>
          <span>Active • Online</span>
        </div>
      </div>

      <div class="waiting-instruction">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 011.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.56.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.893.149c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 01-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.397.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 01-.12-1.45l.527-.737c.25-.35.273-.806.108-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.107-1.204l-.527-.738a1.125 1.125 0 01.12-1.45l.773-.773a1.125 1.125 0 011.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Please assign content from CMS
      </div>
    `;

    return div;
  }

  /**
   * Show waiting screen with device info
   */
  public show(): void {
    SharedLogger.log('[WaitingForContent] Showing waiting screen');

    // Get player container
    const playerContainer = document.getElementById('player-container');
    if (!playerContainer) {
      SharedLogger.error('[WaitingForContent] Player container not found');
      return;
    }

    // Create waiting screen if not exists
    if (!this.waitingElement) {
      this.waitingElement = this.createWaitingScreen();
      playerContainer.appendChild(this.waitingElement);
    }

    // Update device info
    this.updateDeviceInfo();

    // Show waiting screen
    this.waitingElement.style.display = 'flex';

    // Hide video element
    const video = document.getElementById('player-video');
    if (video) {
      video.style.display = 'none';
    }
  }

  /**
   * Hide waiting screen
   */
  public hide(): void {
    SharedLogger.log('[WaitingForContent] Hiding waiting screen');

    if (this.waitingElement) {
      this.waitingElement.style.display = 'none';
    }

    // Show video element
    const video = document.getElementById('player-video');
    if (video) {
      video.style.display = 'block';
    }
  }

  /**
   * Update device information in waiting screen
   */
  private updateDeviceInfo(): void {
    if (!this.waitingElement) return;

    // Get device info from SharedDeviceState
    const deviceName = SharedDeviceState.getDeviceName() || 'Unknown Device';
    const deviceId = SharedDeviceState.getDeviceId();

    // Try to get room number from localStorage (might be stored during activation)
    let roomNumber = localStorage.getItem('device_room_number');

    // If not in localStorage, construct from device name or ID
    if (!roomNumber) {
      roomNumber = deviceName !== 'Unknown Device' ? `Device #${deviceId}` : '-';
    }

    // Update DOM
    const deviceNameEl = this.waitingElement.querySelector('#waiting-device-name');
    const roomNumberEl = this.waitingElement.querySelector('#waiting-room-number');

    if (deviceNameEl) {
      deviceNameEl.textContent = deviceName;
    }

    if (roomNumberEl) {
      roomNumberEl.textContent = roomNumber;
    }

    SharedLogger.log('[WaitingForContent] Device info updated:', {
      deviceName,
      roomNumber,
    });
  }

  /**
   * Check if waiting screen is currently visible
   */
  public isVisible(): boolean {
    return this.waitingElement?.style.display === 'flex';
  }
}

// Export singleton instance
export const WaitingForContent = WaitingForContentManager.getInstance();
