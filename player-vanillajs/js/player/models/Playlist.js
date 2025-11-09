/**
 * Playlist Model
 *
 * @class Playlist
 * @description
 * Represents a scheduled content playlist with validation, computed properties, and download progress tracking.
 * Supports both default (always-active) playlists and time-scheduled playlists.
 *
 * @features
 * - Schedule-based activation (start/end time)
 * - Default playlist fallback
 * - Total duration and file size calculation
 * - Download progress tracking
 * - Content filtering by type (video, image, webpage)
 * - Human-readable size formatting
 *
 * @usage
 * ```javascript
 * // Create playlist from API response
 * const playlist = Playlist.fromAPI({
 *   id: 1,
 *   name: 'Morning Playlist',
 *   schedule_start: '2025-01-01T08:00:00Z',
 *   schedule_end: '2025-01-01T12:00:00Z',
 *   contents: [...]
 * });
 *
 * // Check if currently active
 * if (playlist.isActive()) {
 *   SharedLogger.log('Playlist is active now');
 * }
 *
 * // Get total duration
 * SharedLogger.log('Total duration:', playlist.getTotalDuration(), 'seconds');
 *
 * // Track download progress
 * const downloadedIds = [1, 2, 3];
 * const progress = playlist.getDownloadProgress(downloadedIds);
 * SharedLogger.log('Download progress:', progress + '%');
 * ```
 *
 * @scheduling
 * Playlists can be scheduled or set as default:
 * - **Scheduled**: Active only during schedule_start to schedule_end
 * - **Default**: Active when no scheduled playlist is active (is_default: true)
 * - **Priority**: Scheduled playlists override default playlist
 */
(function() {
  'use strict';

  class Playlist {
    /**
     * Create a Playlist instance
     * @constructor
     * @param {Object} data - Playlist data from API
     * @param {number} [data.id=null] - Playlist unique identifier
     * @param {string} [data.name=null] - Playlist display name
     * @param {string} [data.schedule_start=null] - ISO timestamp of schedule start
     * @param {string} [data.schedule_end=null] - ISO timestamp of schedule end
     * @param {boolean} [data.is_default=false] - Default playlist flag (fallback when no schedule active)
     * @param {number} [data.organization_id=null] - Organization/tenant ID
     * @param {Array} [data.contents=[]] - Array of Content objects
     * @param {string} [data.created_at=null] - ISO timestamp of playlist creation
     * @param {string} [data.updated_at=null] - ISO timestamp of last update
     */
    constructor(data = {}) {
      /** @type {number|null} Playlist unique identifier */
      this.id = data.id || null;

      /** @type {string|null} Playlist display name */
      this.name = data.name || null;

      /** @type {string|null} ISO timestamp of schedule start (null = no schedule) */
      this.schedule_start = data.schedule_start || null;

      /** @type {string|null} ISO timestamp of schedule end (null = no schedule) */
      this.schedule_end = data.schedule_end || null;

      /** @type {boolean} Default playlist flag (active when no scheduled playlist) */
      this.is_default = data.is_default || false;

      /** @type {number|null} Organization/tenant ID for multi-tenancy */
      this.organization_id = data.organization_id || null;

      /** @type {Array<Object>} Array of Content objects */
      this.contents = data.contents || [];

      /** @type {string|null} ISO timestamp of playlist creation */
      this.created_at = data.created_at || null;

      /** @type {string|null} ISO timestamp of last update */
      this.updated_at = data.updated_at || null;
    }

    /**
     * Validate playlist data
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
      const errors = [];

      if (!this.id) {
        errors.push('Playlist ID is required');
      }

      if (!this.name || this.name.trim().length === 0) {
        errors.push('Playlist name is required');
      }

      if (this.contents.length === 0) {
        errors.push('Playlist must have at least one content item');
      }

      return {
        valid: errors.length === 0,
        errors: errors
      };
    }

    /**
     * Get total duration of all contents (in seconds)
     * @returns {number}
     */
    getTotalDuration() {
      return this.contents.reduce((sum, content) => {
        return sum + (content.duration || 0);
      }, 0);
    }

    /**
     * Get total file size of all contents (in bytes)
     * @returns {number}
     */
    getTotalSize() {
      return this.contents.reduce((sum, content) => {
        return sum + (content.file_size || 0);
      }, 0);
    }

    /**
     * Get total file size in human-readable format
     * @returns {string}
     */
    getTotalSizeFormatted() {
      const bytes = this.getTotalSize();

      if (bytes === 0) return '0 B';

      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));

      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Get number of contents
     * @returns {number}
     */
    getContentCount() {
      return this.contents.length;
    }

    /**
     * Get contents by type
     * @param {string} type - video, image, webpage
     * @returns {Array}
     */
    getContentsByType(type) {
      return this.contents.filter(content => content.type === type);
    }

    /**
     * Check if playlist is currently active based on schedule
     * @returns {boolean}
     */
    isActive() {
      if (!this.schedule_start || !this.schedule_end) {
        return this.is_default;
      }

      const now = new Date();
      const start = new Date(this.schedule_start);
      const end = new Date(this.schedule_end);

      return now >= start && now <= end;
    }

    /**
     * Check if all content files are downloaded
     * @param {Array} downloadedIds - Array of downloaded content IDs
     * @returns {boolean}
     */
    isFullyDownloaded(downloadedIds = []) {
      return this.contents.every(content =>
        downloadedIds.includes(content.id)
      );
    }

    /**
     * Get download progress percentage
     * @param {Array} downloadedIds - Array of downloaded content IDs
     * @returns {number} Percentage (0-100)
     */
    getDownloadProgress(downloadedIds = []) {
      if (this.contents.length === 0) return 100;

      const downloadedCount = this.contents.filter(content =>
        downloadedIds.includes(content.id)
      ).length;

      return Math.round((downloadedCount / this.contents.length) * 100);
    }

    /**
     * Convert to plain object for API calls
     * @returns {Object}
     */
    toJSON() {
      return {
        id: this.id,
        name: this.name,
        schedule_start: this.schedule_start,
        schedule_end: this.schedule_end,
        is_default: this.is_default,
        organization_id: this.organization_id,
        contents: this.contents,
        created_at: this.created_at,
        updated_at: this.updated_at
      };
    }

    /**
     * Create Playlist from API response
     * @param {Object} data - API response data
     * @returns {Playlist}
     */
    static fromAPI(data) {
      return new Playlist({
        id: data.id,
        name: data.name,
        schedule_start: data.schedule_start,
        schedule_end: data.schedule_end,
        is_default: data.is_default,
        organization_id: data.organization_id,
        contents: data.contents || data.playlist_contents || [],
        created_at: data.created_at,
        updated_at: data.updated_at
      });
    }
  }

  // Export to window (Vanilla JS pattern)
  window.Playlist = Playlist;

  SharedLogger.log('[Models/Playlist] Playlist model loaded');

})();
