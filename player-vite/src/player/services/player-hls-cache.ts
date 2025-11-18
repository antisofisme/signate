/**
 * Player HLS Cache Service
 * Manages caching of HLS manifests and segments for offline playback
 *
 * @features
 * - Parse HLS master and variant playlists
 * - Download and cache all segments to IndexedDB
 * - Create blob URLs for offline playback
 * - Support adaptive bitrate variants
 * - Smart cache management
 */

import { SharedLogger } from '@shared/logger';
import { ServiceRegistry } from '@shared/services/service-registry';

interface HLSVariant {
  quality: string; // '360p', '480p', '720p', '1080p'
  bandwidth: number;
  resolution: string;
  playlistUrl: string;
}

interface HLSSegment {
  segmentUrl: string;
  duration: number;
  index: number;
}

interface CachedHLSContent {
  contentId: number;
  masterPlaylistUrl: string;
  variants: HLSVariant[];
  selectedQuality: string;
  segments: {
    [quality: string]: HLSSegment[];
  };
  cachedAt: string;
}

/**
 * HLS Cache Service Class
 * Singleton pattern for HLS caching
 */
class PlayerHLSCacheClass {
  private dbName = 'signage_hls_cache';
  private dbVersion = 1;
  private storeName = 'hls_segments';
  private metaStore = 'hls_metadata';
  private db: IDBDatabase | null = null;

  /**
   * Initialize IndexedDB for HLS caching
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        SharedLogger.error('[PlayerHLSCache] Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        SharedLogger.log('[PlayerHLSCache] ✅ IndexedDB initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Store for HLS segments (binary data)
        if (!db.objectStoreNames.contains(this.storeName)) {
          const segmentStore = db.createObjectStore(this.storeName, { keyPath: 'key' });
          segmentStore.createIndex('contentId', 'contentId', { unique: false });
          segmentStore.createIndex('quality', 'quality', { unique: false });
          SharedLogger.log('[PlayerHLSCache] Segment store created');
        }

        // Store for HLS metadata (playlists, variants)
        if (!db.objectStoreNames.contains(this.metaStore)) {
          const metaStore = db.createObjectStore(this.metaStore, { keyPath: 'contentId' });
          metaStore.createIndex('masterPlaylistUrl', 'masterPlaylistUrl', { unique: false });
          SharedLogger.log('[PlayerHLSCache] Metadata store created');
        }
      };
    });
  }

  /**
   * Parse HLS master playlist to extract variants
   */
  private async parseMasterPlaylist(masterUrl: string): Promise<HLSVariant[]> {
    try {
      const response = await fetch(masterUrl);
      const text = await response.text();
      const lines = text.split('\n');

      const variants: HLSVariant[] = [];
      let currentVariant: Partial<HLSVariant> = {};

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Parse #EXT-X-STREAM-INF line
        if (line.startsWith('#EXT-X-STREAM-INF:')) {
          const attrs = line.substring('#EXT-X-STREAM-INF:'.length);

          // Extract bandwidth
          const bandwidthMatch = attrs.match(/BANDWIDTH=(\d+)/);
          if (bandwidthMatch) {
            currentVariant.bandwidth = parseInt(bandwidthMatch[1], 10);
          }

          // Extract resolution
          const resolutionMatch = attrs.match(/RESOLUTION=(\d+x\d+)/);
          if (resolutionMatch) {
            currentVariant.resolution = resolutionMatch[1];
          }

          // Next line should be the playlist URL
          if (i + 1 < lines.length) {
            const nextLine = lines[i + 1].trim();
            if (nextLine && !nextLine.startsWith('#')) {
              // Extract quality from path (e.g., "360p/playlist.m3u8" -> "360p")
              const qualityMatch = nextLine.match(/^(\d+p)\//);
              currentVariant.quality = qualityMatch ? qualityMatch[1] : 'unknown';

              // Construct full URL (relative to master playlist)
              const baseUrl = masterUrl.substring(0, masterUrl.lastIndexOf('/') + 1);
              currentVariant.playlistUrl = baseUrl + nextLine;

              variants.push(currentVariant as HLSVariant);
              currentVariant = {};
            }
          }
        }
      }

      SharedLogger.log(`[PlayerHLSCache] Parsed ${variants.length} variants:`, variants.map(v => v.quality));
      return variants;
    } catch (error) {
      SharedLogger.error('[PlayerHLSCache] Failed to parse master playlist:', error);
      throw error;
    }
  }

