/**
 * Player State Management
 *
 * @module PlayerState
 * @description
 * Reactive state management for playlist playback and content sequencing using EventBus pattern.
 * Manages playlist lifecycle: load → validate → play → next/previous → download tracking.
 *
 * @features
 * - Centralized playback state management
 * - Reactive event-driven updates via EventBus
 * - Playlist validation and error handling
 * - Auto-play next content on completion
 * - Download progress tracking
 * - Volume control
 * - Type-safe state management with TypeScript
 *
 * @events_emitted
 * - **playlist:loaded** - Playlist set/updated (payload: {playlist, contentCount, totalDuration})
 * - **playlist:cleared** - Playlist cleared (no payload)
 * - **player:index-changed** - Content index changed (payload: {index, content, total})
 * - **player:next** - Next content requested (payload: {index, content})
 * - **player:previous** - Previous content requested (payload: {index, content})
 * - **player:playing** - Playback started (payload: {content, index})
 * - **player:paused** - Playback paused (payload: {content, index})
 * - **player:content-ended** - Content playback finished (payload: {content, index})
 * - **player:volume-changed** - Volume changed (payload: number 0.0-1.0)
 * - **player:download-progress** - Content downloaded (payload: {contentId, progress, isComplete})
 *
 * @usage
 * ```typescript
 * import { PlayerState } from '@shared/state';
 *
 * // Subscribe to playlist events
 * SharedEventBus.on('playlist:loaded', (data) => {
 *   console.log('Playlist loaded:', data.playlist.name);
 *   console.log('Total contents:', data.contentCount);
 * });
 *
 * // Load playlist from API
 * PlayerState.setPlaylist({
 *   id: 1,
 *   name: 'Morning Playlist',
 *   contents: [...]
 * });
 *
 * // Navigate content
 * PlayerState.playNext();
 * PlayerState.playPrevious();
 * PlayerState.setCurrentIndex(5);
 *
 * // Control playback
 * PlayerState.setPlaying(true);
 * PlayerState.setVolume(0.8);
 *
 * // Track downloads
 * PlayerState.markContentDownloaded(123);
 * const progress = PlayerState.getDownloadProgress(); // 75%
 * ```
 *
 * @playback_lifecycle
 * 1. **Load**: setPlaylist() → validates → emits playlist:loaded
 * 2. **Play**: getCurrentContent() → UI displays content
 * 3. **End**: onContentEnd() → emits player:content-ended → auto playNext()
 * 4. **Loop**: playNext() wraps to index 0 when reaching end
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { Playlist, Content } from '@shared/models';
import type { PlaylistData } from '@shared/models';

/**
 * Player state interface
 */
export interface PlayerStateData {
  playlist: Playlist | null;
  currentIndex: number;
  isPlaying: boolean;
  isPaused: boolean;
  volume: number;
  downloadedContentIds: number[];
}

/**
 * Player State Manager Class
 * Singleton pattern for global player state management
 */
class PlayerStateClass {
  // Private state
  private currentPlaylist: Playlist | null = null;
  private currentIndex: number = 0;
  private isPlayingFlag: boolean = false;
  private isPausedFlag: boolean = false;
  private volume: number = 1.0;
  private downloadedContentIds: number[] = [];

  /**
   * Get current playlist
   */
  getPlaylist(): Playlist | null {
    return this.currentPlaylist;
  }

  /**
   * Set playlist (triggers playlist:loaded event)
   * @param playlistData - Playlist instance or plain object
   */
  setPlaylist(playlistData: Playlist | PlaylistData): void {
    // Convert to Playlist model if plain object
    if (!(playlistData instanceof Playlist)) {
      this.currentPlaylist = Playlist.fromAPI(playlistData);
    } else {
      this.currentPlaylist = playlistData;
    }

    // Validate playlist
    const validation = this.currentPlaylist.validate();
    if (!validation.valid) {
      SharedLogger.error('[PlayerState] Invalid playlist data:', validation.errors);
    }

    // Reset index
    this.currentIndex = 0;

    // Emit event for reactive UI updates
    SharedEventBus.emit('playlist:loaded', {
      playlist: this.currentPlaylist,
      contentCount: this.currentPlaylist.getContentCount(),
      totalDuration: this.currentPlaylist.getTotalDuration(),
    });

    SharedLogger.log('[PlayerState] Playlist loaded:', this.currentPlaylist.name);
  }

  /**
   * Get current content being played
   */
  getCurrentContent(): Content | null {
    if (!this.currentPlaylist || this.currentPlaylist.contents.length === 0) {
      return null;
    }

    const contentData = this.currentPlaylist.contents[this.currentIndex];
    return contentData instanceof Content ? contentData : Content.fromAPI(contentData);
  }

  /**
   * Get current index
   */
  getCurrentIndex(): number {
    return this.currentIndex;
  }

