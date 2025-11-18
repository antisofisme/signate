/**
 * Player UI Component
 * Handles UI updates, loading states, and keyboard shortcuts
 *
 * @features
 * - Show/hide loading screen
 * - Show/hide waiting state
 * - Show/hide error messages
 * - Update debug info overlay
 * - Initialize keyboard shortcuts
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { i18n } from '@shared/services/i18n';

/**
 * Player UI Manager Class
 * Singleton pattern for player UI management
 */
class PlayerUIManager {
  private static instance: PlayerUIManager;

  private constructor() {
    SharedLogger.log('[PlayerUI] Initializing...');
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): PlayerUIManager {
    if (!PlayerUIManager.instance) {
      PlayerUIManager.instance = new PlayerUIManager();
    }
    return PlayerUIManager.instance;
  }

  /**
   * Show loading screen
   */
  public showLoading(message?: string): void {
    this.hideError();
    const loading = document.getElementById('loading');
    if (loading) {
      const paragraph = loading.querySelector('p');
      if (paragraph) {
        paragraph.textContent = message || i18n.t('player.loading');
      }
      loading.style.display = 'block';
    }
  }

  /**
   * Hide loading screen
   */
  public hideLoading(): void {
    const loading = document.getElementById('loading');
    if (loading) {
      loading.style.display = 'none';
    }
  }

  /**
   * Show waiting state (yellow spinner)
   */
  public showWaiting(message: string): void {
    SharedLogger.log('[PlayerUI] Waiting:', message);

    this.hideError();
    const loading = document.getElementById('loading');
    if (loading) {
      // Change spinner color to yellow/orange for waiting state
      const spinner = loading.querySelector('.spinner');
      if (spinner instanceof HTMLElement) {
        spinner.style.borderTopColor = '#ffa500';
      }

      const paragraph = loading.querySelector('p');
      if (paragraph instanceof HTMLElement) {
        paragraph.textContent = message;
        paragraph.style.color = '#ffa500';
      }

      loading.style.display = 'block';
    }
  }

  /**
   * Show error message
   */
  public showError(message: string): void {
    SharedLogger.error('[PlayerUI] Error:', message);

    this.hideLoading();
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');

    if (error && errorMessage) {
      errorMessage.textContent = message;
      error.style.display = 'block';
    }
  }

  /**
   * Hide error message
   */
  public hideError(): void {
    const error = document.getElementById('error');
    if (error) {
      error.style.display = 'none';
    }
  }

  /**
   * Update debug info overlay
   */
  public updateDebugInfo(
    content: any,
    index: number,
    isCached: boolean
  ): void {
    if (!content) {
      SharedLogger.debug('[PlayerUI] Cannot update debug info - missing content');
      return;
    }

    const debugContent = document.getElementById('debug-content');
    const debugIndex = document.getElementById('debug-index');
    const debugType = document.getElementById('debug-type');
    const debugCache = document.getElementById('debug-cache');

    if (debugContent) {
      debugContent.textContent = content.title || content.name || 'Unknown';
    }
    if (debugIndex) {
      debugIndex.textContent = String(index + 1);
    }
    if (debugType) {
      debugType.textContent = content.content_type || 'unknown';
    }
    if (debugCache) {
      debugCache.textContent = isCached ? 'Cached ✅' : 'Downloading...';
    }
  }

  /**
   * Update total count in debug info
   */
  public updateDebugTotal(total: number): void {
    const debugTotal = document.getElementById('debug-total');
    if (debugTotal) {
      debugTotal.textContent = String(total);
    }
  }

  /**
   * Initialize keyboard shortcuts
   */
  public initKeyboardShortcuts(
    onToggleInfo: () => void,
    onNext: () => void,
    onReload: () => void
  ): void {
    document.addEventListener('keydown', (e: KeyboardEvent) => {
      // Press 'p' to toggle player info
      if (e.key === 'p' || e.key === 'P') {
        const info = document.getElementById('player-info');
        if (info) {
          info.style.display = info.style.display === 'none' ? 'block' : 'none';
        }
        onToggleInfo();
      }

      // Press 'n' to skip to next content
      if (e.key === 'n' || e.key === 'N') {
        SharedLogger.log('[PlayerUI] Manual skip to next');
        onNext();
      }

      // Press 'r' to reload playlist
      if (e.key === 'r' || e.key === 'R') {
        SharedLogger.log('[PlayerUI] Manual reload playlist');
        onReload();
      }

      // Press 's' to toggle schedule info
      if (e.key === 's' || e.key === 'S') {
        SharedLogger.log('[PlayerUI] Toggle schedule info');
        // Emit event via SharedEventBus
        SharedEventBus.emit('ui:toggle-schedule-info');
      }
    });
  }
}

// Export singleton instance
export const PlayerUI = PlayerUIManager.getInstance();
