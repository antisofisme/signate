/**
 * Fullscreen Manager Component
 * Handles fullscreen toggle, button interactions, and display rotation updates
 *
 * @features
 * - Update fullscreen state in DOM
 * - Apply display settings when entering/exiting fullscreen
 * - Setup mouse hover detection for buttons
 * - Setup fullscreen change event listeners
 * - Setup enter/exit fullscreen button handlers
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';

/**
 * Fullscreen Manager Class
 * Singleton pattern for fullscreen management
 */
class FullscreenManagerClass {
  private static instance: FullscreenManagerClass;
  private displaySettings: any = null;
  private shellUI: any = null;

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): FullscreenManagerClass {
    if (!FullscreenManagerClass.instance) {
      FullscreenManagerClass.instance = new FullscreenManagerClass();
    }
    return FullscreenManagerClass.instance;
  }

  /**
   * Set dependencies
   */
  public setDependencies(displaySettings: any, shellUI: any): void {
    this.displaySettings = displaySettings;
    this.shellUI = shellUI;
  }

  /**
   * Update fullscreen state in DOM and apply display settings
   * Called when entering or exiting fullscreen
   */
  private updateFullscreenState(): void {
    const playerContainer = document.getElementById('player-container');
    const isFullscreen = !!document.fullscreenElement;

    SharedLogger.log('[Fullscreen] Fullscreen state changed:', isFullscreen);

    if (isFullscreen) {
      SharedLogger.log('[Fullscreen] Entering fullscreen mode');
      playerContainer?.classList.add('fullscreen');
      document.body.classList.add('is-fullscreen');

      // Wait for browser to finish fullscreen transition, then update
      setTimeout(() => {
        // Recalculate rotation with new viewport dimensions
        SharedLogger.log('[Fullscreen] Recalculating rotation for fullscreen viewport...');
        if (this.displaySettings && 'applyRotation' in this.displaySettings) {
          (this.displaySettings as any).applyRotation();
        }

        // Reload player to update viewport size (ONLY if device is activated)
        const deviceStatus = SharedDeviceState.getDeviceStatus();
        if (deviceStatus === 'active') {
          SharedLogger.log('[Fullscreen] Reloading player for new viewport size...');
          if (this.shellUI) {
            this.shellUI.loadPlayer();
          }
        } else {
          SharedLogger.log('[Fullscreen] Device not activated yet, skip player reload');
        }
      }, 100); // Small delay for browser to complete fullscreen
    } else {
      SharedLogger.log('[Fullscreen] Exiting fullscreen mode');
      playerContainer?.classList.remove('fullscreen');
      document.body.classList.remove('is-fullscreen');

      // Wait for browser to finish fullscreen exit, then update
      setTimeout(() => {
        // Recalculate rotation with normal viewport dimensions
        SharedLogger.log('[Fullscreen] Recalculating rotation for normal viewport...');
        if (this.displaySettings && 'applyRotation' in this.displaySettings) {
          (this.displaySettings as any).applyRotation();
        }

        // Reload player to restore normal viewport size (ONLY if device is activated)
        const deviceStatus = SharedDeviceState.getDeviceStatus();
        if (deviceStatus === 'active') {
          SharedLogger.log('[Fullscreen] Reloading player for normal viewport size...');
          if (this.shellUI) {
            this.shellUI.loadPlayer();
          }
        } else {
          SharedLogger.log('[Fullscreen] Device not activated yet, skip player reload');
        }
      }, 100); // Small delay for browser to complete fullscreen exit
    }
  }

  /**
   * Setup mouse movement hover detection for buttons
   * Shows/hides fullscreen and action buttons based on cursor position
   */
  private setupMouseHover(): void {
    let hoverTimeout: number | null = null;
    let isInArea = false;

    document.addEventListener('mousemove', (e: MouseEvent) => {
      const screenWidth = window.innerWidth;
      // const screenHeight = window.innerHeight;
      const mouseX = e.clientX;
      const mouseY = e.clientY;

      const enterBtn = document.getElementById('enter-fullscreen-btn');
      const exitBtn = document.getElementById('exit-fullscreen-btn');
      const orgPinBtn = document.getElementById('org-pin-btn');
      const clearCacheBtn = document.getElementById('clear-cache-btn');
      const factoryResetBtn = document.getElementById('factory-reset-btn');
      const deviceInfoBtn = document.getElementById('device-info-btn');

      // Define hover area: right 100px, top 300px (untuk mencakup semua tombol sampai device info)
      const hoverAreaRight = 100;
      const hoverAreaTop = 300;

      const isNowInHoverArea = mouseX > screenWidth - hoverAreaRight && mouseY < hoverAreaTop;

      // If entering hover area
      if (isNowInHoverArea && !isInArea) {
        isInArea = true;

        // Clear any existing timeout
        if (hoverTimeout) {
          clearTimeout(hoverTimeout);
        }

        // Show buttons after 300ms hover (prevents accidental triggers)
        hoverTimeout = window.setTimeout(() => {
          // Show buttons based on fullscreen state
          if (document.fullscreenElement) {
            // In fullscreen - show exit button
            exitBtn?.classList.add('show');
            enterBtn?.classList.remove('show');
          } else {
            // Not in fullscreen - show enter button
            enterBtn?.classList.add('show');
            exitBtn?.classList.remove('show');
          }
          // Always show all utility buttons in hover area
          orgPinBtn?.classList.add('show');
          clearCacheBtn?.classList.add('show');
          factoryResetBtn?.classList.add('show');
          deviceInfoBtn?.classList.add('show');
        }, 300); // Require 300ms hover before showing buttons
      }
      // If leaving hover area
      else if (!isNowInHoverArea && isInArea) {
        isInArea = false;

        // Clear timeout if user moves away before buttons show
        if (hoverTimeout) {
          clearTimeout(hoverTimeout);
          hoverTimeout = null;
        }

        // Hide all buttons immediately when leaving area
        enterBtn?.classList.remove('show');
        exitBtn?.classList.remove('show');
        orgPinBtn?.classList.remove('show');
        clearCacheBtn?.classList.remove('show');
        factoryResetBtn?.classList.remove('show');
        deviceInfoBtn?.classList.remove('show');
      }
    });
  }

  /**
   * Setup fullscreen change event listeners for different browsers
   */
  private setupFullscreenListeners(): void {
    document.addEventListener('fullscreenchange', () => this.updateFullscreenState());
    document.addEventListener('webkitfullscreenchange', () => this.updateFullscreenState());
    document.addEventListener('mozfullscreenchange', () => this.updateFullscreenState());
    document.addEventListener('MSFullscreenChange', () => this.updateFullscreenState());
  }

  /**
   * Setup enter fullscreen button click handler
   */
  private setupEnterButton(): void {
    const enterBtn = document.getElementById('enter-fullscreen-btn');
    if (enterBtn) {
      enterBtn.addEventListener('click', () => {
        SharedLogger.log('[Fullscreen] Enter button clicked');
        if (!document.fullscreenElement) {
          SharedLogger.log('[Fullscreen] Entering fullscreen via button...');
          const elem = document.documentElement;

          const requestFullscreen =
            elem.requestFullscreen ||
            (elem as any).webkitRequestFullscreen ||
            (elem as any).mozRequestFullScreen ||
            (elem as any).msRequestFullscreen;

          if (requestFullscreen) {
            requestFullscreen
              .call(elem)
              .then(() => {
                SharedLogger.log('[Fullscreen] Fullscreen entered successfully');
              })
              .catch((err: Error) => {
                SharedLogger.error('[Fullscreen] Fullscreen error:', err);
              });
          }
        } else {
          SharedLogger.log('[Fullscreen] Already in fullscreen');
        }
      });
      SharedLogger.log('[Fullscreen] Enter button listener attached');
    } else {
      SharedLogger.error('[Fullscreen] Enter button not found!');
    }
  }

  /**
   * Setup exit fullscreen button click handler
   */
  private setupExitButton(): void {
    const exitBtn = document.getElementById('exit-fullscreen-btn');
    if (exitBtn) {
      exitBtn.addEventListener('click', () => {
        SharedLogger.log('[Fullscreen] Exit button clicked');
        if (document.fullscreenElement) {
          SharedLogger.log('[Fullscreen] Exiting fullscreen via button...');
          document.exitFullscreen();
        } else {
          SharedLogger.log('[Fullscreen] Already not in fullscreen');
        }
      });
      SharedLogger.log('[Fullscreen] Exit button listener attached');
    } else {
      SharedLogger.error('[Fullscreen] Exit button not found!');
    }
  }

  /**
   * Initialize fullscreen management
   * Call once on page load
   */
  public init(): void {
    SharedLogger.log('[Fullscreen] Initializing Fullscreen Manager');

    // Setup all listeners and handlers
    this.setupMouseHover();
    this.setupFullscreenListeners();
    this.setupEnterButton();
    this.setupExitButton();

    // Set initial state
    this.updateFullscreenState();

    SharedLogger.log('[Fullscreen] Fullscreen Manager initialized');
  }
}

// Export singleton instance
export const FullscreenManager = FullscreenManagerClass.getInstance();
