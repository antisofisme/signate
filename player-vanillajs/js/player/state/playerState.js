/**
 * Player State Management
 *
 * @module playerState
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
 * - Memory leak prevention via private state
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
 * ```javascript
 * // Subscribe to playlist events
 * eventBus.on('playlist:loaded', (data) => {
 *   SharedLogger.log('Playlist loaded:', data.playlist.name);
 *   SharedLogger.log('Total contents:', data.contentCount);
 * });
 *
 * // Load playlist from API
 * playerState.setPlaylist({
 *   id: 1,
 *   name: 'Morning Playlist',
 *   contents: [...]
 * });
 *
 * // Navigate content
 * playerState.playNext();
 * playerState.playPrevious();
 * playerState.setCurrentIndex(5);
 *
 * // Control playback
 * playerState.setPlaying(true);
 * playerState.setVolume(0.8);
 *
 * // Track downloads
 * playerState.markContentDownloaded(123);
 * const progress = playerState.getDownloadProgress(); // 75%
 * ```
 *
 * @playback_lifecycle
 * 1. **Load**: setPlaylist() → validates → emits playlist:loaded
 * 2. **Play**: getCurrentContent() → UI displays content
 * 3. **End**: onContentEnd() → emits player:content-ended → auto playNext()
 * 4. **Loop**: playNext() wraps to index 0 when reaching end
 *
 * @architecture
 * Uses private state encapsulated in IIFE to prevent external mutation.
 * All updates must go through public methods, ensuring validation and event emission.
 */
