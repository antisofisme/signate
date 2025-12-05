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
  rotation: number;  // 0, 90, 180, 270
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
  setVolume(level: number): void;
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
  createBlobUrl(cachedMedia: CachedMedia): Promise<string>;
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
  forceReload(): void;
  getCurrentPlaylist(): Playlist | null;
  isRunning(): boolean;
}

// ========================================
// Command Executor Types
// ========================================

export enum CommandType {
  // Player controls
  PLAY = 'play',
  PAUSE = 'pause',
  STOP = 'stop',
  NEXT = 'next',
  PREVIOUS = 'previous',
  SEEK = 'seek',
  SET_VOLUME = 'set_volume',

  // Playlist controls
  LOAD_PLAYLIST = 'load_playlist',
  RELOAD_PLAYLIST = 'reload_playlist',
  CLEAR_PLAYLIST = 'clear_playlist',

  // Cache controls
  CLEAR_CACHE = 'clear_cache',
  CACHE_CONTENT = 'cache_content',

  // System controls
  REBOOT = 'reboot',
  RELOAD_PAGE = 'reload_page',
  CLEAR_STORAGE = 'clear_storage',
  FACTORY_RESET = 'factory_reset',

  // Display controls
  FULLSCREEN = 'fullscreen',
  EXIT_FULLSCREEN = 'exit_fullscreen',
  SET_BRIGHTNESS = 'set_brightness',

  // Network controls
  RUN_SPEEDTEST = 'run_speedtest',
  PING_TEST = 'ping_test',

  // Info requests
  GET_STATUS = 'get_status',
  GET_SYSTEM_INFO = 'get_system_info',
  GET_PLAYLIST_INFO = 'get_playlist_info',
}

export interface Command {
  id: string;
  type: CommandType;
  params?: Record<string, any>;
  timestamp: string;
}

export interface CommandResult {
  command_id: string;
  success: boolean;
  data?: any;
  error?: string;
  executed_at: string;
}

export interface PlayerCommandExecutor {
  init(): void;
  registerHandler(type: CommandType, handler: (params?: Record<string, any>) => Promise<any>): void;
  executeCommand(command: Command): Promise<CommandResult>;
  getHistory(): CommandResult[];
}

// ========================================
// Health Reporter Types
// ========================================

export interface HealthMetrics {
  // System metrics
  cpu_usage: number | null;
  memory_usage: number | null;
  memory_total_mb: number | null;
  memory_used_mb: number | null;
  disk_usage: number | null;
  disk_total_gb: number | null;
  disk_used_gb: number | null;

  // Network metrics
  network_latency_ms: number | null;
  network_download_mbps: number | null;
  network_upload_mbps: number | null;
  connection_quality: string;

  // Display metrics
  display_resolution: string;
  display_refresh_rate: number;

  // Player metrics
  player_version: string;
  player_uptime_hours: number;
  content_errors_count: number;
  last_error_message: string | null;
  last_error_at: string | null;

  // Metadata
  metadata: {
    user_agent: string;
    platform: string;
    online: boolean;
    timestamp: string;
  };
}

export interface PlayerHealthReporter {
  start(): void;
  stop(): void;
  reportHealth(): Promise<void>;
  collectMetrics(): Promise<HealthMetrics>;
  recordError(errorMessage: string): void;
  resetErrors(): void;
  isRunning(): boolean;
}

// ========================================
// HLS Cache Types
// ========================================

export interface HLSVariant {
  quality: string; // '360p', '480p', '720p', '1080p'
  bandwidth: number;
  resolution: string;
  playlistUrl: string;
}

export interface HLSSegment {
  segmentUrl: string;
  duration: number;
  index: number;
}

export interface CachedHLSContent {
  contentId: number;
  masterPlaylistUrl: string;
  variants: HLSVariant[];
  selectedQuality: string;
  segments: {
    [quality: string]: HLSSegment[];
  };
  cachedAt: string;
}

export interface PlayerHLSCache {
  init(): Promise<void>;
  cacheHLSContent(contentId: number, masterPlaylistUrl: string): Promise<void>;
  isHLSCached(contentId: number): Promise<boolean>;
  getSegments(contentId: number): Promise<Array<{ index: number; data: ArrayBuffer; duration: number }>>;
  isCacheStale(contentId: number, currentUrl: string, serverUpdatedAt?: string): Promise<boolean>;
  clearCache(contentId: number): Promise<void>;
  clearHLSCache(contentId: number): Promise<void>;
  getAllCachedContent(): Promise<CachedHLSContent[]>;
}

// ========================================
// Background Audio Types
// ========================================

export interface PlayerBackgroundAudio {
  init(): void;
  loadFromSettings(settings: DeviceSettings | null): Promise<void>;
  play(): Promise<void>;
  pause(): void;
  stop(): void;
  setVolume(level: number): void;
  setEnabled(enabled: boolean): void;
  isPlaying(): boolean;
  getCurrentAudio(): { id: number | null; url: string | null };
  destroy(): void;
}
