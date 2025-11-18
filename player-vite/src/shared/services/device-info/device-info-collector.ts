/**
 * Device Information Collector Service
 * Centralized service for collecting comprehensive device information
 *
 * @features
 * - Integrates with all player services (VideoJS, PlaylistSync, MediaCache, BackgroundAudio)
 * - Collects network, system, storage, backend, audio, performance metrics
 * - Type-safe with comprehensive interfaces
 * - No UI concerns - pure data collection
 * - Fully testable and reusable
 */

import { ServiceRegistry, getPlayerVideoJS, getPlayerMediaCache, getPlayerPlaylistSync, getPlayerBackgroundAudio } from '@shared/services/service-registry';
import { SharedDeviceState } from '@shared/device';
import { config } from '@shared/config';
import { getOrCreateDeviceUUID } from '@shared/utils/device-fingerprint';
import {
  getNetworkInfo,
  getDownloadSpeed
} from '@shared/utils/network-info';
import {
  getPerformanceInfo,
  getUptime,
  hasWebGLSupport,
  getServiceWorkerStatus
} from '@shared/utils/performance-info';
import type {
  CompleteDeviceInfo,
  DeviceInfo,
  NetworkInfo,
  SystemInfo,
  StorageInfo,
  BackendInfo,
  AudioInfo,
  PerformanceInfo,
  PlaylistInfo,
  CurrentPlayingInfo,
  ContentInfo,
  CacheActivity,
  BrowserInfo,
  ScreenInfo,
  BackgroundAudioInfo,
  MemoryInfo
} from './types';

/**
 * Device Information Collector Class
 * Singleton pattern for collecting device information
 */
class DeviceInfoCollectorClass {
  /**
   * Collect complete device information
   * Returns all information from all tabs
   */
  async collectAll(): Promise<CompleteDeviceInfo> {
    const [device, network, system, storage, backend, audio, performance] = await Promise.all([
      this.collectDeviceInfo(),
      this.collectNetworkInfo(),
      this.collectSystemInfo(),
      this.collectStorageInfo(),
      this.collectBackendInfo(),
      this.collectAudioInfo(),
      this.collectPerformanceInfo(),
    ]);

    return {
      device,
      network,
      system,
      storage,
      backend,
      audio,
      performance,
      timestamp: new Date(),
    };
  }

  /**
   * Collect Device tab information
   */
  private async collectDeviceInfo(): Promise<DeviceInfo> {
    const PlayerPlaylistSync = getPlayerPlaylistSync();
    const PlayerVideoJS = getPlayerVideoJS();

    // Get basic device info from SharedDeviceState
    const deviceIdStr = SharedDeviceState.getDeviceId();
    const deviceId = deviceIdStr ? parseInt(deviceIdStr) : null;
    const deviceName = SharedDeviceState.getDeviceName();
    const deviceCode = SharedDeviceState.getDeviceCode();
    const status = SharedDeviceState.getDeviceStatus();
    const uuid = getOrCreateDeviceUUID();
    const organizationIdStr = SharedDeviceState.getOrganizationId();
    const organizationId = organizationIdStr ? parseInt(organizationIdStr) : null;
    const rotation = SharedDeviceState.getScreenRotation();

    // Get current playlist info
    let currentPlaylist: PlaylistInfo | null = null;
    if (PlayerPlaylistSync) {
      const playlist = PlayerPlaylistSync.getCurrentPlaylist();
      if (playlist) {
        currentPlaylist = {
          id: playlist.id,
          name: playlist.name,
          itemsCount: playlist.items?.length || 0,
          totalDuration: playlist.items?.reduce((sum: number, item: any) => sum + item.duration, 0) || 0,
        };
      }
    }

    // Get current playing info
    let currentPlaying: CurrentPlayingInfo | null = null;
    if (PlayerVideoJS) {
      const state = PlayerVideoJS.getState();
      if (state.currentItem) {
        currentPlaying = {
          contentId: state.currentItem.content_id,
          name: state.currentItem.content.name,
          type: state.currentItem.content.type,
          duration: state.currentItem.duration,
          order: state.currentItem.order,
          isMuted: state.currentItem.is_muted || false,
        };
      }
    }

    return {
      deviceId,
      deviceName,
      deviceCode,
      status,
      uuid,
      organizationId,
      rotation,
      currentPlaylist,
      currentPlaying,
    };
  }