  /**
   * Parse variant playlist to extract segments
   */
  private async parseVariantPlaylist(playlistUrl: string): Promise<HLSSegment[]> {
    try {
      const response = await fetch(playlistUrl);
      const text = await response.text();
      const lines = text.split('\n');

      const segments: HLSSegment[] = [];
      let currentDuration = 6.0; // Default 6 seconds
      let segmentIndex = 0;

      const baseUrl = playlistUrl.substring(0, playlistUrl.lastIndexOf('/') + 1);

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Parse #EXTINF (segment duration)
        if (line.startsWith('#EXTINF:')) {
          const durationMatch = line.match(/#EXTINF:([\d.]+)/);
          if (durationMatch) {
            currentDuration = parseFloat(durationMatch[1]);
          }
        }

        // Segment file (ends with .ts)
        if (line.endsWith('.ts')) {
          segments.push({
            segmentUrl: baseUrl + line,
            duration: currentDuration,
            index: segmentIndex++,
          });
        }
      }

      SharedLogger.log(`[PlayerHLSCache] Parsed ${segments.length} segments from playlist`);
      return segments;
    } catch (error) {
      SharedLogger.error('[PlayerHLSCache] Failed to parse variant playlist:', error);
      throw error;
    }
  }

  /**
   * Download and cache a single segment
   */
  private async cacheSegment(
    contentId: number,
    quality: string,
    segment: HLSSegment
  ): Promise<void> {
    if (!this.db) return;

    try {
      const response = await fetch(segment.segmentUrl);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const arrayBuffer = await response.arrayBuffer();

      // Store segment with composite key
      const key = `${contentId}_${quality}_${segment.index}`;
      const data = {
        key,
        contentId,
        quality,
        segmentIndex: segment.index,
        segmentUrl: segment.segmentUrl,
        data: arrayBuffer,
        size: arrayBuffer.byteLength,
        cachedAt: new Date().toISOString(),
      };

      await this.putSegment(data);
      SharedLogger.log(
        `[PlayerHLSCache] ✅ Cached segment ${segment.index} (${(arrayBuffer.byteLength / 1024).toFixed(1)} KB)`
      );
    } catch (error) {
      SharedLogger.error(`[PlayerHLSCache] ❌ Failed to cache segment ${segment.index}:`, error);
      throw error;
    }
  }

  /**
   * Cache entire HLS content (all variants and segments)
   */
  async cacheHLSContent(contentId: number, masterPlaylistUrl: string): Promise<void> {
    if (!this.db) {
      SharedLogger.warn('[PlayerHLSCache] DB not initialized');
      return;
    }

    try {
      SharedLogger.log(`[PlayerHLSCache] 📥 Starting HLS cache for content ${contentId}`);
      SharedLogger.log(`[PlayerHLSCache] Master playlist: ${masterPlaylistUrl}`);

      // 1. Parse master playlist to get variants
      const variants = await this.parseMasterPlaylist(masterPlaylistUrl);
      if (variants.length === 0) {
        throw new Error('No variants found in master playlist');
      }

      // 2. Select best quality (highest bandwidth)
      const selectedVariant = variants.reduce((prev, current) =>
        current.bandwidth > prev.bandwidth ? current : prev
      );
      SharedLogger.log(`[PlayerHLSCache] Selected quality: ${selectedVariant.quality} (${selectedVariant.bandwidth} bps)`);

      // 3. Parse variant playlist to get segments
      const segments = await this.parseVariantPlaylist(selectedVariant.playlistUrl);
      if (segments.length === 0) {
        throw new Error('No segments found in variant playlist');
      }

      // 4. Download and cache all segments
      SharedLogger.log(`[PlayerHLSCache] Downloading ${segments.length} segments...`);
      let cachedCount = 0;

      for (const segment of segments) {
        await this.cacheSegment(contentId, selectedVariant.quality, segment);
        cachedCount++;

        // Log progress every 5 segments
        if (cachedCount % 5 === 0) {
          SharedLogger.log(`[PlayerHLSCache] Progress: ${cachedCount}/${segments.length} segments cached`);
        }
      }

      // 5. Store metadata
      const metadata: CachedHLSContent = {
        contentId,
        masterPlaylistUrl,
        variants,
        selectedQuality: selectedVariant.quality,
        segments: {
          [selectedVariant.quality]: segments,
        },
        cachedAt: new Date().toISOString(),
      };

      await this.putMetadata(metadata);

      SharedLogger.log(`[PlayerHLSCache] ✅ HLS cache complete for content ${contentId}`);
      SharedLogger.log(`[PlayerHLSCache] Cached ${cachedCount} segments, quality: ${selectedVariant.quality}`);
    } catch (error) {
      SharedLogger.error(`[PlayerHLSCache] ❌ Failed to cache HLS content ${contentId}:`, error);
      throw error;
    }
  }

