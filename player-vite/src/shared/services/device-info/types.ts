/**
 * Device Information Types
 * Centralized type definitions for all device info collectors
 */

// ============================================================================
// DEVICE INFO
// ============================================================================

export interface DeviceInfo {
  deviceId: number | null;
  deviceName: string | null;
  deviceCode: string | null;
  status: string | null;
  uuid: string;
  organizationId: number | null;
  rotation: number;
  currentPlaylist: PlaylistInfo | null;
  currentPlaying: CurrentPlayingInfo | null;
}

export interface PlaylistInfo {
  id: number;
  name: string;
  itemsCount: number;
  totalDuration: number; // seconds
}

export interface CurrentPlayingInfo {
  contentId: number;
  name: string;
  type: string;
  duration: number;
  order: number;
  isMuted: boolean;
}

// ============================================================================
// NETWORK INFO
// ============================================================================

export interface NetworkInfo {
  localIP: string | null;  // Attempted via WebRTC (may fail due to mDNS privacy)
  publicIP: string | null;
  clientIP: string | null; // Actual client IP from backend (most reliable)
  connectionType: string;
  online: boolean;
  downlinkSpeed: string | null; // Mbps
}

// ============================================================================
// SYSTEM INFO
// ============================================================================

export interface SystemInfo {
  platform: string;
  browser: BrowserInfo;
  screen: ScreenInfo;
  cpuCores: number;
  language: string;
  uptime: number; // milliseconds
  online: boolean;
  webglSupport: boolean;
  serviceWorkerStatus: string;
  deviceMemory: number | null; // GB
}

export interface BrowserInfo {
  name: string;
  version: string;
}

export interface ScreenInfo {
  width: number;
  height: number;
}

// Battery info removed - not relevant for digital signage (always plugged in)

// ============================================================================
// STORAGE INFO
// ============================================================================

export interface StorageInfo {
  total: {
    used: number; // bytes
    quota: number; // bytes
    percentage: number;
  };
  breakdown: {
    videos: number; // bytes
    images: number; // bytes
    audio: number; // bytes
    hls: number; // bytes
  };
  assignedContent: ContentInfo[];
  cachedCount: number;
  cacheHitRate: number; // 0-100
  recentCacheActivity: CacheActivity[];
}

export interface ContentInfo {
  id: number;
  name: string;
  type: string;
  size: number; // bytes (expected size)
  cachedSize: number; // bytes (actual cached size)
  cached: boolean;
  cacheStatus: 'cached' | 'downloading' | 'not_cached' | 'failed';
  thumbnailUrl: string | null;
  source: 'direct' | 'tag' | 'playlist' | 'unknown'; // Assignment source
  sourceId?: number; // Tag ID or Playlist ID if applicable
}

export interface CacheActivity {
  contentId: number;
  name: string;
  type: string;
  action: 'cached' | 'failed' | 'evicted';
  timestamp: Date;
  size: number; // bytes
}

// ============================================================================
// BACKEND INFO
// ============================================================================

export interface BackendInfo {
  apiUrl: string;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  websocketStatus: 'connected' | 'disconnected';
  lastHeartbeat: Date | null;
  lastSync: Date | null;
  apiResponseTime: number | null; // ms
  syncFrequency: number; // seconds
  backendVersion: string | null;
}

// ============================================================================
// AUDIO INFO
// ============================================================================

export interface AudioInfo {
  volumeLevel: number; // 0-100
  volumeEnabled: boolean;
  backgroundAudio: BackgroundAudioInfo | null;
  mutedItems: string[]; // Content names
  supportedFormats: string[];
}

export interface BackgroundAudioInfo {
  id: number;
  name: string;
  url: string;
  status: 'playing' | 'paused' | 'stopped' | 'error';
  source: 'device' | 'playlist';
}

// ============================================================================
// PERFORMANCE INFO
// ============================================================================

export interface PerformanceInfo {
  uptime: number; // milliseconds
  memory: MemoryInfo | null;
  fps: number;
  loadTime: number; // milliseconds
}

export interface MemoryInfo {
  used: number; // MB
  total: number; // MB
  limit: number; // MB
  percentage: number;
}

// ============================================================================
// COMPLETE DEVICE INFO (ALL TABS)
// ============================================================================

export interface CompleteDeviceInfo {
  device: DeviceInfo;
  network: NetworkInfo;
  system: SystemInfo;
  storage: StorageInfo;
  backend: BackendInfo;
  audio: AudioInfo;
  performance: PerformanceInfo;
  timestamp: Date;
}
