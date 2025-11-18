/**
 * Clear Cache Handler
 * Handles clearing cached media content while preserving device registration
 */

import { SharedLogger } from '@shared/logger';
import { SharedToast, SharedModal } from '@shared/ui';
import { getPlayerMediaCache } from '@shared/services';

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
      let clearedItems = 0;

      // Clear IndexedDB media cache
      try {
        const mediaCache = getPlayerMediaCache();
        if (mediaCache && typeof mediaCache.clearCache === 'function') {
          await mediaCache.clearCache();
          clearedItems++;
          SharedLogger.success('[ClearCache] Media cache cleared');
        } else {
          SharedLogger.warn('[ClearCache] Media cache not available or missing clearCache method');
        }
      } catch (err) {
        SharedLogger.error('[ClearCache] Error clearing media cache:', err);
      }

      // Clear Cache API if available
      try {
        if ('caches' in window) {
          const cacheNames = await caches.keys();
          SharedLogger.log(`[ClearCache] Found ${cacheNames.length} cache(s) to delete`);

          for (const cacheName of cacheNames) {
            const deleted = await caches.delete(cacheName);
            if (deleted) {
              clearedItems++;
              SharedLogger.success(`[ClearCache] Deleted cache: ${cacheName}`);
            } else {
              SharedLogger.warn(`[ClearCache] Failed to delete cache: ${cacheName}`);
            }
          }
        } else {
          SharedLogger.warn('[ClearCache] Cache API not available in this browser');
        }
      } catch (err) {
        SharedLogger.error('[ClearCache] Error clearing Cache API:', err);
      }

      // Clear localStorage (optional - preserve device registration)
      try {
        const keysToPreserve = ['device_id', 'device_token', 'activation_code', 'device_uuid'];
        const preservedData: Record<string, string> = {};

        // Backup critical keys
        keysToPreserve.forEach(key => {
          const value = localStorage.getItem(key);
          if (value) preservedData[key] = value;
        });

        // Clear all
        const storageLength = localStorage.length;
        localStorage.clear();
        clearedItems++;

        // Restore critical keys
        Object.entries(preservedData).forEach(([key, value]) => {
          localStorage.setItem(key, value);
        });

        SharedLogger.success(`[ClearCache] Cleared ${storageLength} localStorage items (preserved device data)`);
      } catch (err) {
        SharedLogger.error('[ClearCache] Error clearing localStorage:', err);
      }

      // Summary
      if (clearedItems > 0) {
        SharedLogger.success(`[ClearCache] ✅ Successfully cleared ${clearedItems} cache type(s)`);
        SharedToast.success(`Cache cleared successfully! (${clearedItems} items)`, 3000);

        // Reload page after delay
        setTimeout(() => {
          SharedLogger.log('[ClearCache] Reloading page...');
          window.location.reload();
        }, 1500);
      } else {
        SharedLogger.warn('[ClearCache] ⚠️ No cache items were cleared');
        SharedToast.warning('No cache to clear', 3000);
      }

    } catch (error) {
      SharedLogger.error('[ClearCache] ❌ Fatal error:', error);
      SharedToast.error(`Failed to clear cache: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

// Export singleton
export const ClearCacheHandler = new ClearCacheHandlerClass();

// Make available globally
if (typeof window !== 'undefined') {
  (window as any).ClearCacheHandler = ClearCacheHandler;
}