  /**
   * Collect Network tab information
   */
  private async collectNetworkInfo(): Promise<NetworkInfo> {
    const baseNetworkInfo = await getNetworkInfo();
    const downlinkSpeed = getDownloadSpeed();

    // Get client IP from backend (most reliable method)
    let clientIP: string | null = null;
    try {
      const deviceToken = SharedDeviceState.getDeviceToken();
      console.log('[DeviceInfoCollector] Fetching client IP from backend...');

      if (deviceToken) {
        // Use /devices/me endpoint with device JWT authentication
        const url = `${config.api.baseURL}/api/v1/devices/me`;
        console.log('[DeviceInfoCollector] API URL:', url);

        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${deviceToken}`,
          },
        });

        console.log('[DeviceInfoCollector] Response status:', response.status);

        if (response.ok) {
          const data = await response.json();
          console.log('[DeviceInfoCollector] Device data (summary):', {
            id: data.id,
            ip_address: data.ip_address,
            status: data.status
          });
          clientIP = data.ip_address || null;
          console.log('[DeviceInfoCollector] ✅ Client IP from backend:', clientIP);
        } else {
          console.warn('[DeviceInfoCollector] ❌ Failed to fetch device data:', response.statusText);
        }
      } else {
        console.warn('[DeviceInfoCollector] ⚠️ No device token available');
      }
    } catch (error) {
      console.error('[DeviceInfoCollector] ❌ Error fetching client IP:', error);
    }

    return {
      localIP: baseNetworkInfo.localIP,
      publicIP: baseNetworkInfo.publicIP,
      clientIP,
      connectionType: baseNetworkInfo.connectionType,
      online: baseNetworkInfo.online,
      downlinkSpeed,
    };
  }

  /**
   * Collect System tab information
   */
  private async collectSystemInfo(): Promise<SystemInfo> {
    const uptime = getUptime();
    const online = navigator.onLine;
    const webglSupport = hasWebGLSupport();
    const serviceWorkerStatus = getServiceWorkerStatus();

    // @ts-ignore - navigator.deviceMemory is non-standard
    const deviceMemory = navigator.deviceMemory || null;

    // Browser info
    const browserInfo = this.detectBrowser();

    // Screen info
    const screenInfo: ScreenInfo = {
      width: window.screen.width,
      height: window.screen.height,
    };

    return {
      platform: navigator.platform,
      browser: browserInfo,
      screen: screenInfo,
      cpuCores: navigator.hardwareConcurrency || 0,
      language: navigator.language,
      uptime,
      online,
      webglSupport,
      serviceWorkerStatus,
      deviceMemory,
    };
  }

  /**
   * Collect Storage tab information
   */
  private async collectStorageInfo(): Promise<StorageInfo> {
    const PlayerMediaCache = getPlayerMediaCache();
    const PlayerPlaylistSync = getPlayerPlaylistSync();

    // Get storage quota
    let totalUsed = 0;
    let totalQuota = 0;

    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        totalUsed = estimate.usage || 0;
        totalQuota = estimate.quota || 0;
      } catch (error) {
        console.error('[DeviceInfoCollector] Failed to get storage estimate:', error);
      }
    }

    const percentage = totalQuota > 0 ? Math.round((totalUsed / totalQuota) * 100) : 0;

    // Get cache stats and breakdown
    let breakdown = {
      videos: 0,
      images: 0,
      audio: 0,
      hls: 0,
    };
    let cachedCount = 0;
    let assignedContent: ContentInfo[] = [];
    let recentCacheActivity: CacheActivity[] = [];

    if (PlayerMediaCache) {
      try {
        const cacheStats = await PlayerMediaCache.getCacheStats();
        cachedCount = cacheStats.totalItems;

        // Get all cached items to categorize by type
        const allCachedItems = await this.getAllCachedItems();

        for (const item of allCachedItems) {
          const url = item.url.toLowerCase();
          if (url.includes('/videos/') || url.includes('.mp4') || url.includes('.webm')) {
            breakdown.videos += item.size;
          } else if (url.includes('/images/') || url.includes('.jpg') || url.includes('.png') || url.includes('.jpeg')) {
            breakdown.images += item.size;
          } else if (url.includes('/audio/') || url.includes('.mp3') || url.includes('.wav')) {
            breakdown.audio += item.size;
          } else if (url.includes('.m3u8') || url.includes('.ts')) {
            breakdown.hls += item.size;
          }
        }

        // Get recent cache activity (last 10 items, sorted by cachedAt)
        recentCacheActivity = allCachedItems
          .sort((a, b) => new Date(b.cachedAt).getTime() - new Date(a.cachedAt).getTime())
          .slice(0, 10)
          .map(item => ({
            contentId: item.contentId,
            name: this.extractFilename(item.url),
            type: this.detectContentType(item.url),
            action: 'cached' as const,
            timestamp: new Date(item.cachedAt),
            size: item.size,
          }));
      } catch (error) {
        console.error('[DeviceInfoCollector] Failed to get cache stats:', error);
      }
    }

    // Get assigned content from current playlist
    if (PlayerPlaylistSync) {
      const playlist = PlayerPlaylistSync.getCurrentPlaylist();
      if (playlist && playlist.items) {
        assignedContent = await Promise.all(
          playlist.items.map(async (item: any) => {
            const url = item.content.file_path || item.content.url || '';
            let cached = false;
            let cacheStatus: 'cached' | 'downloading' | 'not_cached' | 'failed' = 'not_cached';

            if (PlayerMediaCache && url) {
              cached = await PlayerMediaCache.isCached(url);
              cacheStatus = cached ? 'cached' : 'not_cached';
            }

            return {
              id: item.content_id,
              name: item.content.name,
              type: item.content.type,
              size: item.content.file_size || 0,
              cached,
              cacheStatus,
              thumbnailUrl: item.content.thumbnail_url || null,
            };
          })
        );
      }
    }

    // Calculate cache hit rate
    const totalAssigned = assignedContent.length;
    const totalCached = assignedContent.filter(c => c.cached).length;
    const cacheHitRate = totalAssigned > 0 ? Math.round((totalCached / totalAssigned) * 100) : 0;

    return {
      total: {
        used: totalUsed,
        quota: totalQuota,
        percentage,
      },
      breakdown,
      assignedContent,
      cachedCount,
      cacheHitRate,
      recentCacheActivity,
    };
  }

  /**
   * Collect Backend tab information
   */
  private async collectBackendInfo(): Promise<BackendInfo> {
    const PlayerPlaylistSync = getPlayerPlaylistSync();

    // Get API URL from config
    const apiUrl = config.api.baseURL;

    // Connection status based on last sync
    let connectionStatus: 'connected' | 'disconnected' | 'reconnecting' = 'connected';
    let lastSync: Date | null = null;
    let syncFrequency = 60; // Default 60 seconds

    if (PlayerPlaylistSync) {
      const isRunning = PlayerPlaylistSync.isRunning();
      connectionStatus = isRunning ? 'connected' : 'disconnected';
    }

    // WebSocket status (if available)
    let websocketStatus: 'connected' | 'disconnected' = 'disconnected';
    // TODO: Implement WebSocket service integration when available

    // Heartbeat timing (from ShellActivationPoll)
    const lastHeartbeat = this.getLastHeartbeatTime();

    // API response time (measure with a simple ping)
    let apiResponseTime: number | null = null;
    try {
      const startTime = performance.now();
      await fetch(`${apiUrl}/api/v1/health`, { method: 'GET', signal: AbortSignal.timeout(5000) });
      apiResponseTime = Math.round(performance.now() - startTime);
    } catch (error) {
      connectionStatus = 'disconnected';
    }

    // Backend version (would need to be returned from API)
    const backendVersion = null; // TODO: Add version endpoint

    return {
      apiUrl,
      connectionStatus,
      websocketStatus,
      lastHeartbeat,
      lastSync,
      apiResponseTime,
      syncFrequency,
      backendVersion,
    };
  }

  /**
   * Collect Audio tab information
   */
  private async collectAudioInfo(): Promise<AudioInfo> {
    const PlayerBackgroundAudio = getPlayerBackgroundAudio();
    const PlayerPlaylistSync = getPlayerPlaylistSync();

    // Get volume from device settings or default
    let volumeLevel = 75;
    let volumeEnabled = true;

    // Get background audio info
    let backgroundAudio: BackgroundAudioInfo | null = null;
    if (PlayerBackgroundAudio) {
      const currentAudio = PlayerBackgroundAudio.getCurrentAudio();
      const isPlaying = PlayerBackgroundAudio.isPlaying();

      if (currentAudio.id && currentAudio.url) {
        // Get audio name from device settings if available
        const audioName = 'Background Music'; // TODO: Get from device settings

        backgroundAudio = {
          id: currentAudio.id,
          name: audioName,
          url: currentAudio.url,
          status: isPlaying ? 'playing' : 'paused',
          source: 'device', // or 'playlist' depending on settings
        };
      }
    }

    // Get muted items from playlist
    let mutedItems: string[] = [];
    if (PlayerPlaylistSync) {
      const playlist = PlayerPlaylistSync.getCurrentPlaylist();
      if (playlist && playlist.items) {
        mutedItems = playlist.items
          .filter((item: any) => item.is_muted)
          .map((item: any) => item.content.name);
      }
    }

    // Supported audio formats
    const audio = document.createElement('audio');
    const supportedFormats: string[] = [];

    const formats = [
      { type: 'audio/mpeg', ext: 'MP3' },
      { type: 'audio/ogg', ext: 'OGG' },
      { type: 'audio/wav', ext: 'WAV' },
      { type: 'audio/webm', ext: 'WEBM' },
      { type: 'audio/aac', ext: 'AAC' },
    ];

    for (const format of formats) {
      if (audio.canPlayType(format.type)) {
        supportedFormats.push(format.ext);
      }
    }

    return {
      volumeLevel,
      volumeEnabled,
      backgroundAudio,
      mutedItems,
      supportedFormats,
    };
  }

  /**
   * Collect Performance tab information
   */
  private async collectPerformanceInfo(): Promise<PerformanceInfo> {
    const perfInfo = getPerformanceInfo();

    // Convert memory info format
    let memory: MemoryInfo | null = null;
    if (perfInfo.memory) {
      const percentage = Math.round((perfInfo.memory.used / perfInfo.memory.limit) * 100);
      memory = {
        used: perfInfo.memory.used,
        total: perfInfo.memory.total,
        limit: perfInfo.memory.limit,
        percentage,
      };
    }

    return {
      uptime: perfInfo.uptime,
      memory,
      fps: perfInfo.fps,
      loadTime: perfInfo.loadTime,
    };
  }

  /**
   * Helper: Detect browser name and version
   */
  private detectBrowser(): BrowserInfo {
    const ua = navigator.userAgent;
    let name = 'Unknown';
    let version = 'Unknown';

    if (ua.includes('Firefox/')) {
      name = 'Firefox';
      version = ua.match(/Firefox\/(\d+\.\d+)/)?.[1] || 'Unknown';
    } else if (ua.includes('Edg/')) {
      name = 'Edge';
      version = ua.match(/Edg\/(\d+\.\d+)/)?.[1] || 'Unknown';
    } else if (ua.includes('Chrome/')) {
      name = 'Chrome';
      version = ua.match(/Chrome\/(\d+\.\d+)/)?.[1] || 'Unknown';
    } else if (ua.includes('Safari/')) {
      name = 'Safari';
      version = ua.match(/Version\/(\d+\.\d+)/)?.[1] || 'Unknown';
    }

    return {
      name,
      version,
    };
  }

  /**
   * Helper: Get all cached items from PlayerMediaCache
   */
  private async getAllCachedItems(): Promise<any[]> {
    try {
      // Access IndexedDB directly to get all items
      const db = await this.openCacheDB();
      const transaction = db.transaction(['media'], 'readonly');
      const objectStore = transaction.objectStore('media');
      const request = objectStore.getAll();

      return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('[DeviceInfoCollector] Failed to get cached items:', error);
      return [];
    }
  }

  /**
   * Helper: Open IndexedDB cache
   */
  private async openCacheDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('signage_media_cache', 1);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Helper: Extract filename from URL
   */
  private extractFilename(url: string): string {
    const parts = url.split('/');
    return parts[parts.length - 1] || 'Unknown';
  }

  /**
   * Helper: Detect content type from URL
   */
  private detectContentType(url: string): string {
    const lower = url.toLowerCase();
    if (lower.includes('.mp4') || lower.includes('.webm') || lower.includes('/videos/')) {
      return 'video';
    } else if (lower.includes('.jpg') || lower.includes('.png') || lower.includes('.jpeg') || lower.includes('/images/')) {
      return 'image';
    } else if (lower.includes('.mp3') || lower.includes('.wav') || lower.includes('/audio/')) {
      return 'audio';
    } else if (lower.includes('.m3u8')) {
      return 'hls';
    }
    return 'unknown';
  }

  /**
   * Helper: Get last heartbeat time
   */
  private getLastHeartbeatTime(): Date | null {
    const lastHeartbeat = SharedDeviceState.getLastHeartbeatTime();
    if (lastHeartbeat) {
      return new Date(lastHeartbeat);
    }
    return null;
  }
}

// Export singleton instance
export const DeviceInfoCollector = new DeviceInfoCollectorClass();

// Register to ServiceRegistry
if (typeof window !== 'undefined') {
  ServiceRegistry.register('DeviceInfoCollector', DeviceInfoCollector);
}
