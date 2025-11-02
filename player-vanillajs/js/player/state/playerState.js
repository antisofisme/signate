/**
 * Player State Management
 * Reactive state management for playlist and playback using EventBus pattern
 */

(function() {
  'use strict';

  // Private state
  let _currentPlaylist = null;
  let _currentIndex = 0;
  let _isPlaying = false;
  let _isPaused = false;
  let _volume = 1.0;
  let _downloadedContentIds = [];

  /**
   * Player State Manager
   */
  const playerState = {
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
        console.error('[PlayerState] Invalid playlist data:', validation.errors);
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

      console.log('[PlayerState] Playlist loaded:', _currentPlaylist.name);
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

      console.log(`[PlayerState] Index changed: ${_currentIndex}/${maxIndex}`);
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

      console.log(`[PlayerState] Playing: ${playing}`);
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

      console.log(`[PlayerState] Volume: ${_volume}`);
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

      console.log('[PlayerState] Playlist cleared');
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
  window.playerState = playerState;

  console.log('[State/PlayerState] Player state manager loaded');

})();
