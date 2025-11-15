/**
 * Storage Module - Barrel Export
 * Provides IndexedDB storage and media caching functionality
 */

// IndexedDB Manager
export { dbManager, IndexedDBManager } from './indexed-db-manager';
export type { StorageEstimate, StoreData, TransactionMode } from './indexed-db.types';

// Device Config Storage
export { deviceConfigStorage, DeviceConfigStorage } from './device-config-storage';
export type { DeviceConfig } from './device-config-storage';

// Media Cache
export { mediaCache, MediaCache } from './media-cache';
export type { CachedMediaEntry, ContentCacheInfo, CacheSyncResult } from './media-cache.types';

// Connection Log Storage
export { ConnectionLogStorage } from './connection-log-storage';
export type { ConnectionLogEntry } from './connection-log-storage';

// Schema and Constants
export {
  DB_NAME,
  DB_VERSION,
  SCHEMA,
  STATUS,
  CONTENT_TYPE,
  type IndexConfig,
  type StoreConfig,
  type DeviceStatus,
  type DownloadStatus,
  type SyncStatus,
  type ContentType,
} from './storage-schema';
