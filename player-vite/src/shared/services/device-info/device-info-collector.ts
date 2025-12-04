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

import { ServiceRegistry, getPlayerVideoJS, getPlayerMediaCache, getPlayerPlaylistSync, getPlayerBackgroundAudio, getSharedWebSocket, getPlayerHLSCache } from '@shared/services/service-registry';
// Side-effect import to ensure WebSocket is registered before we try to access it
import '@shared/websocket/shared-websocket';
import { SharedDeviceState } from '@shared/device';
import { config } from '@shared/config';
import { SharedAPIClient } from '@shared/api';
import { getOrCreateDeviceUUID } from '@shared/utils/device-fingerprint';
import { playerScheduleManager } from '@player/services/player-schedule-manager';
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
  MemoryInfo,
  ScheduleInfo
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
    const PlayerHLSCache = getPlayerHLSCache();

    // Get storage quota - try browser API first, then calculate from actual cache
    let totalUsed = 0;
    let totalQuota = 0;
    let quotaAvailable = false;

    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        totalUsed = estimate.usage || 0;
        totalQuota = estimate.quota || 0;
        quotaAvailable = totalQuota > 0;
      } catch (error) {
        console.error('[DeviceInfoCollector] Failed to get storage estimate:', error);
      }
    }

    // Calculate percentage - if browser quota unavailable, use cache-based calculation
    let percentage = 0;
    if (quotaAvailable && totalQuota > 0) {
      percentage = Math.round((totalUsed / totalQuota) * 100);
    }

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
          // Use MIME type for proper categorization (more reliable than URL patterns)
          // Field is 'mime_type' (snake_case) not 'mimeType' (camelCase)
          const mimeType = (item.mime_type || item.mimeType || '').toLowerCase();

          if (mimeType.startsWith('video/') || mimeType.includes('mp4') || mimeType.includes('webm')) {
            breakdown.videos += item.size;
          } else if (mimeType.startsWith('image/') || mimeType.includes('jpeg') || mimeType.includes('png') || mimeType.includes('gif')) {
            breakdown.images += item.size;
          } else if (mimeType.startsWith('audio/') || mimeType.includes('mpeg') || mimeType.includes('wav')) {
            breakdown.audio += item.size;
          } else if (mimeType.includes('mpegurl') || mimeType.includes('mp2t')) {
            // HLS manifest (application/vnd.apple.mpegurl) and segments (video/mp2t)
            breakdown.hls += item.size;
          } else {
            // Fallback: Use URL pattern if mimeType is missing
            const url = (item.url || '').toLowerCase();
            if (url.includes('.mp4') || url.includes('.webm') || url.includes('/videos/')) {
              breakdown.videos += item.size;
            } else if (url.includes('.jpg') || url.includes('.png') || url.includes('.jpeg') || url.includes('/images/')) {
              breakdown.images += item.size;
            } else if (url.includes('.mp3') || url.includes('.wav') || url.includes('/audio/')) {
              breakdown.audio += item.size;
            } else if (url.includes('.m3u8') || url.includes('.ts')) {
              breakdown.hls += item.size;
            }
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

    // Add HLS cache stats from separate IndexedDB
    if (PlayerHLSCache) {
      try {
        const hlsStats = await PlayerHLSCache.getCacheStats();
        breakdown.hls += hlsStats.totalSize; // Add to existing HLS breakdown
        cachedCount += hlsStats.contentCount; // Add HLS content count
      } catch (error) {
        console.error('[DeviceInfoCollector] Failed to get HLS cache stats:', error);
      }
    }

    // Calculate actual cache size from breakdown (sum of all cached content)
    const actualCacheSize = breakdown.videos + breakdown.images + breakdown.audio + breakdown.hls;

    // Debug logging with console.warn (survives production build)
    console.warn('[DeviceInfoCollector] Storage Debug:', {
      browserQuotaAvailable: quotaAvailable,
      browserUsage: totalUsed,
      browserQuota: totalQuota,
      actualCacheSize,
      breakdown,
    });

    // Improved storage calculation logic:
    // 1. If browser API works and returns valid data, use it
    // 2. If browser API fails OR returns 0, use actual cache size from IndexedDB
    // 3. Always prefer actualCacheSize if it's greater (more accurate)

    // Use the higher of browser-reported usage or actual cache (for accuracy)
    if (actualCacheSize > totalUsed) {
      totalUsed = actualCacheSize;
    }

    // If no quota available from browser, estimate based on device type
    if (!quotaAvailable || totalQuota === 0) {
      // Estimate quota based on device capabilities
      // Mobile: ~500MB, Desktop: ~2GB, Signage devices: ~1GB
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      totalQuota = isMobile ? 500 * 1024 * 1024 : 1024 * 1024 * 1024; // 500MB or 1GB
      console.warn('[DeviceInfoCollector] Using estimated quota:', {
        isMobile,
        estimatedQuota: totalQuota / (1024 * 1024) + ' MB'
      });
    }

    // Calculate percentage with better precision for small values
    if (totalQuota > 0) {
      const rawPercent = (totalUsed / totalQuota) * 100;
      // Use 1 decimal place for values < 1%, otherwise round to integer
      if (rawPercent > 0 && rawPercent < 1) {
        percentage = Math.max(0.1, parseFloat(rawPercent.toFixed(1))); // Minimum 0.1% if any usage
      } else {
        percentage = Math.min(100, Math.round(rawPercent));
      }
    } else {
      percentage = 0;
    }

    console.warn('[DeviceInfoCollector] Final storage calculation:', {
      totalUsed,
      totalQuota,
      percentage,
      usedMB: (totalUsed / (1024 * 1024)).toFixed(2),
      quotaMB: (totalQuota / (1024 * 1024)).toFixed(2)
    });

    // ========================================================================
    // FETCH ALL ASSIGNED CONTENT (WITHOUT OVERRIDE FILTER)
    // This ensures Device Info shows ALL content from direct/tag/playlist
    // regardless of whether override mode is active (override only affects playback)
    // ========================================================================
    const deviceId = SharedDeviceState.getDeviceId();
    if (deviceId) {
      try {
        // Make API call WITHOUT schedule_mode=override to get ALL content
        const url = `${config.api.baseURL}/api/v1/client/playlist?device_id=${deviceId}`;
        console.warn('[DeviceInfoCollector] Fetching ALL content (no override filter):', url);

        const response = await SharedAPIClient.get<any>(url);
        const playlist = response?.playlist;

        console.warn('[DeviceInfoCollector] Full playlist data:', {
          hasPlaylist: !!playlist,
          itemCount: playlist?.items?.length || 0,
          sampleItem: playlist?.items?.[0] ? {
            content_id: playlist.items[0].content_id,
            content: {
              name: playlist.items[0].content?.name,
              title: playlist.items[0].content?.title,
              file_size: playlist.items[0].content?.file_size,
              metadata: playlist.items[0].content?.metadata,
            }
          } : null
        });

        if (playlist && playlist.items) {
          assignedContent = await Promise.all(
            playlist.items.map(async (item: any) => {
              const url = item.content.file_path || item.content.url || '';
              const contentType = item.content.type || '';
              let cached = false;
              let cacheStatus: 'cached' | 'downloading' | 'not_cached' | 'failed' = 'not_cached';
              let cachedSize = 0;

              // Check MediaCache for direct files (images, non-HLS videos, audio)
              if (PlayerMediaCache && url) {
                cached = await PlayerMediaCache.isCached(url);
                if (cached) {
                  // Try to get actual cached size
                  try {
                    const cachedMedia = await (PlayerMediaCache as any).getCachedMedia(url);
                    if (cachedMedia) {
                      cachedSize = cachedMedia.size || 0;
                    }
                  } catch (e) {
                    // Ignore error, use file_size from content
                  }
                }
              }

              // Also check HLS cache for video content (HLS is cached separately)
              if (!cached && PlayerHLSCache && contentType === 'video') {
                try {
                  cached = await PlayerHLSCache.isHLSCached(item.content_id);
                  if (cached) {
                    // Get HLS cache size for this content
                    const hlsStats = await (PlayerHLSCache as any).getContentCacheStats?.(item.content_id);
                    if (hlsStats) {
                      cachedSize = hlsStats.totalSize || 0;
                    }
                  }
                } catch (e) {
                  // Ignore error, HLS cache check failed
                }
              }

              cacheStatus = cached ? 'cached' : 'not_cached';

              // Get file_size from metadata (where backend puts it) or directly
              const fileSize = item.content.metadata?.file_size
                || item.content.file_size
                || item.file_size
                || 0;

              // Parse source field from backend (e.g., "direct", "tag:27", "playlist:28")
              const rawSource = item.source || 'unknown';
              let source: 'direct' | 'tag' | 'playlist' | 'unknown' = 'unknown';
              let sourceId: number | undefined;

              if (rawSource === 'direct') {
                source = 'direct';
              } else if (rawSource.startsWith('tag:')) {
                source = 'tag';
                sourceId = parseInt(rawSource.split(':')[1], 10);
              } else if (rawSource.startsWith('playlist:')) {
                source = 'playlist';
                sourceId = parseInt(rawSource.split(':')[1], 10);
              } else if (rawSource.startsWith('legacy-playlist:')) {
                source = 'playlist';
                sourceId = parseInt(rawSource.split(':')[1], 10);
              }

              console.warn('[DeviceInfoCollector] Content item:', {
                id: item.content_id,
                name: item.content.name || item.content.title,
                cached,
                cachedSize,
                fileSize,
                source,
                sourceId,
              });

              return {
                id: item.content_id,
                name: item.content.name || item.content.title || 'Unknown',
                type: contentType,
                size: fileSize,  // Expected size from server (for reference)
                cachedSize: cachedSize,  // REAL cache size from IndexedDB only (0 if not found)
                cached,
                cacheStatus,
                thumbnailUrl: item.content.thumbnail_url || item.content.thumbnail_path || null,
                source,
                sourceId,
              };
            })
          );
        }
      } catch (error) {
        console.error('[DeviceInfoCollector] Failed to fetch all content:', error);
      }
    }

    // Calculate cache hit rate
    const totalAssigned = assignedContent.length;
    const totalCached = assignedContent.filter(c => c.cached).length;
    const cacheHitRate = totalAssigned > 0 ? Math.round((totalCached / totalAssigned) * 100) : 0;

    // ========================================================================
    // GET ACTIVE SCHEDULE INFO
    // This shows the user when override mode is active and which playlist
    // ========================================================================
    let activeSchedule: ScheduleInfo | null = null;
    const currentSchedule = playerScheduleManager.getCurrentSchedule();
    if (currentSchedule) {
      // Get playlist name from the current playback playlist (if available)
      const PlayerPlaylistSync = getPlayerPlaylistSync();
      const playbackPlaylist = PlayerPlaylistSync?.getCurrentPlaylist();
      const playlistName = playbackPlaylist?.name || null;

      activeSchedule = {
        id: currentSchedule.id,
        name: currentSchedule.name,
        playlistId: currentSchedule.playlist_id,
        playlistName,
        mode: currentSchedule.mode || 'rotate',
        startTime: currentSchedule.start_time,
        endTime: currentSchedule.end_time,
      };

      console.warn('[DeviceInfoCollector] Active schedule:', activeSchedule);
    }

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
      activeSchedule,
    };
  }

  /**
   * Collect Backend tab information
   */
  private async collectBackendInfo(): Promise<BackendInfo> {
    // Get API URL from config
    const apiUrl = config.api.baseURL;

    // Default values
    let connectionStatus: 'connected' | 'disconnected' | 'reconnecting' = 'disconnected';
    let lastSync: Date | null = null;
    let syncFrequency = 60; // Default 60 seconds

    // WebSocket status - check directly from service
    // Use console.warn for debugging (survives production build, unlike console.log)
    let websocketStatus: 'connected' | 'disconnected' = 'disconnected';
    const SharedWebSocket = getSharedWebSocket();
    if (SharedWebSocket) {
      // Get internal state details for debugging
      const wsState = (SharedWebSocket as any).state;
      const wsReadyState = (SharedWebSocket as any).ws?.readyState;
      const isConnectedResult = SharedWebSocket.isConnected();

      // Direct check: if ws.readyState === OPEN (1), consider it connected
      // This is a fallback in case internal state tracking has issues
      const wsActuallyOpen = wsReadyState === 1; // WebSocket.OPEN = 1

      // Use the more reliable of the two checks
      websocketStatus = (isConnectedResult || wsActuallyOpen) ? 'connected' : 'disconnected';

      // Debug logging with console.warn (survives production build)
      console.warn('[DeviceInfoCollector] WebSocket Debug:', {
        serviceFound: true,
        internalState: wsState,
        wsReadyState: wsReadyState,
        wsReadyStateLabel: wsReadyState === 0 ? 'CONNECTING' : wsReadyState === 1 ? 'OPEN' : wsReadyState === 2 ? 'CLOSING' : wsReadyState === 3 ? 'CLOSED' : 'null/undefined',
        isConnectedMethod: isConnectedResult,
        wsActuallyOpen: wsActuallyOpen,
        finalStatus: websocketStatus,
      });
    } else {
      console.warn('[DeviceInfoCollector] WebSocket service NOT FOUND in ServiceRegistry!');
    }

    // Heartbeat timing
    const lastHeartbeat = this.getLastHeartbeatTime();

    // API connection status - use actual health check as source of truth
    let apiResponseTime: number | null = null;
    let backendVersion: string | null = null;
    try {
      const startTime = performance.now();
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      apiResponseTime = Math.round(performance.now() - startTime);

      if (response.ok) {
        connectionStatus = 'connected'; // Only set connected if health check succeeds
        const data = await response.json();
        backendVersion = data.version || null;
      } else {
        connectionStatus = 'disconnected';
      }
    } catch (error) {
      connectionStatus = 'disconnected';
      apiResponseTime = null;
    }

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
        // Try to get audio name from device state or fallback
        const device = SharedDeviceState.getDevice() as any;
        const audioName = device?.background_audio_name || 'Background Music';

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

      // Check if 'media' store exists
      if (!db.objectStoreNames.contains('media')) {
        console.warn('[DeviceInfoCollector] IndexedDB "media" store not found. Available stores:',
          Array.from(db.objectStoreNames));
        db.close();
        return [];
      }

      const transaction = db.transaction(['media'], 'readonly');
      const objectStore = transaction.objectStore('media');
      const request = objectStore.getAll();

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const items = request.result || [];
          // Debug logging with console.warn (survives production build)
          console.warn('[DeviceInfoCollector] IndexedDB Cache Items:', {
            count: items.length,
            sample: items.length > 0 ? {
              url: items[0].url,
              mime_type: items[0].mime_type,
              mimeType: items[0].mimeType, // Check both fields
              size: items[0].size,
            } : null,
            allFields: items.length > 0 ? Object.keys(items[0]) : [],
          });
          db.close();
          resolve(items);
        };
        request.onerror = () => {
          console.error('[DeviceInfoCollector] IndexedDB getAll error:', request.error);
          db.close();
          reject(request.error);
        };
      });
    } catch (error) {
      console.warn('[DeviceInfoCollector] Failed to get cached items (DB may not exist yet):', error);
      return [];
    }
  }

  /**
   * Helper: Open IndexedDB cache
   */
  private async openCacheDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('signage_media_cache', 1);

      request.onsuccess = () => {
        console.warn('[DeviceInfoCollector] IndexedDB opened successfully');
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[DeviceInfoCollector] IndexedDB open error:', request.error);
        reject(request.error);
      };

      request.onupgradeneeded = (event) => {
        // Database doesn't exist yet, create it
        console.warn('[DeviceInfoCollector] IndexedDB upgrade needed - creating store');
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('media')) {
          db.createObjectStore('media', { keyPath: 'url' });
        }
      };
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
