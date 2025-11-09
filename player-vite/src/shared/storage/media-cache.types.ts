/**
 * Media Cache Type Definitions
 */

import type { ContentType } from './storage-schema';

/**
 * Cached media entry stored in IndexedDB
 */
export interface CachedMediaEntry {
  content_id: number;
  title: string;
  url: string;
  content_type: ContentType;
  mime_type: string;
  blob: Blob;
  size: number;
  timestamp: number;
}

/**
 * Content info for caching
 */
export interface ContentCacheInfo {
  content_id: number;
  title: string;
  url: string;
  content_type: ContentType;
  mime_type?: string;
}

/**
 * Cache sync result
 */
export interface CacheSyncResult {
  downloaded: number;
  removed: number;
  errors: number;
}
