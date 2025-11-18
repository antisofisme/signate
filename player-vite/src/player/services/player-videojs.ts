/**
 * Player VideoJS Service
 * Manages video playback using Video.js with HTTP Streaming support
 *
 * @features
 * - Video.js integration for adaptive streaming
 * - HLS and DASH support via @videojs/http-streaming
 * - Playlist management and auto-advance
 * - Better error recovery and built-in retry logic
 * - Type-safe with TypeScript
 * - Support for images, videos, and URLs
 */

import videojs from 'video.js';
import 'video.js/dist/video-js.css'; // Import Video.js CSS
import type Player from 'video.js/dist/types/player';
import { SharedLogger } from '@shared/logger';
import { PlayerPlaybackLogger } from './player-playback-logger';
import { playerWidgetRenderer } from './player-widget-renderer';
import { ServiceRegistry } from '@shared/services/service-registry';
import type {
  PlayerVideoJS as IPlayerVideoJS,
  Playlist,
  PlaylistItem,
  PlayerState,
  PlayerConfig,
} from '../types/player.types';

/**
 * Player VideoJS Class
 * Singleton pattern for Video.js playback management
 */
class PlayerVideoJSClass implements IPlayerVideoJS {
  private videoElement: HTMLVideoElement | null = null;
  private player: Player | null = null;
  private state: PlayerState = {
    currentItemIndex: 0,
    isPlaying: false,
    currentItem: null,
    playlist: null,
    error: null,
  };

  private itemTimer: number | null = null;
  private volumeLevel: number = 75; // Default volume (0-100), can be overridden by device settings

  // Track created blob URLs for cleanup
  private activeBlobUrls: Set<string> = new Set();

  // Player configuration
  private readonly playerConfig: PlayerConfig = {
    autoplay: true,
    muted: false,  // Changed: Allow audio playback (HLS videos, audio content)
    loop: false,
    preload: 'auto',
    controls: false,
  };

  // Video.js specific options
  private readonly videojsOptions = {
    html5: {
      vhs: {
        // Video.js HTTP Streaming (for HLS/DASH)
        enableLowInitialPlaylist: true,
        smoothQualityChange: true,
        overrideNative: true,
        limitRenditionByPlayerDimensions: true,
        useNetworkInformationApi: true,
      },
      nativeAudioTracks: false,
      nativeVideoTracks: false,
    },
    liveui: false,
    fluid: false,
    fill: true,
    responsive: true,
    loadingSpinner: false, // We have our own loading UI
    bigPlayButton: false,  // No big play button for digital signage
    errorDisplay: false,   // Custom error handling
    controlBar: false,     // No controls for auto-play
  };

  /**
   * Create blob URL and track it for cleanup
   */
  private createTrackedBlobURL(blob: Blob): string {
    const blobUrl = URL.createObjectURL(blob);
    this.activeBlobUrls.add(blobUrl);
    SharedLogger.log(`[PlayerVideoJS] Created blob URL (total active: ${this.activeBlobUrls.size})`);
    return blobUrl;
  }

  /**
   * Revoke all active blob URLs
   */
  private revokeAllBlobURLs(): void {
    if (this.activeBlobUrls.size === 0) return;

    SharedLogger.log(`[PlayerVideoJS] Revoking ${this.activeBlobUrls.size} blob URLs...`);
    this.activeBlobUrls.forEach(url => {
      try {
        URL.revokeObjectURL(url);
      } catch (error) {
        SharedLogger.warn(`[PlayerVideoJS] Failed to revoke blob URL:`, error);
      }
    });
    this.activeBlobUrls.clear();
    SharedLogger.log('[PlayerVideoJS] ✅ All blob URLs revoked');
  }