(function() {
  'use strict';

  // Private state
  /** @type {Playlist|null} Current playlist instance */
  let _currentPlaylist = null;

  /** @type {number} Current content index (0-indexed) */
  let _currentIndex = 0;

  /** @type {boolean} Playback state flag */
  let _isPlaying = false;

  /** @type {boolean} Pause state flag */
  let _isPaused = false;

  /** @type {number} Volume level (0.0 - 1.0) */
  let _volume = 1.0;

  /** @type {Array<number>} Downloaded content IDs for offline playback */
  let _downloadedContentIds = [];

  /**
   * Player State Manager
   * @namespace playerState
   * @global
   */
  const PlayerState = {
    /**
     * Get current playlist
     * @returns {Playlist|null}
     */
    getPlaylist() {
      return _currentPlaylist;
    },

    /**
     * Set playlist (triggers playlist:loaded event)
     * @param {Playlist|Object} playlistData - Playlist instance or plain object
     */
    setPlaylist(playlistData) {
      // Convert to Playlist model if plain object
      if (!(playlistData instanceof window.Playlist)) {
        _currentPlaylist = window.Playlist.fromAPI(playlistData);
      } else {
        _currentPlaylist = playlistData;
      }

      // Validate playlist
      const validation = _currentPlaylist.validate();
      if (!validation.valid) {
        SharedLogger.error('[PlayerState] Invalid playlist data:', validation.errors);
      }

      // Reset index
      _currentIndex = 0;

      // Emit event for reactive UI updates
      if (window.eventBus) {
        window.eventBus.emit('playlist:loaded', {
          playlist: _currentPlaylist,
          contentCount: _currentPlaylist.getContentCount(),
          totalDuration: _currentPlaylist.getTotalDuration()
        });
      }

      SharedLogger.log('[PlayerState] Playlist loaded:', _currentPlaylist.name);
    },

    /**
     * Get current content being played
     * @returns {Content|null}
     */
    getCurrentContent() {
      if (!_currentPlaylist || _currentPlaylist.contents.length === 0) {
        return null;
      }

      const contentData = _currentPlaylist.contents[_currentIndex];
      return contentData instanceof window.Content
        ? contentData
        : window.Content.fromAPI(contentData);
    },

    /**
     * Get current index
     * @returns {number}
     */
    getCurrentIndex() {
      return _currentIndex;
    },

    /**
     * Set current index (triggers player:index-changed event)
     * @param {number} index
     */
    setCurrentIndex(index) {
      if (!_currentPlaylist) return;

      const maxIndex = _currentPlaylist.contents.length - 1;
      _currentIndex = Math.max(0, Math.min(index, maxIndex));

      const currentContent = this.getCurrentContent();

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('player:index-changed', {
          index: _currentIndex,
          content: currentContent,
          total: _currentPlaylist.contents.length
        });
      }

      SharedLogger.log(`[PlayerState] Index changed: ${_currentIndex}/${maxIndex}`);
    },

    /**
     * Play next content
     */
    playNext() {
      if (!_currentPlaylist) return;

      const nextIndex = (_currentIndex + 1) % _currentPlaylist.contents.length;
      this.setCurrentIndex(nextIndex);

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('player:next', {
          index: _currentIndex,
          content: this.getCurrentContent()
        });
      }
    },

    /**
     * Play previous content
     */
    playPrevious() {
      if (!_currentPlaylist) return;

      const prevIndex = _currentIndex === 0
        ? _currentPlaylist.contents.length - 1
        : _currentIndex - 1;

      this.setCurrentIndex(prevIndex);

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('player:previous', {
          index: _currentIndex,
          content: this.getCurrentContent()
        });
      }
    },

    /**
     * Set playing state
     * @param {boolean} playing
     */
    setPlaying(playing) {
      _isPlaying = playing;
      _isPaused = !playing;

      // Emit event
      if (window.eventBus) {
        const event = playing ? 'player:playing' : 'player:paused';
        window.eventBus.emit(event, {
          content: this.getCurrentContent(),
          index: _currentIndex
        });
      }

      SharedLogger.log(`[PlayerState] Playing: ${playing}`);
    },

    /**
     * Check if playing
     * @returns {boolean}
     */
    isPlaying() {
      return _isPlaying;
    },

    /**
     * Check if paused
     * @returns {boolean}
     */
    isPaused() {
      return _isPaused;
    },

    /**
     * Set volume (0.0 - 1.0)
     * @param {number} volume
     */
    setVolume(volume) {
      _volume = Math.max(0, Math.min(1, volume));

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('player:volume-changed', _volume);
      }

      SharedLogger.log(`[PlayerState] Volume: ${_volume}`);
    },

    /**
     * Get volume
     * @returns {number}
     */
    getVolume() {
      return _volume;
    },

    /**
     * Mark content as downloaded
     * @param {number} contentId
     */
    markContentDownloaded(contentId) {
      if (!_downloadedContentIds.includes(contentId)) {
        _downloadedContentIds.push(contentId);
      }

      // Emit event
      if (window.eventBus && _currentPlaylist) {
        const progress = _currentPlaylist.getDownloadProgress(_downloadedContentIds);
        window.eventBus.emit('player:download-progress', {
          contentId: contentId,
          progress: progress,
          isComplete: _currentPlaylist.isFullyDownloaded(_downloadedContentIds)
        });
      }
    },

    /**
     * Get downloaded content IDs
     * @returns {Array<number>}
     */
    getDownloadedContentIds() {
      return [..._downloadedContentIds];
    },

    /**
     * Check if content is downloaded
     * @param {number} contentId
     * @returns {boolean}
     */
    isContentDownloaded(contentId) {
      return _downloadedContentIds.includes(contentId);
    },

    /**
     * Get download progress percentage
     * @returns {number}
     */
    getDownloadProgress() {
      if (!_currentPlaylist) return 0;
      return _currentPlaylist.getDownloadProgress(_downloadedContentIds);
    },

    /**
     * Clear playlist
     */
    clearPlaylist() {
      _currentPlaylist = null;
      _currentIndex = 0;
      _isPlaying = false;
      _isPaused = false;

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('playlist:cleared');
      }

      SharedLogger.log('[PlayerState] Playlist cleared');
    },

    /**
     * Handle content end (auto play next)
     */
    onContentEnd() {
      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('player:content-ended', {
          content: this.getCurrentContent(),
          index: _currentIndex
        });
      }

      // Auto play next
      this.playNext();
    }
  };

  // Export to window
  window.PlayerState = PlayerState;

  SharedLogger.log('[State/PlayerState Player state manager loaded');

})();
