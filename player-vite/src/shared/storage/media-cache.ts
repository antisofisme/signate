/**
 * Media Cache Module
 * Manages IndexedDB cache for offline media storage and retrieval
 */

import { SharedLogger } from '@shared/logger';
import { dbManager } from './indexed-db-manager';
import type { CachedMediaEntry, ContentCacheInfo, CacheSyncResult } from './media-cache.types';

class MediaCache {
  private readonly STORE_NAME = 'media_files';

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
      return blobUrl;
    } catch (error) {
      SharedLogger.error(`[MediaCache] Failed to get cached blob URL for ${contentId}:`, error);
      return null;
    }
  }

  /**
   * Revoke blob URL to free memory
   */
  revokeBlobUrl(blobUrl: string): void {
    try {
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      SharedLogger.error('[MediaCache] Failed to revoke blob URL:', error);
    }
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
}

// Export singleton instance
export const mediaCache = new MediaCache();

// Export class for testing
export { MediaCache };