  /**
   * Set current index (triggers player:index-changed event)
   * @param index - Content index (0-based)
   */
  setCurrentIndex(index: number): void {
    if (!this.currentPlaylist) return;

    const maxIndex = this.currentPlaylist.contents.length - 1;
    this.currentIndex = Math.max(0, Math.min(index, maxIndex));

    const currentContent = this.getCurrentContent();

    // Emit event
    SharedEventBus.emit('player:index-changed', {
      index: this.currentIndex,
      content: currentContent,
      total: this.currentPlaylist.contents.length,
    });

    SharedLogger.log(`[PlayerState] Index changed: ${this.currentIndex}/${maxIndex}`);
  }

  /**
   * Play next content (wraps to beginning)
   */
  playNext(): void {
    if (!this.currentPlaylist) return;

    const nextIndex = (this.currentIndex + 1) % this.currentPlaylist.contents.length;
    this.setCurrentIndex(nextIndex);

    // Emit event
    SharedEventBus.emit('player:next', {
      index: this.currentIndex,
      content: this.getCurrentContent(),
    });
  }

  /**
   * Play previous content (wraps to end)
   */
  playPrevious(): void {
    if (!this.currentPlaylist) return;

    const prevIndex =
      this.currentIndex === 0
        ? this.currentPlaylist.contents.length - 1
        : this.currentIndex - 1;

    this.setCurrentIndex(prevIndex);

    // Emit event
    SharedEventBus.emit('player:previous', {
      index: this.currentIndex,
      content: this.getCurrentContent(),
    });
  }

  /**
   * Set playing state
   * @param playing - True to play, false to pause
   */
  setPlaying(playing: boolean): void {
    this.isPlayingFlag = playing;
    this.isPausedFlag = !playing;

    // Emit event
    const event = playing ? 'player:playing' : 'player:paused';
    SharedEventBus.emit(event, {
      content: this.getCurrentContent(),
      index: this.currentIndex,
    });

    SharedLogger.log(`[PlayerState] Playing: ${playing}`);
  }

  /**
   * Check if playing
   */
  isPlaying(): boolean {
    return this.isPlayingFlag;
  }

  /**
   * Check if paused
   */
  isPaused(): boolean {
    return this.isPausedFlag;
  }

  /**
   * Set volume (0.0 - 1.0)
   * @param newVolume - Volume level (clamped to 0.0-1.0)
   */
  setVolume(newVolume: number): void {
    this.volume = Math.max(0, Math.min(1, newVolume));

    // Emit event
    SharedEventBus.emit('player:volume-changed', this.volume);

    SharedLogger.log(`[PlayerState] Volume: ${this.volume}`);
  }

  /**
   * Get volume
   */
  getVolume(): number {
    return this.volume;
  }

  /**
   * Mark content as downloaded
   * @param contentId - Content ID
   */
  markContentDownloaded(contentId: number): void {
    if (!this.downloadedContentIds.includes(contentId)) {
      this.downloadedContentIds.push(contentId);
    }

    // Emit event
    if (this.currentPlaylist) {
      const progress = this.currentPlaylist.getDownloadProgress(this.downloadedContentIds);
      SharedEventBus.emit('player:download-progress', {
        contentId: contentId,
        progress: progress,
        isComplete: this.currentPlaylist.isFullyDownloaded(this.downloadedContentIds),
      });
    }
  }

  /**
   * Get downloaded content IDs
   */
  getDownloadedContentIds(): number[] {
    return [...this.downloadedContentIds];
  }

  /**
   * Check if content is downloaded
   * @param contentId - Content ID
   */
  isContentDownloaded(contentId: number): boolean {
    return this.downloadedContentIds.includes(contentId);
  }

  /**
   * Get download progress percentage
   */
  getDownloadProgress(): number {
    if (!this.currentPlaylist) return 0;
    return this.currentPlaylist.getDownloadProgress(this.downloadedContentIds);
  }

  /**
   * Clear playlist and reset state
   */
  clearPlaylist(): void {
    this.currentPlaylist = null;
    this.currentIndex = 0;
    this.isPlayingFlag = false;
    this.isPausedFlag = false;

    // Emit event
    SharedEventBus.emit('playlist:cleared');

    SharedLogger.log('[PlayerState] Playlist cleared');
  }

  /**
   * Handle content end (auto play next)
   */
  onContentEnd(): void {
    // Emit event
    SharedEventBus.emit('player:content-ended', {
      content: this.getCurrentContent(),
      index: this.currentIndex,
    });

    // Auto play next
    this.playNext();
  }

  /**
   * Get complete state snapshot
   */
  getState(): PlayerStateData {
    return {
      playlist: this.currentPlaylist,
      currentIndex: this.currentIndex,
      isPlaying: this.isPlayingFlag,
      isPaused: this.isPausedFlag,
      volume: this.volume,
      downloadedContentIds: [...this.downloadedContentIds],
    };
  }

  /**
   * Reset all state to defaults
   */
  reset(): void {
    this.clearPlaylist();
    this.volume = 1.0;
    this.downloadedContentIds = [];
    SharedLogger.log('[PlayerState] State reset to defaults');
  }
}

// Export singleton instance
export const PlayerState = new PlayerStateClass();

// Make available globally for debugging
declare global {
  interface Window {
    PlayerState: typeof PlayerState;
  }
}

if (typeof window !== 'undefined') {
  window.PlayerState = PlayerState;
}

SharedLogger.log('[State/PlayerState] Player state manager loaded');
