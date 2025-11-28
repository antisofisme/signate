/**
 * Keyboard Shortcuts Component
 * Handles keyboard events for common shell operations
 *
 * @features
 * - Toggle shell debug info ('s' key)
 * - Reload player ('r' key)
 * - Toggle fullscreen ('f' key)
 * - Exit fullscreen ('Esc' key)
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { SharedToast } from '@shared/ui';
import type { ShellUI } from './shell-ui';

/**
 * Keyboard Shortcuts Manager Class
 * Singleton pattern for keyboard shortcuts management
 */
class KeyboardShortcutsManager {
  private static instance: KeyboardShortcutsManager;
  private shellUI: typeof ShellUI | null = null;
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): KeyboardShortcutsManager {
    if (!KeyboardShortcutsManager.instance) {
      KeyboardShortcutsManager.instance = new KeyboardShortcutsManager();
    }
    return KeyboardShortcutsManager.instance;
  }

  /**
   * Set ShellUI dependency
   */
  public setShellUI(shellUI: typeof ShellUI): void {
    this.shellUI = shellUI;
  }

  /**
   * Handle 's' key - Toggle shell debug info
   */
  private handleDebugToggle(): void {
    const info = document.getElementById('shell-info');
    if (info) {
      info.style.display = info.style.display === 'none' ? 'block' : 'none';

      // Update debug info
      const debugDeviceId = document.getElementById('debug-device-id');
      const debugStatus = document.getElementById('debug-status');

      if (debugDeviceId) {
        debugDeviceId.textContent = SharedDeviceState.getDeviceId() || '-';
      }
      if (debugStatus) {
        debugStatus.textContent = SharedDeviceState.getDeviceStatus() || '-';
      }
    }
  }

  /**
   * Handle 'r' key - Reload player only
   */
  private handlePlayerReload(): void {
    if (this.shellUI) {
      this.shellUI.reloadPlayer();
    }
  }

  /**
   * Handle 'f' key - Toggle fullscreen
   */
  private handleFullscreenToggle(): void {
    SharedLogger.log(
      '[Keyboard] F key pressed, current fullscreen state:',
      !!document.fullscreenElement
    );

    if (!document.fullscreenElement) {
      // Enter fullscreen
      SharedLogger.log('[Keyboard] Attempting to enter fullscreen...');

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
            SharedLogger.log('[Keyboard] Fullscreen entered successfully');
          })
          .catch((err: Error) => {
            SharedLogger.error('[Keyboard] Fullscreen error:', err);
            SharedToast.error(`Fullscreen Failed: ${err.message}`);
          });
      } else {
        SharedLogger.error('[Keyboard] Fullscreen API not supported');
        SharedToast.error('Fullscreen Not Supported: Your browser does not support fullscreen mode');
      }
    } else {
      // Exit fullscreen
      SharedLogger.log('[Keyboard] Exiting fullscreen...');
      document.exitFullscreen();
    }
  }

  /**
   * Handle 'Esc' key - Exit fullscreen
   */
  private handleEscapeKey(): void {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  }

  /**
   * Initialize keyboard shortcuts
   * Call once on page load
   */
  public init(): void {
    // Prevent double initialization
    if (this.keydownHandler) {
      SharedLogger.warn('[Keyboard] Already initialized, skipping');
      return;
    }

    SharedLogger.log('[Keyboard] Initializing Keyboard Shortcuts');

    // Store handler reference for cleanup
    this.keydownHandler = (e: KeyboardEvent) => {
      // Press 's' to toggle shell debug info
      if (e.key === 's' || e.key === 'S') {
        this.handleDebugToggle();
      }

      // Press 'r' to reload player only (not shell)
      if (e.key === 'r' || e.key === 'R') {
        this.handlePlayerReload();
      }

      // Press 'f' to toggle fullscreen
      if (e.key === 'f' || e.key === 'F') {
        this.handleFullscreenToggle();
      }

      // Press 'Esc' to exit fullscreen
      if (e.key === 'Escape' && document.fullscreenElement) {
        this.handleEscapeKey();
      }
    };

    document.addEventListener('keydown', this.keydownHandler);

    SharedLogger.log('[Keyboard] Keyboard Shortcuts initialized');
  }

  /**
   * Cleanup keyboard shortcuts
   */
  public destroy(): void {
    if (this.keydownHandler) {
      document.removeEventListener('keydown', this.keydownHandler);
      this.keydownHandler = null;
      SharedLogger.log('[Keyboard] Keyboard Shortcuts destroyed');
    }
  }
}

// Export singleton instance
export const KeyboardShortcuts = KeyboardShortcutsManager.getInstance();
