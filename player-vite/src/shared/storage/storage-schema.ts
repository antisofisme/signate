/**
 * IndexedDB Schema
 * Defines database structure for offline storage
 */

export const DB_NAME = 'signage_player';
export const DB_VERSION = 2; // Incremented for device_config store

/**
 * Index configuration
 */
export interface IndexConfig {
  name: string;
  keyPath: string | string[];
  unique: boolean;
}

/**
 * Object store configuration
 */
export interface StoreConfig {
  keyPath: string;
  autoIncrement: boolean;
  indexes?: IndexConfig[];
}

/**
 * Database Schema
 * Each object store with its keyPath and indexes
 */
export const SCHEMA: Record<string, StoreConfig> = {
  // Device configuration (separate from devices for release flow management)
  device_config: {
    keyPath: 'key',
    autoIncrement: false,
    indexes: [],
  },

  // Device information
  devices: {
    keyPath: 'id',
    autoIncrement: false,
    indexes: [
      { name: 'code', keyPath: 'code', unique: true },
      { name: 'last_seen', keyPath: 'last_seen', unique: false },
      { name: 'status', keyPath: 'status', unique: false },
    ],
  },

  // Playlists
  playlists: {
    keyPath: 'id',
    autoIncrement: false,
    indexes: [
      { name: 'device_id', keyPath: 'device_id', unique: false },
      { name: 'updated_at', keyPath: 'updated_at', unique: false },
      { name: 'is_active', keyPath: 'is_active', unique: false },
    ],
  },

  // Content/Videos
  contents: {
    keyPath: 'id',
    autoIncrement: false,
    indexes: [
      { name: 'playlist_id', keyPath: 'playlist_id', unique: false },
      { name: 'download_status', keyPath: 'download_status', unique: false },
      { name: 'type', keyPath: 'type', unique: false },
      { name: 'sequence', keyPath: 'sequence', unique: false },
    ],
  },

  // HLS Segments
  segments: {
    keyPath: 'id',
    autoIncrement: false,
    indexes: [
      { name: 'content_id', keyPath: 'content_id', unique: false },
      { name: 'sequence', keyPath: 'sequence', unique: false },
      { name: 'downloaded_at', keyPath: 'downloaded_at', unique: false },
    ],
  },

  // Download queue
  download_queue: {
    keyPath: 'id',
    autoIncrement: true,
    indexes: [
      { name: 'content_id', keyPath: 'content_id', unique: false },
      { name: 'status', keyPath: 'status', unique: false },
      { name: 'priority', keyPath: 'priority', unique: false },
      { name: 'created_at', keyPath: 'created_at', unique: false },
    ],
  },

  // Analytics events (for offline queuing)
  analytics: {
    keyPath: 'id',
    autoIncrement: true,
    indexes: [
      { name: 'event_type', keyPath: 'event_type', unique: false },
      { name: 'synced', keyPath: 'synced', unique: false },
      { name: 'created_at', keyPath: 'created_at', unique: false },
    ],
  },

  // Cache for API responses
  cache: {
    keyPath: 'url',
    autoIncrement: false,
    indexes: [
      { name: 'timestamp', keyPath: 'timestamp', unique: false },
      { name: 'expires_at', keyPath: 'expires_at', unique: false },
    ],
  },

  // Media files cache (for offline playback)
  media_files: {
    keyPath: 'content_id',
    autoIncrement: false,
    indexes: [
      { name: 'url', keyPath: 'url', unique: false },
      { name: 'timestamp', keyPath: 'timestamp', unique: false },
    ],
  },
};

/**
 * Enums for status values
 */
export const STATUS = {
  DEVICE: {
    PENDING: 'pending',
    ACTIVE: 'active',
    INACTIVE: 'inactive',
    RELEASED: 'released',
  },
  DOWNLOAD: {
    PENDING: 'pending',
    DOWNLOADING: 'downloading',
    COMPLETED: 'completed',
    FAILED: 'failed',
  },
  SYNC: {
    PENDING: 'pending',
    SYNCING: 'syncing',
    SYNCED: 'synced',
    FAILED: 'failed',
  },
} as const;

/**
 * Content types
 */
export const CONTENT_TYPE = {
  VIDEO: 'video',
  IMAGE: 'image',
  WEBPAGE: 'webpage',
} as const;

/**
 * Type exports for TypeScript
 */
export type DeviceStatus = typeof STATUS.DEVICE[keyof typeof STATUS.DEVICE];
export type DownloadStatus = typeof STATUS.DOWNLOAD[keyof typeof STATUS.DOWNLOAD];
export type SyncStatus = typeof STATUS.SYNC[keyof typeof STATUS.SYNC];
export type ContentType = typeof CONTENT_TYPE[keyof typeof CONTENT_TYPE];
