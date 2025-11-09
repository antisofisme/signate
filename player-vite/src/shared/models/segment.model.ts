/**
 * Segment Model
 *
 * Represents an HLS video segment (.ts file) for offline caching in IndexedDB.
 * Used to store HLS video segments locally for offline playback capability.
 *
 * @features
 * - HLS segment blob storage in IndexedDB
 * - Download progress tracking
 * - Sequence-based ordering
 * - Size formatting
 * - Unique segment ID generation
 */

import { SharedLogger } from '@shared/logger';

/**
 * Segment data interface
 */
export interface SegmentData {
  id?: string | null;
  content_id?: number | null;
  url?: string | null;
  sequence?: number;
  duration?: number;
  blob?: Blob | null;
  size?: number;
  downloaded?: boolean;
  downloaded_at?: string | null;
}

/**
 * Validation result interface
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Segment Model Class
 */
export class Segment {
  id: string | null;
  content_id: number | null;
  url: string | null;
  sequence: number;
  duration: number;
  blob: Blob | null;
  size: number;
  downloaded: boolean;
  downloaded_at: string | null;

  constructor(data: SegmentData = {}) {
    this.id = data.id ?? null;
    this.content_id = data.content_id ?? null;
    this.url = data.url ?? null;
    this.sequence = data.sequence ?? 0;
    this.duration = data.duration ?? 0;
    this.blob = data.blob ?? null;
    this.size = data.size ?? 0;
    this.downloaded = data.downloaded ?? false;
    this.downloaded_at = data.downloaded_at ?? null;
  }

  /**
   * Validate segment data
   */
  validate(): ValidationResult {
    const errors: string[] = [];

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
      errors,
    };
  }

  /**
   * Check if segment is downloaded
   */
  isDownloaded(): boolean {
    return this.downloaded && this.blob !== null;
  }

  /**
   * Get formatted size
   */
  getFormattedSize(): string {
    const bytes = this.size;

    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get unique segment ID from URL
   */
  getSegmentId(): string {
    if (this.id) return this.id;

    // Generate ID from content_id + sequence
    return `${this.content_id}_seg_${this.sequence}`;
  }

  /**
   * Mark segment as downloaded
   */
  markAsDownloaded(blob: Blob): void {
    this.blob = blob;
    this.size = blob.size;
    this.downloaded = true;
    this.downloaded_at = new Date().toISOString();
  }

  /**
   * Convert to IndexedDB format
   */
  toIndexedDB(): SegmentData {
    return {
      id: this.getSegmentId(),
      content_id: this.content_id,
      url: this.url,
      sequence: this.sequence,
      duration: this.duration,
      blob: this.blob,
      size: this.size,
      downloaded: this.downloaded,
      downloaded_at: this.downloaded_at,
    };
  }

  /**
   * Convert to plain object (without blob for JSON)
   */
  toJSON(): Omit<SegmentData, 'blob'> {
    return {
      id: this.getSegmentId(),
      content_id: this.content_id,
      url: this.url,
      sequence: this.sequence,
      duration: this.duration,
      size: this.size,
      downloaded: this.downloaded,
      downloaded_at: this.downloaded_at,
    };
  }

  /**
   * Create Segment from IndexedDB data
   */
  static fromIndexedDB(data: SegmentData): Segment {
    return new Segment({
      id: data.id,
      content_id: data.content_id,
      url: data.url,
      sequence: data.sequence,
      duration: data.duration,
      blob: data.blob,
      size: data.size,
      downloaded: data.downloaded,
      downloaded_at: data.downloaded_at,
    });
  }

  /**
   * Parse segment URL to extract sequence number
   */
  static parseSequenceFromURL(url: string): number {
    const match = url.match(/segment[_-]?(\d+)\./i);
    return match ? parseInt(match[1]) : 0;
  }

  /**
   * Create Segment from HLS playlist entry
   */
  static fromHLSPlaylist(
    contentId: number,
    url: string,
    duration: number,
    sequence: number
  ): Segment {
    return new Segment({
      content_id: contentId,
      url,
      duration,
      sequence,
      downloaded: false,
    });
  }
}

SharedLogger.log('[Models/Segment] Segment model loaded');
