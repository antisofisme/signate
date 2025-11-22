/**
 * Version Checker Service
 * Automatically detects when player is rebuilt and triggers reload with cache clear
 *
 * How it works:
 * 1. On build, Vite generates version.json with build timestamp
 * 2. Player polls version.json every 30 seconds
 * 3. If version changes, clears cache and reloads
 * 4. Does NOT affect device registration or organization assignment
 */

import { SharedLogger } from '@shared/logger';

interface VersionInfo {
  buildTime: string;
  buildTimestamp: number;
}

class VersionCheckerClass {
  private currentVersion: VersionInfo | null = null;
  private checkInterval: number | null = null;
  private readonly CHECK_INTERVAL_MS = 30 * 1000; // Check every 30 seconds
  private readonly VERSION_URL = '/version.json';

  /**
   * Initialize version checker
   */
  async init(): Promise<void> {
    try {
      // Get initial version
      this.currentVersion = await this.fetchVersion();

      if (this.currentVersion) {
        SharedLogger.log(`[VersionChecker] Initialized with build: ${this.currentVersion.buildTime}`);

        // Start polling for version changes
        this.startPolling();
      } else {
        SharedLogger.warn('[VersionChecker] Could not fetch initial version, polling disabled');
      }
    } catch (error) {
      SharedLogger.error('[VersionChecker] Failed to initialize:', error);
    }
  }

  /**
   * Fetch version info from server
   */
  private async fetchVersion(): Promise<VersionInfo | null> {
    try {
      // Add cache-busting query param
      const response = await fetch(`${this.VERSION_URL}?t=${Date.now()}`, {
        cache: 'no-store'
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      // Version file might not exist yet
      return null;
    }
  }

  /**
   * Start polling for version changes
   */
  private startPolling(): void {
    this.checkInterval = window.setInterval(async () => {
      await this.checkForUpdate();
    }, this.CHECK_INTERVAL_MS);

    SharedLogger.log(`[VersionChecker] Polling started (every ${this.CHECK_INTERVAL_MS / 1000}s)`);
  }

  /**
   * Check if new version is available
   */
  private async checkForUpdate(): Promise<void> {
    const newVersion = await this.fetchVersion();

    if (!newVersion || !this.currentVersion) {
      return;
    }

    // Compare timestamps
    if (newVersion.buildTimestamp !== this.currentVersion.buildTimestamp) {
      SharedLogger.warn(`[VersionChecker] New version detected!`);
      SharedLogger.warn(`[VersionChecker] Current: ${this.currentVersion.buildTime}`);
      SharedLogger.warn(`[VersionChecker] New: ${newVersion.buildTime}`);

      // Trigger reload with cache clear
      await this.reloadWithCacheClear();
    }
  }

  /**
   * Clear caches and reload page
   * Does NOT affect device registration or IndexedDB data
   */
  private async reloadWithCacheClear(): Promise<void> {
    SharedLogger.log('[VersionChecker] Clearing caches and reloading...');

    try {
      // 1. Clear Service Worker caches (if any)
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.map(name => caches.delete(name))
        );
        SharedLogger.log('[VersionChecker] Service worker caches cleared');
      }

      // 2. Unregister service workers (if any)
      if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(
          registrations.map(reg => reg.unregister())
        );
        SharedLogger.log('[VersionChecker] Service workers unregistered');
      }

      // 3. Clear media caches from IndexedDB (player-media-cache)
      // but keep device registration data (player-device, player-connection-logs)
      try {
        const mediaDBRequest = indexedDB.deleteDatabase('player-media-cache');
        mediaDBRequest.onsuccess = () => {
          SharedLogger.log('[VersionChecker] Media cache cleared');
        };
      } catch (e) {
        // Ignore if database doesn't exist
      }

      // 4. Hard reload (bypass browser cache)
      // Use replace to not add to history
      window.location.replace(window.location.href.split('?')[0] + '?v=' + Date.now());

    } catch (error) {
      SharedLogger.error('[VersionChecker] Error during cache clear:', error);
      // Fallback: simple reload
      window.location.reload();
    }
  }

  /**
   * Stop polling (for cleanup)
   */
  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
      SharedLogger.log('[VersionChecker] Polling stopped');
    }
  }

  /**
   * Get current version info
   */
  getVersion(): VersionInfo | null {
    return this.currentVersion;
  }

  /**
   * Force check for update (can be called manually)
   */
  async forceCheck(): Promise<void> {
    SharedLogger.log('[VersionChecker] Force check triggered');
    await this.checkForUpdate();
  }
}

// Export singleton instance
export const VersionChecker = new VersionCheckerClass();

// Make available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).VersionChecker = VersionChecker;
}
