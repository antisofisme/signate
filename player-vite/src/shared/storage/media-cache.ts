/**
 * Media Cache Module
 * Manages IndexedDB cache for offline media storage and retrieval
 */

import { SharedLogger } from '@shared/logger';
import { dbManager } from './indexed-db-manager';
import type { CachedMediaEntry, ContentCacheInfo, CacheSyncResult } from './media-cache.types';

class MediaCache {
  private readonly STORE_NAME = 'media_files';

  // Track active blob URLs for proper cleanup (prevent memory leak)
  private activeBlobUrls: Set<string> = new Set();

  /**
   * Initialize media cache database
   */
  async init(): Promise<void> {
    try {
      await dbManager.open();
      SharedLogger.log('[MediaCache] Initialized successfully');
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Check if content is cached
   */
  async isContentCached(contentId: number): Promise<boolean> {
    try {
      const cached = await dbManager.get<CachedMediaEntry>(this.STORE_NAME, contentId);
      return !!cached;
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to check cache for content ${contentId}:`, error);
      return false;
    }
  }

  /**
   * Get cached content entry
   */
  async getCachedContent(contentId: number): Promise<CachedMediaEntry | undefined> {
    try {
      return await dbManager.get<CachedMediaEntry>(this.STORE_NAME, contentId);
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to get cached content ${contentId}:`, error);
      return undefined;
    }
  }

  /**
   * Download and cache content
   */
  async downloadAndCacheContent(content: ContentCacheInfo): Promise<CachedMediaEntry | null> {
    try {
      SharedLogger.log(`[MediaCache] Downloading content ${content.content_id}: ${content.title}`);

      // Fetch content from URL
      const response = await fetch(content.url);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status}`);
      }

      // Get blob data
      const blob = await response.blob();
      const contentType =
        response.headers.get('content-type') || content.mime_type || 'application/octet-stream';

      // Store in IndexedDB
      const cacheEntry: CachedMediaEntry = {
        content_id: content.content_id,
        title: content.title,
        url: content.url,
        content_type: content.content_type,
        mime_type: contentType,
        blob: blob,
        size: blob.size,
        timestamp: Date.now(),
      };

      await this.saveToCache(cacheEntry);

      SharedLogger.log(
        `[MediaCache] Cached content ${content.content_id} (${(blob.size / 1024 / 1024).toFixed(2)} MB)`
      );
      return cacheEntry;
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to cache content ${content.content_id}:`, error);
      return null;
    }
  }

  /**
   * Save content to cache
   */
  async saveToCache(cacheEntry: CachedMediaEntry): Promise<void> {
    try {
      await dbManager.put(this.STORE_NAME, cacheEntry);
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to save to cache:', error);
      throw error;
    }
  }

  /**
   * Delete content from cache
   */
  async deleteFromCache(contentId: number): Promise<void> {
    try {
      await dbManager.delete(this.STORE_NAME, contentId);
      SharedLogger.log(`[MediaCache] Removed content ${contentId} from cache`);
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to delete content ${contentId}:`, error);
      throw error;
    }
  }

  /**
   * Get all cached content IDs
   */
  async getAllCachedContentIds(): Promise<number[]> {
    try {
      const allCached = await dbManager.getAll<CachedMediaEntry>(this.STORE_NAME);
      return allCached.map((entry) => entry.content_id);
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to get all cached content IDs:', error);
      return [];
    }
  }

  /**
   * Sync cache with playlist - download new content and remove unused
   */
  async syncCacheWithPlaylist(newPlaylist: ContentCacheInfo[]): Promise<CacheSyncResult> {
    const result: CacheSyncResult = {
      downloaded: 0,
      removed: 0,
      errors: 0,
    };

    try {
      // Get all cached content IDs
      const cachedIds = await this.getAllCachedContentIds();
      const playlistIds = newPlaylist.map((item) => item.content_id);

      // Find content to remove (in cache but not in playlist)
      const idsToRemove = cachedIds.filter((id) => !playlistIds.includes(id));

      // Find content to download (in playlist but not in cache)
      const idsToDownload = playlistIds.filter((id) => !cachedIds.includes(id));

      // Remove unused content from cache
      for (const id of idsToRemove) {
        try {
          await this.deleteFromCache(id);
          result.removed++;
        } catch (error) {
          SharedLogger.error(`[MediaCache] Failed to remove content ${id}:`, error);
          result.errors++;
        }
      }

      // Download new content
      for (const content of newPlaylist) {
        if (idsToDownload.includes(content.content_id)) {
          try {
            const cached = await this.downloadAndCacheContent(content);
            if (cached) {
              result.downloaded++;
            } else {
              result.errors++;
            }
          } catch (error) {
            SharedLogger.error(`[MediaCache] Failed to download content ${content.content_id}:`, error);
            result.errors++;
          }
        }
      }

      SharedLogger.log(
        `[MediaCache] Sync complete: +${result.downloaded} downloaded, -${result.removed} removed, ${result.errors} errors`
      );
    } catch (error) {
      SharedLogger.error('[MediaCache] Cache sync failed:', error);
    }

    return result;
  }

  /**
   * Get cached blob URL for playback
   * NOTE: All blob URLs are tracked and MUST be revoked via revokeAllBlobUrls()
   */
  async getCachedBlobUrl(contentId: number): Promise<string | null> {
    try {
      const cached = await this.getCachedContent(contentId);

      if (!cached) {
        return null;
      }

      // Create blob with correct MIME type for playback
      // This is critical for video playback - browser needs to know the video format
      const typedBlob = new Blob([cached.blob], { type: cached.mime_type });
      const blobUrl = URL.createObjectURL(typedBlob);

      // Track blob URL for cleanup
      this.activeBlobUrls.add(blobUrl);

      return blobUrl;
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to get cached blob URL for ${contentId}:`, error);
      return null;
    }
  }

  /**
   * Revoke a single blob URL to free memory
   */
  revokeBlobUrl(blobUrl: string): void {
    try {
      URL.revokeObjectURL(blobUrl);
      this.activeBlobUrls.delete(blobUrl);
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to revoke blob URL:', error);
    }
  }

  /**
   * Revoke all tracked blob URLs
   * IMPORTANT: Call this on content transition to prevent memory leaks
   */
  revokeAllBlobUrls(): void {
    const count = this.activeBlobUrls.size;
    if (count === 0) return;

    this.activeBlobUrls.forEach(url => {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {
        // Ignore - URL might already be revoked
      }
    });
    this.activeBlobUrls.clear();
    SharedLogger.log(`[MediaCache] 🧹 Revoked ${count} blob URLs`);
  }

  /**
   * Get count of active blob URLs (for debugging)
   */
  getActiveBlobUrlCount(): number {
    return this.activeBlobUrls.size;
  }

  /**
   * Clear all cache (for debugging/reset)
   */
  async clearAllCache(): Promise<void> {
    try {
      await dbManager.clear(this.STORE_NAME);
      SharedLogger.log('[MediaCache] All cache cleared');
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to clear all cache:', error);
      throw error;
    }
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<{
    totalItems: number;
    totalSize: number;
    oldestTimestamp: number;
    newestTimestamp: number;
  }> {
    try {
      const allCached = await dbManager.getAll<CachedMediaEntry>(this.STORE_NAME);

      const stats = {
        totalItems: allCached.length,
        totalSize: allCached.reduce((sum, entry) => sum + entry.size, 0),
        oldestTimestamp: Math.min(...allCached.map((entry) => entry.timestamp), Date.now()),
        newestTimestamp: Math.max(...allCached.map((entry) => entry.timestamp), 0),
      };

      return stats;
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to get cache stats:', error);
      return {
        totalItems: 0,
        totalSize: 0,
        oldestTimestamp: 0,
        newestTimestamp: 0,
      };
    }
  }

  /**
   * Clean up old cache entries
   * Removes entries older than maxAge (default: 7 days)
   * Also enforces maxSize limit (default: 500 MB)
   */
  async cleanupOldCache(options?: {
    maxAgeMs?: number;
    maxSizeBytes?: number;
  }): Promise<{
    removedByAge: number;
    removedBySize: number;
    freedBytes: number;
  }> {
    const {
      maxAgeMs = 7 * 24 * 60 * 60 * 1000, // 7 days default
      maxSizeBytes = 500 * 1024 * 1024, // 500 MB default
    } = options || {};

    const result = {
      removedByAge: 0,
      removedBySize: 0,
      freedBytes: 0,
    };

    try {
      const allCached = await dbManager.getAll<CachedMediaEntry>(this.STORE_NAME);
      const now = Date.now();

      // Sort by timestamp (oldest first)
      allCached.sort((a, b) => a.timestamp - b.timestamp);

      // Phase 1: Remove entries older than maxAge
      for (const entry of allCached) {
        const age = now - entry.timestamp;
        if (age > maxAgeMs) {
          try {
            await this.deleteFromCache(entry.content_id);
            result.removedByAge++;
            result.freedBytes += entry.size;
          } catch (error) {
            SharedLogger.error(`[MediaCache] Cleanup: Failed to remove old entry ${entry.content_id}:`, error);
          }
        }
      }

      // Phase 2: If still over size limit, remove oldest entries
      let currentSize = allCached.reduce((sum, entry) => sum + entry.size, 0) - result.freedBytes;

      if (currentSize > maxSizeBytes) {
        // Re-fetch remaining entries (after age cleanup)
        const remainingCached = await dbManager.getAll<CachedMediaEntry>(this.STORE_NAME);
        remainingCached.sort((a, b) => a.timestamp - b.timestamp);

        for (const entry of remainingCached) {
          if (currentSize <= maxSizeBytes) break;

          try {
            await this.deleteFromCache(entry.content_id);
            result.removedBySize++;
            result.freedBytes += entry.size;
            currentSize -= entry.size;
          } catch (error) {
            SharedLogger.error(`[MediaCache] Cleanup: Failed to remove oversized entry ${entry.content_id}:`, error);
          }
        }
      }

      if (result.removedByAge > 0 || result.removedBySize > 0) {
        SharedLogger.log(
          `[MediaCache] Cleanup complete: ` +
          `${result.removedByAge} old entries, ${result.removedBySize} size-limited, ` +
          `freed ${(result.freedBytes / 1024 / 1024).toFixed(2)} MB`
        );
      }
    } catch (error) {
      SharedLogger.error('[MediaCache] Cleanup failed:', error);
    }

    return result;
  }

  /**
   * Start periodic cache cleanup (runs every 24 hours)
   */
  private cleanupIntervalId: ReturnType<typeof setInterval> | null = null;

  startPeriodicCleanup(intervalMs: number = 24 * 60 * 60 * 1000): void {
    // Clear existing interval if any
    if (this.cleanupIntervalId) {
      clearInterval(this.cleanupIntervalId);
    }

    // Run initial cleanup
    this.cleanupOldCache().catch((error) => {
      SharedLogger.error('[MediaCache] Initial cleanup failed:', error);
    });

    // Schedule periodic cleanup
    this.cleanupIntervalId = setInterval(() => {
      this.cleanupOldCache().catch((error) => {
        SharedLogger.error('[MediaCache] Periodic cleanup failed:', error);
      });
    }, intervalMs);

    SharedLogger.log(`[MediaCache] Periodic cleanup scheduled (every ${intervalMs / 1000 / 60 / 60} hours)`);
  }

  /**
   * Stop periodic cache cleanup
   */
  stopPeriodicCleanup(): void {
    if (this.cleanupIntervalId) {
      clearInterval(this.cleanupIntervalId);
      this.cleanupIntervalId = null;
      SharedLogger.log('[MediaCache] Periodic cleanup stopped');
    }
  }
}

// Export singleton instance
export const mediaCache = new MediaCache();

// Export class for testing
export { MediaCache };