  /**
   * Check if HLS content is fully cached
   */
  async isHLSCached(contentId: number): Promise<boolean> {
    if (!this.db) return false;

    const metadata = await this.getMetadata(contentId);
    return metadata !== null;
  }

  /**
   * Get all cached segments for a content (for offline playback)
   * Returns segments sorted by index
   */
  async getSegments(contentId: number): Promise<Array<{ index: number; data: ArrayBuffer; duration: number }>> {
    if (!this.db) return [];

    try {
      // Get metadata to know which quality and how many segments
      const metadata = await this.getMetadata(contentId);
      if (!metadata) {
        SharedLogger.warn(`[PlayerHLSCache] No cached metadata for content ${contentId}`);
        return [];
      }

      const quality = metadata.selectedQuality;
      const segmentInfos = metadata.segments[quality];

      if (!segmentInfos || segmentInfos.length === 0) {
        SharedLogger.warn(`[PlayerHLSCache] No segments found for quality ${quality}`);
        return [];
      }

      SharedLogger.log(`[PlayerHLSCache] Loading ${segmentInfos.length} segments for content ${contentId} (${quality})`);

      // Load all segments from IndexedDB
      const segments: Array<{ index: number; data: ArrayBuffer; duration: number }> = [];

      for (const segInfo of segmentInfos) {
        const key = `${contentId}_${quality}_${segInfo.index}`;
        const segmentData = await this.getSegment(key);

        if (segmentData && segmentData.data) {
          segments.push({
            index: segInfo.index,
            data: segmentData.data,
            duration: segInfo.duration || 6.0,
          });
        } else {
          SharedLogger.warn(`[PlayerHLSCache] Missing segment ${segInfo.index} for content ${contentId}`);
        }
      }

      // Sort by index to ensure correct playback order
      segments.sort((a, b) => a.index - b.index);

      SharedLogger.log(`[PlayerHLSCache] ✅ Loaded ${segments.length} segments from cache`);
      return segments;
    } catch (error) {
      SharedLogger.error(`[PlayerHLSCache] Failed to get segments for content ${contentId}:`, error);
      return [];
    }
  }

