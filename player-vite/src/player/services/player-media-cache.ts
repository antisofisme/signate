/**
 * Player Media Cache Service
 * Manages IndexedDB cache for offline content playback
 *
 * @features
 * - IndexedDB-based caching for videos, images, and files
 * - Smart cache management with size limits
 * - Automatic cache warming from playlist
 * - Cache invalidation and cleanup
 * - Type-safe with TypeScript
 */

import { SharedLogger } from '@shared/logger';
import type { PlayerMediaCache as IPlayerMediaCache, CachedMedia, CacheStats } from '../types/player.types';

/**
 * Player Media Cache Class
 * Singleton pattern for media caching
 */
class PlayerMediaCacheClass implements IPlayerMediaCache {
  private dbName = 'signage_media_cache';
  private dbVersion = 1;
  private storeName = 'media';
  private db: IDBDatabase | null = null;

  /**
   * Initialize IndexedDB
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        SharedLogger.log('[PlayerMediaCache] ✅ IndexedDB initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(this.storeName)) {
          const objectStore = db.createObjectStore(this.storeName, { keyPath: 'url' });
          objectStore.createIndex('contentId', 'contentId', { unique: false });
          objectStore.createIndex('cachedAt', 'cachedAt', { unique: false });
          objectStore.createIndex('lastAccessed', 'lastAccessed', { unique: false });
          SharedLogger.log('[PlayerMediaCache] Object store created');
        }
      };
    });
  }

  /**
   * Cache media from URL
   */
  async cacheMedia(url: string, contentId: number): Promise<void> {
    if (!this.db) {
      SharedLogger.warn('[PlayerMediaCache] DB not initialized');
      return;
    }

    try {
      // Check if already cached
      const existing = await this.getCachedMedia(url);
      if (existing) {
        SharedLogger.log(`[PlayerMediaCache] Media already cached: ${url}`);
        // Update last accessed
        await this.updateLastAccessed(url);
        return;
      }

      SharedLogger.log(`[PlayerMediaCache] 📥 Caching media: ${url}`);

      // Download media
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      const arrayBuffer = await blob.arrayBuffer();

      // Store in IndexedDB
      const cachedMedia: CachedMedia = {
        url,
        contentId,
        data: arrayBuffer,
        mimeType: blob.type,
        size: blob.size,
        cachedAt: new Date().toISOString(),
        lastAccessed: new Date().toISOString(),
      };

      await this.putMedia(cachedMedia);
      SharedLogger.log(`[PlayerMediaCache] ✅ Cached ${(blob.size / 1024 / 1024).toFixed(2)} MB: ${url}`);
    } catch (error) {
      SharedLogger.error(`[PlayerMediaCache] ❌ Failed to cache ${url}:`, error);
      throw error;
    }
  }

  /**
   * Get cached media by URL
   */
  async getCachedMedia(url: string): Promise<CachedMedia | null> {
    if (!this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.get(url);

      request.onsuccess = () => {
        resolve(request.result || null);
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to get cached media:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get cached media as Blob URL
   */
  async getCachedBlobURL(url: string): Promise<string | null> {
    const cached = await this.getCachedMedia(url);
    if (!cached) return null;

    // Update last accessed
    await this.updateLastAccessed(url);

    // Create Blob URL
    const blob = new Blob([cached.data], { type: cached.mimeType });
    return URL.createObjectURL(blob);
  }

  /**
   * Check if media is cached
   */
  async isCached(url: string): Promise<boolean> {
    const cached = await this.getCachedMedia(url);
    return cached !== null;
  }

  /**
   * Delete cached media
   */
  async deleteMedia(url: string): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.delete(url);

      request.onsuccess = () => {
        SharedLogger.log(`[PlayerMediaCache] 🗑️ Deleted cache: ${url}`);
        resolve();
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to delete cached media:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Clear all cached media
   */
  async clearCache(): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.clear();

      request.onsuccess = () => {
        SharedLogger.log('[PlayerMediaCache] 🗑️ All cache cleared');
        resolve();
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to clear cache:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<CacheStats> {
    if (!this.db) {
      return { totalItems: 0, totalSize: 0, oldestCache: null, newestCache: null };
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.getAll();

      request.onsuccess = () => {
        const items: CachedMedia[] = request.result;
        const totalSize = items.reduce((sum, item) => sum + item.size, 0);
        const sortedByDate = items.sort((a, b) =>
          new Date(a.cachedAt).getTime() - new Date(b.cachedAt).getTime()
        );

        const stats: CacheStats = {
          totalItems: items.length,
          totalSize,
          oldestCache: sortedByDate[0]?.cachedAt || null,
          newestCache: sortedByDate[sortedByDate.length - 1]?.cachedAt || null,
        };

        SharedLogger.log('[PlayerMediaCache] 📊 Cache stats:', {
          ...stats,
          totalSizeMB: (totalSize / 1024 / 1024).toFixed(2) + ' MB',
        });

        resolve(stats);
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to get cache stats:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Cleanup old cache based on LRU (Least Recently Used)
   */
  async cleanupOldCache(maxItems = 50, maxSizeMB = 500): Promise<void> {
    if (!this.db) return;

    const stats = await this.getCacheStats();
    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    SharedLogger.log('[PlayerMediaCache] 🧹 Running cache cleanup...', {
      currentItems: stats.totalItems,
      currentSizeMB: (stats.totalSize / 1024 / 1024).toFixed(2),
      maxItems,
      maxSizeMB,
    });

    if (stats.totalItems <= maxItems && stats.totalSize <= maxSizeBytes) {
      SharedLogger.log('[PlayerMediaCache] No cleanup needed');
      return;
    }

    // Get all items sorted by last accessed (oldest first)
    const transaction = this.db.transaction([this.storeName], 'readwrite');
    const objectStore = transaction.objectStore(this.storeName);
    const index = objectStore.index('lastAccessed');
    const request = index.openCursor();

    let deletedItems = 0;
    let deletedSize = 0;

    return new Promise((resolve, reject) => {
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (!cursor) {
          SharedLogger.log(`[PlayerMediaCache] ✅ Cleanup complete: Deleted ${deletedItems} items (${(deletedSize / 1024 / 1024).toFixed(2)} MB)`);
          resolve();
          return;
        }

        const item: CachedMedia = cursor.value;

        // Delete if over limits
        if (stats.totalItems - deletedItems > maxItems || stats.totalSize - deletedSize > maxSizeBytes) {
          cursor.delete();
          deletedItems++;
          deletedSize += item.size;
          SharedLogger.log(`[PlayerMediaCache] Deleted: ${item.url} (${(item.size / 1024 / 1024).toFixed(2)} MB)`);
        }

        cursor.continue();
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Cleanup failed:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Store media in IndexedDB
   */
  private async putMedia(media: CachedMedia): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.put(media);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        SharedLogger.error('[PlayerMediaCache] Failed to put media:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Update last accessed timestamp
   */
  private async updateLastAccessed(url: string): Promise<void> {
    const cached = await this.getCachedMedia(url);
    if (!cached) return;

    cached.lastAccessed = new Date().toISOString();
    await this.putMedia(cached);
  }
}

// Export singleton instance
export const PlayerMediaCache = new PlayerMediaCacheClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.PlayerMediaCache = PlayerMediaCache;
}
