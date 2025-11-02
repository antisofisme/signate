/**
 * Content Model
 * Represents a single content item (video, image, webpage) with validation
 */

(function() {
  'use strict';

  class Content {
    constructor(data = {}) {
      this.id = data.id || null;
      this.title = data.title || null;
      this.type = data.type || 'video'; // video, image, webpage
      this.url = data.url || null;
      this.duration = data.duration || 10; // seconds
      this.file_size = data.file_size || 0; // bytes
      this.thumbnail_url = data.thumbnail_url || null;
      this.order = data.order || 0;
      this.metadata = data.metadata || {};
      this.created_at = data.created_at || null;
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
