/**
 * Player Background Audio Service
 * Manages looping background music independent of visual content playback
 *
 * @features
 * - Device-level or playlist-level background audio
 * - Cache-first strategy for offline playback
 * - Volume control synchronized with device settings
 * - Continuous loop
 * - Analytics logging
 */

import { SharedLogger } from '@shared/logger';
import { ServiceRegistry } from '@shared/services/service-registry';
import type { DeviceSettings } from '@player/types/player.types';
import type { PlayerMediaCache as IPlayerMediaCache } from '@player/types/player.types';

/**
 * Background Audio Player Service
 */
class PlayerBackgroundAudioClass {
  private audioElement: HTMLAudioElement | null = null;
  private currentAudioUrl: string | null = null;
  private currentAudioId: number | null = null;
  private volumeLevel: number = 75; // 0-100
  private isEnabled: boolean = true;
  private _isPlaying: boolean = false;
  private _isStopping: boolean = false;

  /**
   * Initialize background audio player
   */
  init(): void {
    if (this.audioElement) {
      SharedLogger.warn('[PlayerBackgroundAudio] Already initialized');
      return;
    }

    // Create dedicated <audio> element for background music
    this.audioElement = document.createElement('audio');
    this.audioElement.id = 'background-audio-player';
    this.audioElement.loop = true; // Continuous loop
    this.audioElement.preload = 'auto';
    this.audioElement.style.display = 'none'; // Hidden element

    // Append to body
    document.body.appendChild(this.audioElement);

    // Event listeners
    this.audioElement.addEventListener('play', () => {
      this._isPlaying = true;
      SharedLogger.log('[PlayerBackgroundAudio] 🎵 Background audio started');
    });

    this.audioElement.addEventListener('pause', () => {
      this._isPlaying = false;
      SharedLogger.log('[PlayerBackgroundAudio] ⏸️ Background audio paused');
    });

    this.audioElement.addEventListener('error', (e) => {
      // Ignore errors when intentionally stopping/clearing audio
      if (this._isStopping) {
        return;
      }
      SharedLogger.error('[PlayerBackgroundAudio] ❌ Playback error:', e);
      this._isPlaying = false;
    });

    this.audioElement.addEventListener('ended', () => {
      // Should not happen with loop=true, but handle anyway
      SharedLogger.log('[PlayerBackgroundAudio] Audio ended (loop should prevent this)');
      if (this.currentAudioUrl && this.isEnabled) {
        void this.play(); // Restart
      }
    });

    SharedLogger.log('[PlayerBackgroundAudio] ✅ Initialized');
  }

  /**
   * Load and play background audio from device settings
   *
   * @param settings Device settings containing background audio info and volume
   */
  async loadFromSettings(settings: DeviceSettings | null): Promise<void> {
    if (!settings) {
      SharedLogger.warn('[PlayerBackgroundAudio] No device settings provided');
      this.stop();
      return;
    }

    // Update volume and enabled state
    this.volumeLevel = settings.volume_level;
    this.isEnabled = settings.is_volume_enabled;

    // Check if background audio is assigned
    if (!settings.background_audio_url || !settings.background_audio_id) {
      SharedLogger.log('[PlayerBackgroundAudio] No background audio assigned');
      this.stop();
      return;
    }

    // Check if same audio is already playing
    if (this.currentAudioId === settings.background_audio_id && this._isPlaying) {
      SharedLogger.log('[PlayerBackgroundAudio] Same background audio already playing');
      // Just update volume
      this.setVolume(this.volumeLevel);
      return;
    }

    // Load new background audio
    SharedLogger.log('[PlayerBackgroundAudio] Loading background audio:', {
      id: settings.background_audio_id,
      name: settings.background_audio_name,
      url: settings.background_audio_url,
      volume: this.volumeLevel,
    });

    try {
      // Stop current audio if playing
      this.stop();

      // Cache-first strategy (same as PlayerVideoJS for audio)
      const PlayerMediaCache = ServiceRegistry.get<IPlayerMediaCache>('PlayerMediaCache');
      let finalAudioUrl = settings.background_audio_url;
      let isFromCache = false;

      if (PlayerMediaCache) {
        const cachedMedia = await PlayerMediaCache.getCachedMedia(settings.background_audio_url);

        if (cachedMedia) {
          // ✅ OFFLINE: Use cached audio
          const cachedUrl = await PlayerMediaCache.getCachedBlobURL(settings.background_audio_url);
          if (cachedUrl) {
            finalAudioUrl = cachedUrl;
            isFromCache = true;
            SharedLogger.log('[PlayerBackgroundAudio] 💾 Using cached audio (OFFLINE)');
          }
        } else {
          // 🌐 STREAMING: Load from network + trigger background download
          SharedLogger.log('[PlayerBackgroundAudio] 🌐 Streaming from network, caching in background');

          // Trigger background cache (don't wait)
          PlayerMediaCache.cacheMedia(settings.background_audio_url, settings.background_audio_id)
            .then(() => {
              SharedLogger.log('[PlayerBackgroundAudio] ✅ Background audio cached successfully');
            })
            .catch((err: Error) => {
              SharedLogger.warn('[PlayerBackgroundAudio] Cache failed:', err.message);
            });
        }
      }

      // Load audio
      if (!this.audioElement) {
        this.init();
      }

      this.audioElement!.src = finalAudioUrl;
      this.currentAudioUrl = finalAudioUrl;
      this.currentAudioId = settings.background_audio_id;

      // Set volume
      this.setVolume(this.volumeLevel);

      // Play if enabled
      if (this.isEnabled) {
        await this.play();
        SharedLogger.log(`[PlayerBackgroundAudio] ${isFromCache ? '💾 OFFLINE' : '🌐 STREAMING'} background audio playing`);
      } else {
        SharedLogger.log('[PlayerBackgroundAudio] Volume disabled, background audio loaded but not playing');
      }
    } catch (error) {
      SharedLogger.error('[PlayerBackgroundAudio] Failed to load background audio:', error);
      this._isPlaying = false;
    }
  }

