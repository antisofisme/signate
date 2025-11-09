/**
 * Player HLS Service
 * Manages HLS video playback using HLS.js
 *
 * @features
 * - HLS.js integration for adaptive streaming
 * - Playlist management and auto-advance
 * - Error recovery and fallback
 * - Type-safe with TypeScript
 * - Support for images, videos, and URLs
 */

import Hls from 'hls.js';
import { SharedLogger } from '@shared/logger';
import type {
  PlayerHLS as IPlayerHLS,
  Playlist,
  PlaylistItem,
  PlayerState,
  PlayerConfig,
  HLSConfig,
} from '../types/player.types';

/**
 * Player HLS Class
 * Singleton pattern for HLS playback management
 */
class PlayerHLSClass implements IPlayerHLS {
  private videoElement: HTMLVideoElement | null = null;
  private hls: Hls | null = null;
  private state: PlayerState = {
    currentItemIndex: 0,
    isPlaying: false,
    currentItem: null,
    playlist: null,
    error: null,
  };

  private itemTimer: number | null = null;

  // Player configuration
  private readonly playerConfig: PlayerConfig = {
    autoplay: true,
    muted: true,
    loop: false,
    preload: 'auto',
    controls: false,
  };

  // HLS configuration
  private readonly hlsConfig: HLSConfig = {
    enableWorker: true,
    lowLatencyMode: false,
    backBufferLength: 90,
    maxBufferLength: 30,
    maxMaxBufferLength: 600,
  };

  /**
   * Initialize player with video element
   */
  init(videoElement: HTMLVideoElement): void {
    this.videoElement = videoElement;

    // Apply player configuration
    this.videoElement.autoplay = this.playerConfig.autoplay;
    this.videoElement.muted = this.playerConfig.muted;
    this.videoElement.loop = this.playerConfig.loop;
    this.videoElement.preload = this.playerConfig.preload;
    this.videoElement.controls = this.playerConfig.controls;

    // Setup event listeners
    this.setupEventListeners();

    SharedLogger.log('[PlayerHLS] Initialized');
  }