  /**
   * Get single segment from IndexedDB
   */
  private async getSegment(key: string): Promise<any> {
    if (!this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.get(key);

      request.onsuccess = () => {
        resolve(request.result || null);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Check if cached content is stale (needs refresh)
   * Uses hybrid approach: URL-based + Timestamp-based validation
   */
  async isCacheStale(contentId: number, currentUrl: string, serverUpdatedAt?: string): Promise<boolean> {
    if (!this.db) return false;

    try {
      const metadata = await this.getMetadata(contentId);
      if (!metadata) {
        // No cache found, not stale (will download fresh)
        return false;
      }

      // Check 1: URL changed? (UUID changed on re-upload)
      if (metadata.masterPlaylistUrl !== currentUrl) {
        SharedLogger.log(`[PlayerHLSCache] 🔄 URL changed for content ${contentId}`);
        SharedLogger.log(`[PlayerHLSCache]    Old: ${metadata.masterPlaylistUrl}`);
        SharedLogger.log(`[PlayerHLSCache]    New: ${currentUrl}`);
        return true;
      }

      // Check 2: Server updated after cached? (Timestamp-based)
      if (serverUpdatedAt) {
        const serverDate = new Date(serverUpdatedAt);
        const cachedDate = new Date(metadata.cachedAt);

        if (serverDate > cachedDate) {
          SharedLogger.log(`[PlayerHLSCache] 🔄 Content ${contentId} updated on server`);
          SharedLogger.log(`[PlayerHLSCache]    Server: ${serverDate.toISOString()}`);
          SharedLogger.log(`[PlayerHLSCache]    Cached: ${cachedDate.toISOString()}`);
          return true;
        }
      }

      // Cache is fresh
      SharedLogger.log(`[PlayerHLSCache] ✅ Cache fresh for content ${contentId}`);
      return false;
    } catch (error) {
      SharedLogger.error(`[PlayerHLSCache] Failed to check cache staleness:`, error);
      return false;
    }
  }

  /**
   * Clear cached content (segments + metadata)
   * Used when content is updated on server
   */
  async clearCache(contentId: number): Promise<void> {
    if (!this.db) return;

    try {
      SharedLogger.log(`[PlayerHLSCache] 🗑️ Clearing cache for content ${contentId}`);

      // Get metadata to know which segments to delete
      const metadata = await this.getMetadata(contentId);
      if (!metadata) {
        SharedLogger.warn(`[PlayerHLSCache] No metadata found for content ${contentId}`);
        return;
      }

      const quality = metadata.selectedQuality;
      const segments = metadata.segments[quality];

      // Delete all segments
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);

      for (const segment of segments) {
        const key = `${contentId}_${quality}_${segment.index}`;
        store.delete(key);
      }

      await new Promise<void>((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });

      // Delete metadata
      const metaTransaction = this.db.transaction([this.metaStore], 'readwrite');
      const metaStore = metaTransaction.objectStore(this.metaStore);
      metaStore.delete(contentId);

      await new Promise<void>((resolve, reject) => {
        metaTransaction.oncomplete = () => resolve();
        metaTransaction.onerror = () => reject(metaTransaction.error);
      });

      SharedLogger.log(`[PlayerHLSCache] ✅ Cache cleared for content ${contentId}`);
    } catch (error) {
      SharedLogger.error(`[PlayerHLSCache] Failed to clear cache for content ${contentId}:`, error);
      throw error;
    }
  }

  /**
   * Get cached HLS metadata
   */
  private async getMetadata(contentId: number): Promise<CachedHLSContent | null> {
    if (!this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.metaStore], 'readonly');
      const objectStore = transaction.objectStore(this.metaStore);
      const request = objectStore.get(contentId);

      request.onsuccess = () => {
        resolve(request.result || null);
      };

      request.onerror = () => {
        SharedLogger.error('[PlayerHLSCache] Failed to get metadata:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Store segment in IndexedDB
   */
  private async putSegment(data: any): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const objectStore = transaction.objectStore(this.storeName);
      const request = objectStore.put(data);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        SharedLogger.error('[PlayerHLSCache] Failed to put segment:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Store metadata in IndexedDB
   */
  private async putMetadata(metadata: CachedHLSContent): Promise<void> {
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.metaStore], 'readwrite');
      const objectStore = transaction.objectStore(this.metaStore);
      const request = objectStore.put(metadata);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        SharedLogger.error('[PlayerHLSCache] Failed to put metadata:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Clear HLS cache for specific content
   */
  async clearHLSCache(contentId: number): Promise<void> {
    if (!this.db) return;

    try {
      // Delete metadata
      const metaTx = this.db.transaction([this.metaStore], 'readwrite');
      const metaStore = metaTx.objectStore(this.metaStore);
      await new Promise<void>((resolve, reject) => {
        const request = metaStore.delete(contentId);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });

      // Delete all segments for this content
      const segmentTx = this.db.transaction([this.storeName], 'readwrite');
      const segmentStore = segmentTx.objectStore(this.storeName);
      const index = segmentStore.index('contentId');
      const range = IDBKeyRange.only(contentId);

      await new Promise<void>((resolve, reject) => {
        const request = index.openCursor(range);
        request.onsuccess = (event) => {
          const cursor = (event.target as IDBRequest).result;
          if (cursor) {
            cursor.delete();
            cursor.continue();
          } else {
            resolve();
          }
        };
        request.onerror = () => reject(request.error);
      });

      SharedLogger.log(`[PlayerHLSCache] 🗑️ Cleared HLS cache for content ${contentId}`);
    } catch (error) {
      SharedLogger.error('[PlayerHLSCache] Failed to clear HLS cache:', error);
      throw error;
    }
  }

  /**
   * Get all cached content metadata
   * Used by Device Info popup to display cached content list
   */
  async getAllCachedContent(): Promise<CachedHLSContent[]> {
    if (!this.db) {
      SharedLogger.warn('[PlayerHLSCache] Database not initialized');
      return [];
    }

    try {
      const transaction = this.db.transaction([this.metaStore], 'readonly');
      const store = transaction.objectStore(this.metaStore);

      return new Promise<CachedHLSContent[]>((resolve, reject) => {
        const request = store.getAll();

        request.onsuccess = () => {
          const results = request.result as CachedHLSContent[];
          SharedLogger.log(`[PlayerHLSCache] Found ${results.length} cached content items`);
          resolve(results);
        };

        request.onerror = () => {
          SharedLogger.error('[PlayerHLSCache] Failed to get all cached content:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      SharedLogger.error('[PlayerHLSCache] Error getting all cached content:', error);
      return [];
    }
  }
}

// Export singleton instance
export const PlayerHLSCache = new PlayerHLSCacheClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('PlayerHLSCache', PlayerHLSCache);
}