  /**
   * Play background audio
   */
  async play(): Promise<void> {
    if (!this.audioElement || !this.currentAudioUrl) {
      SharedLogger.warn('[PlayerBackgroundAudio] No audio loaded');
      return;
    }

    if (!this.isEnabled) {
      SharedLogger.warn('[PlayerBackgroundAudio] Volume disabled, cannot play');
      return;
    }

    try {
      await this.audioElement.play();
    } catch (error) {
      SharedLogger.error('[PlayerBackgroundAudio] Play failed:', error);
      this._isPlaying = false;
    }
  }

  /**
   * Pause background audio
   */
  pause(): void {
    if (!this.audioElement) return;

    this.audioElement.pause();
  }

  /**
   * Stop and clear background audio
   */
  stop(): void {
    if (!this.audioElement) return;

    this._isStopping = true;
    this.audioElement.pause();
    this.audioElement.src = '';
    this.currentAudioUrl = null;
    this.currentAudioId = null;
    this._isPlaying = false;

    SharedLogger.log('[PlayerBackgroundAudio] 🛑 Stopped');

    // Reset stopping flag after a brief delay
    setTimeout(() => {
      this._isStopping = false;
    }, 100);
  }

  /**
   * Set volume level (0-100)
   */
  setVolume(level: number): void {
    if (!this.audioElement) return;

    // Clamp between 0-100
    this.volumeLevel = Math.max(0, Math.min(100, level));

    // Convert to 0.0-1.0 for HTML5 audio
    this.audioElement.volume = this.volumeLevel / 100;

    SharedLogger.log(`[PlayerBackgroundAudio] 🔊 Volume set to ${this.volumeLevel}%`);
  }

  /**
   * Enable/disable audio playback
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;

    if (!enabled && this._isPlaying) {
      this.pause();
      SharedLogger.log('[PlayerBackgroundAudio] 🔇 Disabled');
    } else if (enabled && this.currentAudioUrl && !this._isPlaying) {
      void this.play();
      SharedLogger.log('[PlayerBackgroundAudio] 🔊 Enabled');
    }
  }

  /**
   * Get current playing status
   */
  isPlaying(): boolean {
    return this._isPlaying;
  }

  /**
   * Get current audio info
   */
  getCurrentAudio(): { id: number | null; url: string | null } {
    return {
      id: this.currentAudioId,
      url: this.currentAudioUrl,
    };
  }

  /**
   * Cleanup on destroy
   */
  destroy(): void {
    this.stop();

    if (this.audioElement && this.audioElement.parentNode) {
      this.audioElement.parentNode.removeChild(this.audioElement);
    }

    this.audioElement = null;
    SharedLogger.log('[PlayerBackgroundAudio] 🗑️ Destroyed');
  }
}

// Export singleton instance
export const PlayerBackgroundAudio = new PlayerBackgroundAudioClass();

// Register to ServiceRegistry for global access
if (typeof window !== 'undefined') {
  ServiceRegistry.register('PlayerBackgroundAudio', PlayerBackgroundAudio);
}