  /**
   * Load playlist and start playback
   */
  async loadPlaylist(playlist: Playlist): Promise<void> {
    if (!this.videoElement) {
      throw new Error('[PlayerHLS] Video element not initialized');
    }

    if (!playlist.items || playlist.items.length === 0) {
      throw new Error('[PlayerHLS] Playlist is empty');
    }

    this.state.playlist = playlist;
    this.state.currentItemIndex = 0;
    this.state.error = null;

    SharedLogger.log('[PlayerHLS] Playlist loaded:', {
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
    if (!this.state.playlist || !this.videoElement) {
      return;
    }

    if (index < 0 || index >= this.state.playlist.items.length) {
      SharedLogger.warn('[PlayerHLS] Invalid item index:', index);
      return;
    }

    const item = this.state.playlist.items[index];
    this.state.currentItemIndex = index;
    this.state.currentItem = item;

    SharedLogger.log('[PlayerHLS] Playing item:', {
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
      case 'url':
        await this.playURL(item);
        break;
      default:
        SharedLogger.warn('[PlayerHLS] Unsupported content type:', item.content.type);
        await this.next();
    }
  }

  /**
   * Play video content (HLS or direct)
   */
  private async playVideo(item: PlaylistItem): Promise<void> {
    if (!this.videoElement) return;

    const videoUrl = item.content.file_path || item.content.url;
    if (!videoUrl) {
      SharedLogger.error('[PlayerHLS] No video URL found');
      await this.next();
      return;
    }

    // Check if HLS is supported and needed
    if (videoUrl.includes('.m3u8') && Hls.isSupported()) {
      await this.playHLS(videoUrl);
    } else {
      // Direct video playback (MP4, WebM, etc.)
      await this.playDirect(videoUrl);
    }
  }

  /**
   * Play HLS stream
   */
  private async playHLS(url: string): Promise<void> {
    if (!this.videoElement) return;

    // Destroy previous HLS instance
    if (this.hls) {
      this.hls.destroy();
    }

    // Create new HLS instance
    this.hls = new Hls(this.hlsConfig);
    this.hls.loadSource(url);
    this.hls.attachMedia(this.videoElement);

    // Setup HLS event listeners
    this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
      SharedLogger.log('[PlayerHLS] HLS manifest parsed');
      void this.videoElement?.play();
    });

    this.hls.on(Hls.Events.ERROR, (_event, data) => {
      if (data.fatal) {
        SharedLogger.error('[PlayerHLS] Fatal HLS error:', data);
        this.handleHLSError(data);
      }
    });
  }

  /**
   * Play direct video (non-HLS)
   */
  private async playDirect(url: string): Promise<void> {
    if (!this.videoElement) return;

    this.videoElement.src = url;
    await this.videoElement.play();
    SharedLogger.log('[PlayerHLS] Playing direct video');
  }

  /**
   * Play image content
   */
  private async playImage(item: PlaylistItem): Promise<void> {
    if (!this.videoElement) return;

    // Hide video, show image overlay
    this.videoElement.style.display = 'none';

    // Create image element
    const imageElement = document.createElement('img');
    imageElement.src = item.content.file_path || item.content.url || '';
    imageElement.style.width = '100%';
    imageElement.style.height = '100%';
    imageElement.style.objectFit = 'contain';
    imageElement.id = 'temp-image';

    // Add to DOM
    this.videoElement.parentElement?.appendChild(imageElement);

    // Set timer for duration
    this.itemTimer = window.setTimeout(() => {
      void this.next();
    }, item.duration * 1000);

    SharedLogger.log('[PlayerHLS] Playing image for', item.duration, 'seconds');
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

    // Set timer for duration
    this.itemTimer = window.setTimeout(() => {
      void this.next();
    }, item.duration * 1000);

    SharedLogger.log('[PlayerHLS] Playing URL for', item.duration, 'seconds');
  }

  /**
   * Play (resume)
   */
  async play(): Promise<void> {
    if (!this.videoElement) return;

    await this.videoElement.play();
    this.state.isPlaying = true;
    SharedLogger.log('[PlayerHLS] Playback resumed');
  }

  /**
   * Pause
   */
  pause(): void {
    if (!this.videoElement) return;

    this.videoElement.pause();
    this.state.isPlaying = false;
    SharedLogger.log('[PlayerHLS] Playback paused');
  }

  /**
   * Stop playback
   */
  stop(): void {
    this.pause();
    this.clearItemTimer();
    this.cleanupTemporaryElements();

    if (this.hls) {
      this.hls.destroy();
      this.hls = null;
    }

    SharedLogger.log('[PlayerHLS] Playback stopped');
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
   * Setup video element event listeners
   */
  private setupEventListeners(): void {
    if (!this.videoElement) return;

    // Video ended - play next
    this.videoElement.addEventListener('ended', () => {
      void this.next();
    });

    // Video error - try next
    this.videoElement.addEventListener('error', (e) => {
      SharedLogger.error('[PlayerHLS] Video error:', e);
      void this.next();
    });

    // Playback started
    this.videoElement.addEventListener('playing', () => {
      this.state.isPlaying = true;
      SharedLogger.log('[PlayerHLS] Playback started');
    });

    // Playback paused
    this.videoElement.addEventListener('pause', () => {
      this.state.isPlaying = false;
    });
  }

  /**
   * Handle HLS fatal errors
   */
  private handleHLSError(data: any): void {
    switch (data.type) {
      case 'networkError':
        SharedLogger.error('[PlayerHLS] Network error, trying to recover...');
        this.hls?.startLoad();
        break;
      case 'mediaError':
        SharedLogger.error('[PlayerHLS] Media error, trying to recover...');
        this.hls?.recoverMediaError();
        break;
      default:
        SharedLogger.error('[PlayerHLS] Fatal error, skipping to next item');
        void this.next();
        break;
    }
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
   * Cleanup temporary elements (images, iframes)
   */
  private cleanupTemporaryElements(): void {
    document.getElementById('temp-image')?.remove();
    document.getElementById('temp-iframe')?.remove();

    if (this.videoElement) {
      this.videoElement.style.display = 'block';
    }
  }

  /**
   * Destroy player and cleanup
   */
  destroy(): void {
    this.stop();

    if (this.hls) {
      this.hls.destroy();
      this.hls = null;
    }

    this.state = {
      currentItemIndex: 0,
      isPlaying: false,
      currentItem: null,
      playlist: null,
      error: null,
    };

    SharedLogger.log('[PlayerHLS] Player destroyed');
  }
}

// Export singleton instance
export const PlayerHLS = new PlayerHLSClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.PlayerHLS = PlayerHLS;
}
