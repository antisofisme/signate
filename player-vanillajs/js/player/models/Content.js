/**
 * Content Model
 *
 * @class Content
 * @description
 * Represents a single playable content item (video, image, or webpage) with validation and utility methods.
 * Supports both standard video formats (MP4, WebM) and HLS streaming (m3u8).
 *
 * @features
 * - Multi-type content support (video, image, webpage)
 * - HLS video detection (.m3u8 extension)
 * - Duration and file size formatting
 * - Display title truncation
 * - File extension parsing
 * - Type-specific icon mapping
 *
 * @usage
 * ```javascript
 * // Create content from API response
 * const content = Content.fromAPI({
 *   id: 1,
 *   title: 'Product Demo Video',
 *   type: 'video',
 *   url: 'https://cdn.example.com/demo.mp4',
 *   duration: 120,
 *   file_size: 15728640
 * });
 *
 * // Check content type
 * if (content.isVideo()) {
 *   console.log('This is a video');
 * }
 *
 * // Check if HLS
 * if (content.isHLS()) {
 *   console.log('Use HLS player');
 * }
 *
 * // Get formatted duration and size
 * console.log('Duration:', content.getFormattedDuration()); // "2:00"
 * console.log('Size:', content.getFormattedSize()); // "15.0 MB"
 * ```
 *
 * @content_types
 * - **video**: MP4, WebM, HLS (.m3u8) video files
 * - **image**: JPG, PNG, GIF, WebP static images
 * - **webpage**: External URLs or HTML content
 *
 * @hls_support
 * Content with .m3u8 extension is treated as HLS stream.
 * Use `isHLS()` to detect and load with appropriate player (hls.js).
 */
(function() {
  'use strict';

  class Content {
    /**
     * Create a Content instance
     * @constructor
     * @param {Object} data - Content data from API
     * @param {number} [data.id=null] - Content unique identifier
     * @param {string} [data.title=null] - Content display title
     * @param {('video'|'image'|'webpage')} [data.type='video'] - Content type
     * @param {string} [data.url=null] - Content file URL or webpage URL
     * @param {number} [data.duration=10] - Display duration in seconds
     * @param {number} [data.file_size=0] - File size in bytes
     * @param {string} [data.thumbnail_url=null] - Thumbnail preview URL
     * @param {number} [data.order=0] - Display order in playlist
     * @param {Object} [data.metadata={}] - Additional metadata (width, height, fps, etc.)
     * @param {string} [data.created_at=null] - ISO timestamp of content creation
     * @param {string} [data.updated_at=null] - ISO timestamp of last update
     */
    constructor(data = {}) {
      /** @type {number|null} Content unique identifier */
      this.id = data.id || null;

      /** @type {string|null} Content display title */
      this.title = data.title || null;

      /** @type {('video'|'image'|'webpage')} Content type */
      this.type = data.type || 'video';

      /** @type {string|null} Content file URL or webpage URL */
      this.url = data.url || null;

      /** @type {number} Display duration in seconds (for images/webpages) or video length */
      this.duration = data.duration || 10;

      /** @type {number} File size in bytes (0 for webpages) */
      this.file_size = data.file_size || 0;

      /** @type {string|null} Thumbnail preview URL */
      this.thumbnail_url = data.thumbnail_url || null;

      /** @type {number} Display order in playlist (0-indexed) */
      this.order = data.order || 0;

      /** @type {Object} Additional metadata (width, height, fps, codec, etc.) */
      this.metadata = data.metadata || {};

      /** @type {string|null} ISO timestamp of content creation */
      this.created_at = data.created_at || null;

      /** @type {string|null} ISO timestamp of last update */
      this.updated_at = data.updated_at || null;
    }

    /**
     * Validate content data
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
      const errors = [];

      if (!this.id) {
        errors.push('Content ID is required');
      }

      if (!this.title || this.title.trim().length === 0) {
        errors.push('Content title is required');
      }

      if (!['video', 'image', 'webpage'].includes(this.type)) {
        errors.push('Invalid content type (must be: video, image, or webpage)');
      }

      if (!this.url || this.url.trim().length === 0) {
        errors.push('Content URL is required');
      }

      if (this.duration <= 0) {
        errors.push('Duration must be greater than 0');
      }

      return {
        valid: errors.length === 0,
        errors: errors
      };
    }

    /**
     * Check if content is video
     * @returns {boolean}
     */
    isVideo() {
      return this.type === 'video';
    }

    /**
     * Check if content is image
     * @returns {boolean}
     */
    isImage() {
      return this.type === 'image';
    }

    /**
     * Check if content is webpage
     * @returns {boolean}
     */
    isWebpage() {
      return this.type === 'webpage';
    }

    /**
     * Get file extension from URL
     * @returns {string}
     */
    getFileExtension() {
      if (!this.url) return '';

      const match = this.url.match(/\.([^./?#]+)(?:[?#]|$)/);
      return match ? match[1].toLowerCase() : '';
    }

    /**
     * Check if content is HLS video
     * @returns {boolean}
     */
    isHLS() {
      const ext = this.getFileExtension();
      return this.isVideo() && ext === 'm3u8';
    }

    /**
     * Get formatted duration (HH:MM:SS)
     * @returns {string}
     */
    getFormattedDuration() {
      const hours = Math.floor(this.duration / 3600);
      const minutes = Math.floor((this.duration % 3600) / 60);
      const seconds = Math.floor(this.duration % 60);

      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }
    }

    /**
     * Get formatted file size
     * @returns {string}
     */
    getFormattedSize() {
      const bytes = this.file_size;

      if (bytes === 0) return '0 B';

      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));

      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Get display title (truncate if too long)
     * @param {number} maxLength - Maximum length
     * @returns {string}
     */
    getDisplayTitle(maxLength = 50) {
      if (!this.title) return 'Untitled';

      if (this.title.length <= maxLength) {
        return this.title;
      }

      return this.title.substring(0, maxLength - 3) + '...';
    }

    /**
     * Get icon class based on content type
     * @returns {string}
     */
    getIconClass() {
      switch (this.type) {
        case 'video':
          return 'video-icon';
        case 'image':
          return 'image-icon';
        case 'webpage':
          return 'web-icon';
        default:
          return 'file-icon';
      }
    }

    /**
     * Convert to plain object for API calls
     * @returns {Object}
     */
    toJSON() {
      return {
        id: this.id,
        title: this.title,
        type: this.type,
        url: this.url,
        duration: this.duration,
        file_size: this.file_size,
        thumbnail_url: this.thumbnail_url,
        order: this.order,
        metadata: this.metadata,
        created_at: this.created_at,
        updated_at: this.updated_at
      };
    }

    /**
     * Create Content from API response
     * @param {Object} data - API response data
     * @returns {Content}
     */
    static fromAPI(data) {
      return new Content({
        id: data.id,
        title: data.title || data.name,
        type: data.type || data.content_type,
        url: data.url || data.file_url,
        duration: data.duration || 10,
        file_size: data.file_size || 0,
        thumbnail_url: data.thumbnail_url,
        order: data.order || data.sequence || 0,
        metadata: data.metadata || {},
        created_at: data.created_at,
        updated_at: data.updated_at
      });
    }
  }

  // Export to window (Vanilla JS pattern)
  window.Content = Content;

  console.log('[Models/Content] Content model loaded');

})();
