/**
 * Player Layer Type Definitions
 * Types for HLS playback, media management, and synchronization
 */

// ========================================
// Content & Playlist Types
// ========================================

export type ContentType = 'image' | 'video' | 'audio' | 'url' | 'text' | 'widget';

export interface PlaylistItem {
  id: number;
  content_id: number;
  duration: number;
  order: number;
  is_muted: boolean;  // Per-content mute control
  content: ContentItem;
}

export interface ContentItem {
  id: number;
  name: string;
  type: ContentType;
  file_path: string | null;
  url: string | null;
  thumbnail_path: string | null;
  mime_type?: string | null;
  metadata: Record<string, unknown> | null;
}

export interface Playlist {
  id: number;
  name: string;
  is_active: boolean;
  background_audio_id?: number | null;  // Playlist-level background audio
  items: PlaylistItem[];
  total_items?: number;
}

export interface DeviceSettings {
  volume_level: number;  // 0-100
  is_volume_enabled: boolean;
  background_audio_id: number | null;
  background_audio_url: string | null;
  background_audio_name: string | null;
}

export interface PlaylistSyncResponse {
  playlist: Playlist | null;
  device_settings: DeviceSettings | null;
  has_changes: boolean;
  message?: string;
}

// ========================================
// Video Player Types
// ========================================

export interface PlayerConfig {
  autoplay: boolean;
  muted: boolean;
  loop: boolean;
  preload: 'auto' | 'metadata' | 'none';
  controls: boolean;
}

export interface PlayerState {
  currentItemIndex: number;
  isPlaying: boolean;
  currentItem: PlaylistItem | null;
  playlist: Playlist | null;
  error: Error | null;
}

// Video.js Player Interface
export interface PlayerVideoJS {
  init(videoElement: HTMLVideoElement): void;
  loadPlaylist(playlist: Playlist): Promise<void>;
  play(): Promise<void>;
  pause(): void;
  stop(): void;
  next(): Promise<void>;
  previous(): Promise<void>;
  getCurrentItem(): PlaylistItem | null;
  getState(): PlayerState;
  destroy(): void;
}

// ========================================
// Media Cache Types
// ========================================

export interface CachedMedia {
  url: string;
  contentId: number;
  data: ArrayBuffer;
  mimeType: string;
  size: number;
  cachedAt: string;
  lastAccessed: string;
}

export interface CacheStats {
  totalItems: number;
  totalSize: number;
  oldestCache: string | null;
  newestCache: string | null;
}

export interface PlayerMediaCache {
  init(): Promise<void>;
  cacheMedia(url: string, contentId: number): Promise<void>;
  getCachedMedia(url: string): Promise<CachedMedia | null>;
  getCachedBlobURL(url: string): Promise<string | null>;
  isCached(url: string): Promise<boolean>;
  deleteMedia(url: string): Promise<void>;
  clearCache(): Promise<void>;
  getCacheStats(): Promise<CacheStats>;
  cleanupOldCache(maxItems?: number, maxSizeMB?: number): Promise<void>;
}

// ========================================
// Heartbeat Types
// ========================================

export interface HeartbeatPayload {
  device_id: number;
  status: 'online' | 'offline';
  current_content_id: number | null;
  system_info: SystemInfo;
}

export interface SystemInfo {
  platform: string;
  memory_usage?: number;
  cpu_usage?: number;
  uptime?: number;
}

export interface Heartbeat {
  start(): void;
  stop(): void;
  sendHeartbeat(): Promise<void>;
  isRunning(): boolean;
}

// ========================================
// Playlist Sync Types
// ========================================

export interface PlaylistSync {
  start(): void;
  stop(): void;
  syncNow(): Promise<boolean>;
  isRunning(): boolean;
}