  /**
   * Initialize player with video element
   */
  init(videoElement: HTMLVideoElement): void {
    this.videoElement = videoElement;

    try {
      // Initialize Video.js player
      this.player = videojs(videoElement, {
        ...this.playerConfig,
        ...this.videojsOptions,
      });

      // Setup event listeners
      this.setupEventListeners();

      SharedLogger.log('[PlayerVideoJS] ✅ Initialized successfully');
    } catch (error) {
      SharedLogger.error('[PlayerVideoJS] ❌ Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Set volume level (0-100)
   */
  setVolume(level: number): void {
    if (!this.player) return;

    this.volumeLevel = Math.max(0, Math.min(100, level));
    this.player.volume(this.volumeLevel / 100);

    SharedLogger.log(`[PlayerVideoJS] 🔊 Volume set to ${this.volumeLevel}%`);
  }

  /**
   * Load playlist and start playback
   */
  async loadPlaylist(playlist: Playlist): Promise<void> {
    if (!this.videoElement) {
      throw new Error('[PlayerVideoJS] Video element not initialized');
    }

    if (!this.player) {
      throw new Error('[PlayerVideoJS] Player not initialized');
    }

    if (!playlist.items || playlist.items.length === 0) {
      throw new Error('[PlayerVideoJS] Playlist is empty');
    }

    this.state.playlist = playlist;
    this.state.currentItemIndex = 0;
    this.state.error = null;

    SharedLogger.log('[PlayerVideoJS] Playlist loaded:', {
      name: playlist.name,
      items: playlist.items.length,
    });

    // Start playing first item
    await this.playItem(0);
  }

  /**
   * Play specific playlist item by index
   */
  private async playItem(index: number): Promise<void> {
    if (!this.state.playlist || !this.videoElement || !this.player) {
      return;
    }

    if (index < 0 || index >= this.state.playlist.items.length) {
      SharedLogger.warn('[PlayerVideoJS] Invalid item index:', index);
      return;
    }

    // Log playback end for previous item (if switching items)
    if (PlayerPlaybackLogger.hasActiveLog()) {
      await PlayerPlaybackLogger.logPlaybackEnd(false); // Not completed (skipped)
    }

    const item = this.state.playlist.items[index];
    this.state.currentItemIndex = index;
    this.state.currentItem = item;

    SharedLogger.log('[PlayerVideoJS] Playing item:', {
      index,
      name: item.content.name,
      type: item.content.type,
      duration: item.duration,
    });

    // Clear previous timer
    this.clearItemTimer();

    // Handle different content types
    switch (item.content.type) {
      case 'video':
        await this.playVideo(item);
        break;
      case 'image':
        await this.playImage(item);
        break;
      case 'audio':
        await this.playAudio(item);
        break;
      case 'url':
        await this.playURL(item);
        break;
      case 'widget':
        await this.playWidget(item);
        break;
      default:
        SharedLogger.warn('[PlayerVideoJS] Unsupported content type:', item.content.type);
        await this.next();
    }
  }

  /**
   * Play video content (HYBRID: Cache-first, then stream + background download)
   */
  private async playVideo(item: PlaylistItem): Promise<void> {
    if (!this.player || !this.videoElement) return;

    const videoUrl = item.content.file_path || item.content.url;
    if (!videoUrl) {
      SharedLogger.error('[PlayerVideoJS] No video URL found');
      await this.next();
      return;
    }

    try {
      const isHLS = videoUrl.includes('.m3u8');
      let finalUrl = videoUrl;
      let isFromCache = false;

      // HLS VIDEO: Use HLS segment caching with offline-first playback + cache validation
      if (isHLS) {
        const PlayerHLSCache = ServiceRegistry.get<any>('PlayerHLSCache');

        if (PlayerHLSCache) {
          const isCached = await PlayerHLSCache.isHLSCached(item.content_id);

          if (isCached) {
            // Check if cache is stale (content updated on server)
            const updatedAt = (item.content as any).updated_at;
            const isStale = await PlayerHLSCache.isCacheStale(item.content_id, videoUrl, updatedAt);

            if (isStale) {
              // 🔄 CACHE STALE: Content updated on server, refresh cache
              SharedLogger.log('[PlayerVideoJS] 🔄 Content updated, refreshing cache:', videoUrl);

              // Clear old cache
              await PlayerHLSCache.clearCache(item.content_id);

              // Download fresh content (streaming while caching)
              SharedLogger.log('[PlayerVideoJS] 🌐 Streaming updated content (caching in background):', videoUrl);
              PlayerHLSCache.cacheHLSContent(item.content_id, videoUrl).then(() => {
                SharedLogger.log('[PlayerVideoJS] ✅ Updated content cached:', videoUrl);
              }).catch((err: Error) => {
                SharedLogger.warn('[PlayerVideoJS] Failed to cache updated content:', err.message);
              });

              // Play from network (updated version)
              // finalUrl remains as videoUrl (network)
            } else {
              // ✅ OFFLINE HLS: Cache is fresh, play from IndexedDB using Blob URLs
              SharedLogger.log('[PlayerVideoJS] 💾 Playing HLS from cache (OFFLINE):', videoUrl);

              try {
                // Load segments from IndexedDB and create Blob playlist
                finalUrl = await this.createOfflineHLSPlaylist(item.content_id, PlayerHLSCache);
                isFromCache = true;
                SharedLogger.log('[PlayerVideoJS] ✅ Offline HLS playlist created');
              } catch (error) {
                SharedLogger.error('[PlayerVideoJS] Failed to create offline playlist, fallback to network:', error);
                // Fallback to network streaming if offline playback fails
              }
            }
          } else {
            // 🌐 STREAMING HLS: First time, play from network + cache segments in background
            SharedLogger.log('[PlayerVideoJS] 🌐 Streaming HLS (caching segments in background):', videoUrl);

            // Start background HLS segment download (non-blocking)
            PlayerHLSCache.cacheHLSContent(item.content_id, videoUrl).then(() => {
              SharedLogger.log('[PlayerVideoJS] ✅ HLS segments cached:', videoUrl);
            }).catch((err: Error) => {
              SharedLogger.warn('[PlayerVideoJS] HLS caching failed:', err.message);
            });
          }
        }
      }
      // DIRECT VIDEO: Use file-based caching
      else {
        const PlayerMediaCache = ServiceRegistry.get<any>('PlayerMediaCache');

        if (PlayerMediaCache) {
          const cachedMedia = await PlayerMediaCache.getCachedMedia(videoUrl);

          if (cachedMedia) {
            // ✅ OFFLINE: Play from cache (blob URL)
            finalUrl = await PlayerMediaCache.createBlobUrl(cachedMedia);
            isFromCache = true;
            SharedLogger.log('[PlayerVideoJS] 💾 Playing from cache (OFFLINE):', videoUrl);
          } else {
            // 🌐 STREAMING: Play from network + trigger background download
            SharedLogger.log('[PlayerVideoJS] 🌐 Streaming from network (downloading in background):', videoUrl);

            // Start background download (non-blocking)
            PlayerMediaCache.cacheMedia(videoUrl, item.content_id).then(() => {
              SharedLogger.log('[PlayerVideoJS] ✅ Background download complete:', videoUrl);
            }).catch((err: Error) => {
              SharedLogger.warn('[PlayerVideoJS] Background download failed:', err.message);
            });
          }
        }
      }

      // Video.js automatically handles HLS, DASH, and direct video
      this.player.src({
        src: finalUrl,
        type: this.getMimeType(videoUrl, item.content.mime_type || undefined),
      });

      // Show video element (might be hidden from image/url)
      this.videoElement.style.display = 'block';

      // Apply per-content mute flag and volume
      if (item.is_muted) {
        this.player.muted(true);
        SharedLogger.log('[PlayerVideoJS] 🔇 Content is muted (is_muted=true)');
      } else {
        this.player.muted(false);
        this.player.volume(this.volumeLevel / 100);
        SharedLogger.log(`[PlayerVideoJS] 🔊 Volume: ${this.volumeLevel}%`);
      }

      await this.player.play();

      SharedLogger.log(`[PlayerVideoJS] ${isFromCache ? '💾 OFFLINE' : '🌐 STREAMING'} ${isHLS ? 'HLS' : 'DIRECT'}:`, videoUrl);
    } catch (error) {
      SharedLogger.error('[PlayerVideoJS] Failed to play video:', error);
      await this.next();
    }
  }

  /**
   * Get MIME type for video source
   */
  private getMimeType(url: string, contentType?: string): string {
    if (url.includes('.m3u8')) return 'application/x-mpegURL'; // HLS
    if (url.includes('.mpd')) return 'application/dash+xml';  // DASH
    if (url.includes('.webm')) return 'video/webm';
    if (url.includes('.mp4')) return 'video/mp4';
    return contentType || 'video/mp4'; // Default fallback
  }

  /**
   * Play image content (HYBRID: Cache-first, then stream + background download)
   */
  private async playImage(item: PlaylistItem): Promise<void> {
    if (!this.videoElement) return;

    // Hide video, show image overlay
    this.videoElement.style.display = 'none';

    const imageUrl = item.content.file_path || item.content.url || '';

    // HYBRID STRATEGY: Check cache first
    const PlayerMediaCache = ServiceRegistry.get<any>('PlayerMediaCache');
    let finalImageUrl = imageUrl;
    let isFromCache = false;

    if (PlayerMediaCache && imageUrl) {
      const cachedMedia = await PlayerMediaCache.getCachedMedia(imageUrl);

      if (cachedMedia) {
        // ✅ OFFLINE: Use cached image
        finalImageUrl = await PlayerMediaCache.createBlobUrl(cachedMedia);
        isFromCache = true;
        SharedLogger.log('[PlayerVideoJS] 💾 Image from cache (OFFLINE):', imageUrl);
      } else {
        // 🌐 STREAMING: Load from network + trigger background download
        SharedLogger.log('[PlayerVideoJS] 🌐 Image from network (downloading in background):', imageUrl);

        // Start background download (non-blocking)
        PlayerMediaCache.cacheMedia(imageUrl, item.content_id).then(() => {
          SharedLogger.log('[PlayerVideoJS] ✅ Image background download complete:', imageUrl);
        }).catch((err: Error) => {
          SharedLogger.warn('[PlayerVideoJS] Image background download failed:', err.message);
        });
      }
    }

    // Create image element
    const imageElement = document.createElement('img');
    imageElement.src = finalImageUrl;
    imageElement.style.width = '100%';
    imageElement.style.height = '100%';
    imageElement.style.objectFit = 'contain';
    imageElement.id = 'temp-image';

    // Add to DOM
    this.videoElement.parentElement?.appendChild(imageElement);

    // Log playback start for analytics (images)
    if (this.state.playlist) {
      void PlayerPlaybackLogger.logPlaybackStart(item, this.state.playlist.id);
    }

    // Set timer for duration
    this.itemTimer = window.setTimeout(() => {
      // Log playback end (completed)
      void PlayerPlaybackLogger.logPlaybackEnd(true);
      void this.next();
    }, item.duration * 1000);

    SharedLogger.log(`[PlayerVideoJS] ${isFromCache ? '💾 OFFLINE' : '🌐 STREAMING'} image for`, item.duration, 'seconds');
  }

  /**
   * Play audio content (HYBRID: Cache-first, then stream + background download)
   */
  private async playAudio(item: PlaylistItem): Promise<void> {
    if (!this.player || !this.videoElement) return;

    const audioUrl = item.content.file_path || item.content.url || '';

    // HYBRID STRATEGY: Check cache first
    const PlayerMediaCache = ServiceRegistry.get<any>('PlayerMediaCache');
    let finalAudioUrl = audioUrl;
    let isFromCache = false;

    if (PlayerMediaCache && audioUrl) {
      const cachedMedia = await PlayerMediaCache.getCachedMedia(audioUrl);

      if (cachedMedia) {
        // ✅ OFFLINE: Use cached audio
        finalAudioUrl = await PlayerMediaCache.createBlobUrl(cachedMedia);
        isFromCache = true;
        SharedLogger.log('[PlayerVideoJS] 💾 Audio from cache (OFFLINE):', audioUrl);
      } else {
        // 🌐 STREAMING: Load from network + trigger background download
        SharedLogger.log('[PlayerVideoJS] 🌐 Audio from network (downloading in background):', audioUrl);

        // Start background download (non-blocking)
        PlayerMediaCache.cacheMedia(audioUrl, item.content_id).then(() => {
          SharedLogger.log('[PlayerVideoJS] ✅ Audio background download complete:', audioUrl);
        }).catch((err: Error) => {
          SharedLogger.warn('[PlayerVideoJS] Audio background download failed:', err.message);
        });
      }
    }

    // Show video element (for audio visualization or black screen)
    this.videoElement.style.display = 'block';

    // Load audio in video player
    const mimeType = this.getMimeType(finalAudioUrl);
    this.player.src({
      src: finalAudioUrl,
      type: mimeType,
    });

    // Log playback start for analytics
    if (this.state.playlist) {
      void PlayerPlaybackLogger.logPlaybackStart(item, this.state.playlist.id);
    }

    // Apply per-content mute flag and volume
    if (item.is_muted) {
      this.player.muted(true);
      SharedLogger.log('[PlayerVideoJS] 🔇 Audio is muted (is_muted=true)');
    } else {
      this.player.muted(false);
      this.player.volume(this.volumeLevel / 100);
      SharedLogger.log(`[PlayerVideoJS] 🔊 Volume: ${this.volumeLevel}%`);
    }

    // Play audio
    try {
      await this.player.play();
      SharedLogger.log(`[PlayerVideoJS] ${isFromCache ? '💾 OFFLINE' : '🌐 STREAMING'} audio playing`);

      // Set timer for duration (in case audio doesn't have metadata)
      this.itemTimer = window.setTimeout(() => {
        void PlayerPlaybackLogger.logPlaybackEnd(true);
        void this.next();
      }, item.duration * 1000);
    } catch (error) {
      SharedLogger.error('[PlayerVideoJS] Audio playback error:', error);
      void this.next();
    }
  }

  /**
   * Play URL content (iframe)
   */
  private async playURL(item: PlaylistItem): Promise<void> {
    if (!this.videoElement) return;

    // Hide video, show iframe overlay
    this.videoElement.style.display = 'none';

    // Create iframe element
    const iframeElement = document.createElement('iframe');
    iframeElement.src = item.content.url || '';
    iframeElement.style.width = '100%';
    iframeElement.style.height = '100%';
    iframeElement.style.border = 'none';
    iframeElement.id = 'temp-iframe';

    // Add to DOM
    this.videoElement.parentElement?.appendChild(iframeElement);

    // Log playback start for analytics (URLs)
    if (this.state.playlist) {
      void PlayerPlaybackLogger.logPlaybackStart(item, this.state.playlist.id);
    }

    // Set timer for duration
    this.itemTimer = window.setTimeout(() => {
      // Log playback end (completed)
      void PlayerPlaybackLogger.logPlaybackEnd(true);
      void this.next();
    }, item.duration * 1000);

    SharedLogger.log('[PlayerVideoJS] Playing URL for', item.duration, 'seconds');
  }

  /**
   * Create offline HLS playlist from cached segments
   * Loads all segments from IndexedDB and creates Blob URLs
   */
  private async createOfflineHLSPlaylist(contentId: number, cache: any): Promise<string> {
    SharedLogger.log(`[PlayerVideoJS] Creating offline HLS playlist for content ${contentId}`);

    // Get all segments from cache
    const segments = await cache.getSegments(contentId);

    if (!segments || segments.length === 0) {
      throw new Error('No segments found in cache');
    }

    SharedLogger.log(`[PlayerVideoJS] Found ${segments.length} cached segments`);

    // Create Blob URLs for each segment
    const segmentBlobUrls: string[] = [];

    for (const segment of segments) {
      // Create Blob from ArrayBuffer
      const blob = new Blob([segment.data], { type: 'video/mp2t' });
      const blobUrl = this.createTrackedBlobURL(blob); // Use tracked method
      segmentBlobUrls.push(blobUrl);
    }

    SharedLogger.log(`[PlayerVideoJS] Created ${segmentBlobUrls.length} Blob URLs`);

    // Create HLS playlist with Blob URLs
    let playlistContent = '#EXTM3U\n';
    playlistContent += '#EXT-X-VERSION:3\n';
    playlistContent += '#EXT-X-TARGETDURATION:6\n';
    playlistContent += '#EXT-X-MEDIA-SEQUENCE:0\n';

    segments.forEach((segment: any, index: number) => {
      playlistContent += `#EXTINF:${segment.duration.toFixed(1)},\n`;
      playlistContent += `${segmentBlobUrls[index]}\n`;
    });

    playlistContent += '#EXT-X-ENDLIST\n';

    // Create Blob URL for playlist
    const playlistBlob = new Blob([playlistContent], {
      type: 'application/vnd.apple.mpegurl',
    });
    const playlistUrl = this.createTrackedBlobURL(playlistBlob); // Use tracked method

    SharedLogger.log('[PlayerVideoJS] ✅ Offline HLS playlist created:', playlistUrl);
    return playlistUrl;
  }

  /**
   * Play widget content
   */
  private async playWidget(item: PlaylistItem): Promise<void> {
    if (!this.videoElement) return;

    // Hide video element
    this.videoElement.style.display = 'none';

    // Initialize widget renderer if not already
    if (!this.videoElement.parentElement?.querySelector('#widget-overlay')) {
      playerWidgetRenderer.initialize(this.videoElement.parentElement!);
    }

    // Render widgets
    await playerWidgetRenderer.renderWidgets(item.content);

    // Log playback start for analytics (widgets)
    if (this.state.playlist) {
      void PlayerPlaybackLogger.logPlaybackStart(item, this.state.playlist.id);
    }

    // Set timer for duration
    this.itemTimer = window.setTimeout(() => {
      // Clear widgets
      playerWidgetRenderer.clearWidgets();

      // Log playback end (completed)
      void PlayerPlaybackLogger.logPlaybackEnd(true);
      void this.next();
    }, item.duration * 1000);

    SharedLogger.log('[PlayerVideoJS] Playing widgets for', item.duration, 'seconds');
  }

  /**
   * Play (resume)
   */
  async play(): Promise<void> {
    if (!this.player) return;

    try {
      await this.player.play();
      this.state.isPlaying = true;
      SharedLogger.log('[PlayerVideoJS] Playback resumed');
    } catch (error) {
      SharedLogger.error('[PlayerVideoJS] Play failed:', error);
    }
  }

  /**
   * Pause
   */
  pause(): void {
    if (!this.player) return;

    this.player.pause();
    this.state.isPlaying = false;
    SharedLogger.log('[PlayerVideoJS] Playback paused');
  }

  /**
   * Stop playback
   */
  stop(): void {
    this.pause();
    this.clearItemTimer();
    this.cleanupTemporaryElements();

    if (this.player) {
      this.player.pause();
      this.player.src(''); // Clear source
    }

    SharedLogger.log('[PlayerVideoJS] Playback stopped');
  }

  /**
   * Play next item
   */
  async next(): Promise<void> {
    if (!this.state.playlist) return;

    this.cleanupTemporaryElements();

    const nextIndex = this.state.currentItemIndex + 1;

    if (nextIndex >= this.state.playlist.items.length) {
      // Loop back to first item
      await this.playItem(0);
    } else {
      await this.playItem(nextIndex);
    }
  }

  /**
   * Play previous item
   */
  async previous(): Promise<void> {
    if (!this.state.playlist) return;

    this.cleanupTemporaryElements();

    const prevIndex = this.state.currentItemIndex - 1;

    if (prevIndex < 0) {
      // Go to last item
      await this.playItem(this.state.playlist.items.length - 1);
    } else {
      await this.playItem(prevIndex);
    }
  }

  /**
   * Get current playlist item
   */
  getCurrentItem(): PlaylistItem | null {
    return this.state.currentItem;
  }

  /**
   * Get player state
   */
  getState(): PlayerState {
    return { ...this.state };
  }

  /**
   * Setup Video.js event listeners
   */
  private setupEventListeners(): void {
    if (!this.player) return;

    // Video ended - play next
    this.player.on('ended', () => {
      SharedLogger.log('[PlayerVideoJS] Video ended - advancing to next');
      // Log playback end for analytics (completed)
      void PlayerPlaybackLogger.logPlaybackEnd(true);
      void this.next();
    });

    // Video error - Video.js has better error handling
    this.player.on('error', () => {
      const error = this.player?.error();
      SharedLogger.error('[PlayerVideoJS] Video error:', error);

      if (error) {
        // Log error details
        SharedLogger.error('[PlayerVideoJS] Error code:', error.code);
        SharedLogger.error('[PlayerVideoJS] Error message:', error.message);

        // Handle specific error codes
        switch (error.code) {
          case 1: // MEDIA_ERR_ABORTED
            SharedLogger.warn('[PlayerVideoJS] Playback aborted, skipping to next');
            void this.next();
            break;
          case 2: // MEDIA_ERR_NETWORK
            SharedLogger.warn('[PlayerVideoJS] Network error, retrying once...');
            // Video.js will auto-retry, but if it fails, skip
            setTimeout(() => {
              if (this.player?.error()) {
                void this.next();
              }
            }, 3000);
            break;
          case 3: // MEDIA_ERR_DECODE
            SharedLogger.warn('[PlayerVideoJS] Decode error, skipping to next');
            void this.next();
            break;
          case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            SharedLogger.warn('[PlayerVideoJS] Source not supported, skipping to next');
            void this.next();
            break;
          default:
            SharedLogger.warn('[PlayerVideoJS] Unknown error, skipping to next');
            void this.next();
        }
      }
    });

    // Playback started
    this.player.on('playing', () => {
      this.state.isPlaying = true;
      SharedLogger.log('[PlayerVideoJS] Playback started');

      // Log playback start for analytics
      if (this.state.currentItem && this.state.playlist) {
        void PlayerPlaybackLogger.logPlaybackStart(
          this.state.currentItem,
          this.state.playlist.id
        );
      }
    });

    // Playback paused
    this.player.on('pause', () => {
      this.state.isPlaying = false;
      SharedLogger.log('[PlayerVideoJS] Playback paused');
    });

    // Waiting for data
    this.player.on('waiting', () => {
      SharedLogger.log('[PlayerVideoJS] Buffering...');
    });

    // Can play through (buffered enough)
    this.player.on('canplaythrough', () => {
      SharedLogger.log('[PlayerVideoJS] Ready to play');
    });
  }

  /**
   * Clear item timer
   */
  private clearItemTimer(): void {
    if (this.itemTimer !== null) {
      clearTimeout(this.itemTimer);
      this.itemTimer = null;
    }
  }

  /**
   * Cleanup temporary elements (images, iframes, widgets)
   */
  private cleanupTemporaryElements(): void {
    document.getElementById('temp-image')?.remove();
    document.getElementById('temp-iframe')?.remove();

    // Clear widgets
    playerWidgetRenderer.clearWidgets();

    // Revoke all blob URLs from previous item
    this.revokeAllBlobURLs();

    if (this.videoElement) {
      this.videoElement.style.display = 'block';
    }
  }

  /**
   * Destroy player and cleanup
   */
  destroy(): void {
    this.stop();

    // Revoke all blob URLs before destroying
    this.revokeAllBlobURLs();

    if (this.player) {
      this.player.dispose(); // Video.js cleanup method
      this.player = null;
    }

    // Destroy widget renderer
    playerWidgetRenderer.destroy();

    this.state = {
      currentItemIndex: 0,
      isPlaying: false,
      currentItem: null,
      playlist: null,
      error: null,
    };

    SharedLogger.log('[PlayerVideoJS] Player destroyed');
  }
}

// Export singleton instance
export const PlayerVideoJS = new PlayerVideoJSClass();

// Register to ServiceRegistry (replaces window.*)
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerVideoJS', PlayerVideoJS);

  // Expose videojs to window for compatibility and testing
  (window as any).videojs = videojs;
}
