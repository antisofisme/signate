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
  private isInitialized = false;

  // Event handler references for cleanup
  private mousemoveHandler: ((e: MouseEvent) => void) | null = null;
  private fullscreenChangeHandler: (() => void) | null = null;
  private enterBtnHandler: (() => void) | null = null;
  private exitBtnHandler: (() => void) | null = null;

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

    // Store handler reference for cleanup
    this.mousemoveHandler = (e: MouseEvent) => {
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
    };

    document.addEventListener('mousemove', this.mousemoveHandler);
  }

  /**
   * Setup fullscreen change event listeners for different browsers
   */
  private setupFullscreenListeners(): void {
    // Store handler reference for cleanup
    this.fullscreenChangeHandler = () => this.updateFullscreenState();

    document.addEventListener('fullscreenchange', this.fullscreenChangeHandler);
    document.addEventListener('webkitfullscreenchange', this.fullscreenChangeHandler);
    document.addEventListener('mozfullscreenchange', this.fullscreenChangeHandler);
    document.addEventListener('MSFullscreenChange', this.fullscreenChangeHandler);
  }

  /**
   * Setup enter fullscreen button click handler
   */
  private setupEnterButton(): void {
    const enterBtn = document.getElementById('enter-fullscreen-btn');
    if (enterBtn) {
      // Store handler reference for cleanup
      this.enterBtnHandler = () => {
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
      };
      enterBtn.addEventListener('click', this.enterBtnHandler);
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
      // Store handler reference for cleanup
      this.exitBtnHandler = () => {
        SharedLogger.log('[Fullscreen] Exit button clicked');
        if (document.fullscreenElement) {
          SharedLogger.log('[Fullscreen] Exiting fullscreen via button...');
          document.exitFullscreen();
        } else {
          SharedLogger.log('[Fullscreen] Already not in fullscreen');
        }
      };
      exitBtn.addEventListener('click', this.exitBtnHandler);
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
    // Prevent double initialization
    if (this.isInitialized) {
      SharedLogger.warn('[Fullscreen] Already initialized, skipping');
      return;
    }

    SharedLogger.log('[Fullscreen] Initializing Fullscreen Manager');

    // Setup all listeners and handlers
    this.setupMouseHover();
    this.setupFullscreenListeners();
    this.setupEnterButton();
    this.setupExitButton();

    // Set initial state
    this.updateFullscreenState();

    this.isInitialized = true;
    SharedLogger.log('[Fullscreen] Fullscreen Manager initialized');
  }

  /**
   * Cleanup fullscreen management
   */
  public destroy(): void {
    // Remove mousemove handler
    if (this.mousemoveHandler) {
      document.removeEventListener('mousemove', this.mousemoveHandler);
      this.mousemoveHandler = null;
    }

    // Remove fullscreen change handlers
    if (this.fullscreenChangeHandler) {
      document.removeEventListener('fullscreenchange', this.fullscreenChangeHandler);
      document.removeEventListener('webkitfullscreenchange', this.fullscreenChangeHandler);
      document.removeEventListener('mozfullscreenchange', this.fullscreenChangeHandler);
      document.removeEventListener('MSFullscreenChange', this.fullscreenChangeHandler);
      this.fullscreenChangeHandler = null;
    }

    // Remove button handlers
    const enterBtn = document.getElementById('enter-fullscreen-btn');
    const exitBtn = document.getElementById('exit-fullscreen-btn');

    if (enterBtn && this.enterBtnHandler) {
      enterBtn.removeEventListener('click', this.enterBtnHandler);
      this.enterBtnHandler = null;
    }

    if (exitBtn && this.exitBtnHandler) {
      exitBtn.removeEventListener('click', this.exitBtnHandler);
      this.exitBtnHandler = null;
    }

    this.isInitialized = false;
    SharedLogger.log('[Fullscreen] Fullscreen Manager destroyed');
  }
}

// Export singleton instance
export const FullscreenManager = FullscreenManagerClass.getInstance();
