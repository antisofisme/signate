/**
 * Clear Cache Handler
 * Handles clearing cached media content while preserving device registration
 */

import { SharedLogger } from '@shared/logger';
import { SharedToast, SharedModal } from '@shared/ui';
import { getPlayerMediaCache, getShellBootstrap } from '@shared/services';

class ClearCacheHandlerClass {
  private button: HTMLButtonElement | null = null;

  /**
   * Initialize clear cache handler
   */
  init(): void {
    this.button = document.getElementById('clear-cache-btn') as HTMLButtonElement;

    if (!this.button) {
      SharedLogger.warn('[ClearCache] Button not found');
      return;
    }

    // Open confirmation dialog on button click
    this.button.addEventListener('click', () => {
      this.showConfirmDialog();
    });

    SharedLogger.log('[ClearCache] ✅ Initialized');
  }

  /**
   * Show confirmation dialog using SharedModal
   */
  private async showConfirmDialog(): Promise<void> {
    const confirmed = await SharedModal.confirm(
      'Clear Media Cache',
      'Are you sure you want to clear all cached media? This will free up storage but media will need to be downloaded again.',
      'Clear Cache',
      'Cancel'
    );

    if (confirmed) {
      await this.handleClearCache();
    }
  }

  /**
   * Handle clear cache action
   */
  private async handleClearCache(): Promise<void> {
    try {
      SharedLogger.log('[ClearCache] Starting cache clear...');

      // Clear IndexedDB media cache
      if (getPlayerMediaCache()) {
        await getPlayerMediaCache().clearAll();
        SharedLogger.log('[ClearCache] ✅ Media cache cleared');
      }

      // Clear Cache API if available
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        for (const cacheName of cacheNames) {
          await caches.delete(cacheName);
          SharedLogger.log(`[ClearCache] ✅ Deleted cache: ${cacheName}`);
        }
      }

      SharedLogger.log('[ClearCache] ✅ Cache cleared successfully, reloading player...');

      // Show success toast
      SharedToast.success('Cache cleared successfully! Reloading player...', 4000);

      // Reload player services only (not full page) after delay
      setTimeout(async () => {
        if (getShellBootstrap()?.reloadPlayerServices) {
          await getShellBootstrap().reloadPlayerServices();
          SharedToast.success('Player reloaded successfully!', 3000);
        } else {
          // Fallback to full reload if method not available
          SharedLogger.warn('[ClearCache] reloadPlayerServices not available, using full reload');
          window.location.reload();
        }
      }, 1500);

    } catch (error) {
      SharedLogger.error('[ClearCache] ❌ Error clearing cache:', error);
      SharedToast.error('Failed to clear cache. Please try again.');
    }
  }
}

// Export singleton
export const ClearCacheHandler = new ClearCacheHandlerClass();

// Make available globally
if (typeof window !== 'undefined') {
  (window as any).ClearCacheHandler = ClearCacheHandler;
}
