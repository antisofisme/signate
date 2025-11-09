/**
 * Shell Fullscreen Handler
 * Manages fullscreen mode for player
 *
 * @features
 * - Auto-enter fullscreen on load
 * - Handle standard Fullscreen API
 * - Support webOS TV fullscreen methods
 * - Support Tizen TV fullscreen methods
 * - Listen to EventBus FULLSCREEN events
 * - Handle fullscreen change events
 * - Auto-initialize on import
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';

/**
 * Fullscreen request options
 */
export interface FullscreenOptions {
  navigationUI?: 'auto' | 'show' | 'hide';
}

/**
 * Shell Fullscreen Handler Class
 * Singleton pattern for fullscreen management
 */
class ShellFullscreenHandlerClass {
  private initialized = false;
  private isFullscreen = false;
  private autoEnterOnLoad = true;

  /**
   * Check if running on TV platform (webOS, Tizen, Android TV)
   */
  private isTVPlatform(): boolean {
    const ua = navigator.userAgent.toLowerCase();
    return (
      ua.includes('webos') ||
      ua.includes('web0s') ||
      ua.includes('tizen') ||
      ua.includes('android tv')
    );
  }

  /**
   * Initialize fullscreen handler
   */
  init(autoEnter = true): void {
    if (this.initialized) {
      SharedLogger.warn('[FullscreenHandler] Already initialized');
      return;
    }

    this.initialized = true;
    this.autoEnterOnLoad = autoEnter;

    // Listen to fullscreen change events
    document.addEventListener('fullscreenchange', this.handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', this.handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', this.handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', this.handleFullscreenChange);

    // Listen to EventBus events
    SharedEventBus.on('fullscreen:enter', () => this.enter(), 'fullscreen-handler');
    SharedEventBus.on('fullscreen:exit', () => this.exit(), 'fullscreen-handler');
    SharedEventBus.on('fullscreen:toggle', () => this.toggle(), 'fullscreen-handler');

    // Auto-enter fullscreen on load (only for TV platforms)
    if (this.autoEnterOnLoad && this.isTVPlatform()) {
      // Delay to allow page to fully load
      setTimeout(() => {
        SharedLogger.log('[FullscreenHandler] Auto-entering fullscreen for TV platform...');
        this.enter();
      }, 1000);
    } else if (this.autoEnterOnLoad) {
      SharedLogger.log('[FullscreenHandler] Auto-enter disabled for browser (requires user gesture)');
    }

    SharedLogger.log('[FullscreenHandler] Initialized - Auto-enter:', autoEnter);
  }

  /**
   * Enter fullscreen mode
   */
  async enter(options?: FullscreenOptions): Promise<boolean> {
    if (this.isFullscreen) {
      SharedLogger.log('[FullscreenHandler] Already in fullscreen');
      return true;
    }

    try {
      const element = document.documentElement;

      // Try webOS TV fullscreen
      if (this.enterWebOSFullscreen()) {
        return true;
      }

      // Try Tizen TV fullscreen
      if (this.enterTizenFullscreen()) {
        return true;
      }

      // Try standard Fullscreen API
      if (element.requestFullscreen) {
        await element.requestFullscreen(options);
      }
      // @ts-ignore - webkit prefix
      else if (element.webkitRequestFullscreen) {
        // @ts-ignore
        await element.webkitRequestFullscreen();
      }
      // @ts-ignore - moz prefix
      else if (element.mozRequestFullScreen) {
        // @ts-ignore
        await element.mozRequestFullScreen();
      }
      // @ts-ignore - ms prefix
      else if (element.msRequestFullscreen) {
        // @ts-ignore
        await element.msRequestFullscreen();
      } else {
        SharedLogger.warn('[FullscreenHandler] Fullscreen API not supported');
        return false;
      }

      SharedLogger.log('[FullscreenHandler] Entered fullscreen');
      return true;
    } catch (error) {
      SharedLogger.error('[FullscreenHandler] Failed to enter fullscreen:', error);
      return false;
    }
  }

  /**
   * Exit fullscreen mode
   */
  async exit(): Promise<boolean> {
    if (!this.isFullscreen) {
      SharedLogger.log('[FullscreenHandler] Not in fullscreen');
      return true;
    }

    try {
      // Try webOS TV fullscreen
      if (this.exitWebOSFullscreen()) {
        return true;
      }

      // Try Tizen TV fullscreen
      if (this.exitTizenFullscreen()) {
        return true;
      }

      // Try standard Fullscreen API
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      }
      // @ts-ignore - webkit prefix
      else if (document.webkitExitFullscreen) {
        // @ts-ignore
        await document.webkitExitFullscreen();
      }
      // @ts-ignore - moz prefix
      else if (document.mozCancelFullScreen) {
        // @ts-ignore
        await document.mozCancelFullScreen();
      }
      // @ts-ignore - ms prefix
      else if (document.msExitFullscreen) {
        // @ts-ignore
        await document.msExitFullscreen();
      }

      SharedLogger.log('[FullscreenHandler] Exited fullscreen');
      return true;
    } catch (error) {
      SharedLogger.error('[FullscreenHandler] Failed to exit fullscreen:', error);
      return false;
    }
  }

  /**
   * Toggle fullscreen mode
   */
  async toggle(): Promise<boolean> {
    if (this.isFullscreen) {
      return this.exit();
    } else {
      return this.enter();
    }
  }

