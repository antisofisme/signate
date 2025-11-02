/**
 * Segment Model
 * Represents an HLS video segment for offline storage in IndexedDB
 */

(function() {
  'use strict';

  class Segment {
    constructor(data = {}) {
      this.id = data.id || null; // Unique segment ID
      this.content_id = data.content_id || null; // Parent content ID
      this.url = data.url || null; // Original segment URL
      this.sequence = data.sequence || 0; // Segment sequence number
      this.duration = data.duration || 0; // Segment duration in seconds
      this.blob = data.blob || null; // Blob data for offline storage
      this.size = data.size || 0; // Blob size in bytes
      this.downloaded = data.downloaded || false;
      this.downloaded_at = data.downloaded_at || null;
    }

    /**
     * Validate segment data
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
      const errors = [];

      if (!this.content_id) {
        errors.push('Content ID is required');
      }

      if (!this.url || this.url.trim().length === 0) {
        errors.push('Segment URL is required');
      }

      if (this.sequence < 0) {
        errors.push('Sequence must be non-negative');
      }

      return {
        valid: errors.length === 0,
        errors: errors
      };
    }

    /**
     * Check if segment is downloaded
     * @returns {boolean}
     */
    isDownloaded() {
      return this.downloaded && this.blob !== null;
    }

    /**
     * Get formatted size
     * @returns {string}
     */
    getFormattedSize() {
      const bytes = this.size;

      if (bytes === 0) return '0 B';

      const k = 1024;
      const sizes = ['B', 'KB', 'MB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));

      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Get unique segment ID from URL
     * @returns {string}
     */
    getSegmentId() {
      if (this.id) return this.id;

      // Generate ID from content_id + sequence
      return `${this.content_id}_seg_${this.sequence}`;
    }

    /**
     * Mark segment as downloaded
     * @param {Blob} blob - Segment blob data
     */
    markAsDownloaded(blob) {
      this.blob = blob;
      this.size = blob.size;
      this.downloaded = true;
      this.downloaded_at = new Date().toISOString();
    }

    /**
     * Convert to IndexedDB format
     * @returns {Object}
     */
    toIndexedDB() {
      return {
        id: this.getSegmentId(),
        content_id: this.content_id,
        url: this.url,
        sequence: this.sequence,
        duration: this.duration,
        blob: this.blob,
        size: this.size,
        downloaded: this.downloaded,
        downloaded_at: this.downloaded_at
      };
    }

    /**
     * Convert to plain object (without blob for JSON)
     * @returns {Object}
     */
    toJSON() {
      return {
        id: this.getSegmentId(),
        content_id: this.content_id,
        url: this.url,
        sequence: this.sequence,
        duration: this.duration,
        size: this.size,
        downloaded: this.downloaded,
        downloaded_at: this.downloaded_at
      };
    }

    /**
     * Create Segment from IndexedDB data
     * @param {Object} data - IndexedDB record
     * @returns {Segment}
     */
    static fromIndexedDB(data) {
      return new Segment({
        id: data.id,
        content_id: data.content_id,
        url: data.url,
        sequence: data.sequence,
        duration: data.duration,
        blob: data.blob,
        size: data.size,
        downloaded: data.downloaded,
        downloaded_at: data.downloaded_at
      });
    }

    /**
     * Parse segment URL to extract sequence number
     * @param {string} url - Segment URL (e.g., segment_00001.ts)
     * @returns {number}
     */
    static parseSequenceFromURL(url) {
      const match = url.match(/segment[_-]?(\d+)\./i);
      return match ? parseInt(match[1]) : 0;
    }

    /**
     * Create Segment from HLS playlist entry
     * @param {number} contentId - Parent content ID
     * @param {string} url - Segment URL
     * @param {number} duration - Segment duration
     * @param {number} sequence - Sequence number
     * @returns {Segment}
     */
    static fromHLSPlaylist(contentId, url, duration, sequence) {
      return new Segment({
        content_id: contentId,
        url: url,
        duration: duration,
        sequence: sequence,
        downloaded: false
      });
    }
  }

  // Export to window (Vanilla JS pattern)
  window.Segment = Segment;

  console.log('[Models/Segment] Segment model loaded');

})();