  /**
   * Get fullscreen status
   */
  getStatus(): boolean {
    return this.isFullscreen;
  }

  /**
   * Check if fullscreen is available
   */
  isAvailable(): boolean {
    const element = document.documentElement;

    return !!(
      element.requestFullscreen ||
      // @ts-ignore
      element.webkitRequestFullscreen ||
      // @ts-ignore
      element.mozRequestFullScreen ||
      // @ts-ignore
      element.msRequestFullscreen ||
      // @ts-ignore
      typeof window.webOS !== 'undefined' ||
      // @ts-ignore
      typeof window.tizen !== 'undefined'
    );
  }

  /**
   * Handle fullscreen change event
   */
  private handleFullscreenChange = (): void => {
    const wasFullscreen = this.isFullscreen;

    this.isFullscreen = !!(
      document.fullscreenElement ||
      // @ts-ignore
      document.webkitFullscreenElement ||
      // @ts-ignore
      document.mozFullScreenElement ||
      // @ts-ignore
      document.msFullscreenElement
    );

    if (this.isFullscreen !== wasFullscreen) {
      if (this.isFullscreen) {
        SharedEventBus.emit(EventNames.UI_FULLSCREEN_ENTER);
        SharedLogger.log('[FullscreenHandler] Fullscreen entered');
      } else {
        SharedEventBus.emit(EventNames.UI_FULLSCREEN_EXIT);
        SharedLogger.log('[FullscreenHandler] Fullscreen exited');
      }
    }
  };

  /**
   * Enter fullscreen on webOS TV
   */
  private enterWebOSFullscreen(): boolean {
    // @ts-ignore - webOS API
    if (typeof window.webOS !== 'undefined' && window.webOS.platformBack) {
      try {
        // webOS TVs are already fullscreen by default
        this.isFullscreen = true;
        SharedEventBus.emit(EventNames.UI_FULLSCREEN_ENTER);
        SharedLogger.log('[FullscreenHandler] webOS TV - Already fullscreen');
        return true;
      } catch (error) {
        SharedLogger.error('[FullscreenHandler] webOS fullscreen error:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Exit fullscreen on webOS TV
   */
  private exitWebOSFullscreen(): boolean {
    // @ts-ignore - webOS API
    if (typeof window.webOS !== 'undefined' && window.webOS.platformBack) {
      try {
        // Cannot exit fullscreen on webOS TV
        SharedLogger.warn('[FullscreenHandler] Cannot exit fullscreen on webOS TV');
        return true;
      } catch (error) {
        SharedLogger.error('[FullscreenHandler] webOS exit fullscreen error:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Enter fullscreen on Tizen TV
   */
  private enterTizenFullscreen(): boolean {
    // @ts-ignore - Tizen API
    if (typeof window.tizen !== 'undefined') {
      try {
        // Tizen TVs are already fullscreen by default
        this.isFullscreen = true;
        SharedEventBus.emit(EventNames.UI_FULLSCREEN_ENTER);
        SharedLogger.log('[FullscreenHandler] Tizen TV - Already fullscreen');
        return true;
      } catch (error) {
        SharedLogger.error('[FullscreenHandler] Tizen fullscreen error:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Exit fullscreen on Tizen TV
   */
  private exitTizenFullscreen(): boolean {
    // @ts-ignore - Tizen API
    if (typeof window.tizen !== 'undefined') {
      try {
        // Cannot exit fullscreen on Tizen TV
        SharedLogger.warn('[FullscreenHandler] Cannot exit fullscreen on Tizen TV');
        return true;
      } catch (error) {
        SharedLogger.error('[FullscreenHandler] Tizen exit fullscreen error:', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Request fullscreen with error handling
   */
  async requestFullscreen(element?: HTMLElement): Promise<void> {
    const targetElement = element || document.documentElement;

    try {
      if (targetElement.requestFullscreen) {
        await targetElement.requestFullscreen();
      }
      // @ts-ignore
      else if (targetElement.webkitRequestFullscreen) {
        // @ts-ignore
        await targetElement.webkitRequestFullscreen();
      }
      // @ts-ignore
      else if (targetElement.mozRequestFullScreen) {
        // @ts-ignore
        await targetElement.mozRequestFullScreen();
      }
      // @ts-ignore
      else if (targetElement.msRequestFullscreen) {
        // @ts-ignore
        await targetElement.msRequestFullscreen();
      }
    } catch (error) {
      SharedLogger.error('[FullscreenHandler] Fullscreen request failed:', error);
      throw error;
    }
  }

  /**
   * Cleanup event listeners
   */
  destroy(): void {
    document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('mozfullscreenchange', this.handleFullscreenChange);
    document.removeEventListener('MSFullscreenChange', this.handleFullscreenChange);
    SharedEventBus.removeNamespace('fullscreen-handler');
    this.initialized = false;
    SharedLogger.log('[FullscreenHandler] Destroyed');
  }
}

// Export singleton instance
export const ShellFullscreenHandler = new ShellFullscreenHandlerClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellFullscreenHandler: typeof ShellFullscreenHandler;
  }
}

if (typeof window !== 'undefined') {
  window.ShellFullscreenHandler = ShellFullscreenHandler;
}

// Auto-initialize when module is imported
ShellFullscreenHandler.init();
