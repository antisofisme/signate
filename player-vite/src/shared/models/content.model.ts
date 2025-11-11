/**
 * Content Model
 *
 * Represents a single playable content item (video, image, or webpage)
 * with validation and utility methods.
 *
 * @features
 * - Multi-type content support (video, image, webpage)
 * - HLS video detection (.m3u8 extension)
 * - Duration and file size formatting
 * - Display title truncation
 * - File extension parsing
 * - Type-specific icon mapping
 */

import { SharedLogger } from '@shared/logger';

/**
 * Content type enumeration
 */
export type ContentType = 'video' | 'image' | 'webpage' | 'widget';

/**
 * Content metadata interface
 */
export interface ContentMetadata {
  width?: number;
  height?: number;
  fps?: number;
  codec?: string;
  bitrate?: number;
  [key: string]: any;
}

/**
 * Content data interface
 */
export interface ContentData {
  id?: number | null;
  title?: string | null;
  type?: ContentType;
  url?: string | null;
  duration?: number;
  file_size?: number;
  thumbnail_url?: string | null;
  order?: number;
  metadata?: ContentMetadata;
  widget_data?: any; // Widget configuration data
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * Validation result interface
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Content Model Class
 */
export class Content {
  id: number | null;
  title: string | null;
  type: ContentType;
  url: string | null;
  duration: number;
  file_size: number;
  thumbnail_url: string | null;
  order: number;
  metadata: ContentMetadata;
  widget_data?: any;
  created_at: string | null;
  updated_at: string | null;

  constructor(data: ContentData = {}) {
    this.id = data.id ?? null;
    this.title = data.title ?? null;
    this.type = data.type ?? 'video';
    this.url = data.url ?? null;
    this.duration = data.duration ?? 10;
    this.file_size = data.file_size ?? 0;
    this.thumbnail_url = data.thumbnail_url ?? null;
    this.order = data.order ?? 0;
    this.metadata = data.metadata ?? {};
    this.widget_data = data.widget_data;
    this.created_at = data.created_at ?? null;
    this.updated_at = data.updated_at ?? null;
  }

  /**
   * Validate content data
   */
  validate(): ValidationResult {
    const errors: string[] = [];

    if (!this.id) {
      errors.push('Content ID is required');
    }

    if (!this.title || this.title.trim().length === 0) {
      errors.push('Content title is required');
    }

    if (!['video', 'image', 'webpage', 'widget'].includes(this.type)) {
      errors.push('Invalid content type (must be: video, image, webpage, or widget)');
    }

    if (!this.url || this.url.trim().length === 0) {
      errors.push('Content URL is required');
    }

    if (this.duration <= 0) {
      errors.push('Duration must be greater than 0');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Check if content is video
   */
  isVideo(): boolean {
    return this.type === 'video';
  }

  /**
   * Check if content is image
   */
  isImage(): boolean {
    return this.type === 'image';
  }

  /**
   * Check if content is webpage
   */
  isWebpage(): boolean {
    return this.type === 'webpage';
  }

  /**
   * Get file extension from URL
   */
  getFileExtension(): string {
    if (!this.url) return '';

    const match = this.url.match(/\.([^./?#]+)(?:[?#]|$)/);
    return match ? match[1].toLowerCase() : '';
  }

  /**
   * Check if content is HLS video
   */
  isHLS(): boolean {
    const ext = this.getFileExtension();
    return this.isVideo() && ext === 'm3u8';
  }

  /**
   * Get formatted duration (HH:MM:SS or MM:SS)
   */
  getFormattedDuration(): string {
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
   */
  getFormattedSize(): string {
    const bytes = this.file_size;

    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get display title (truncate if too long)
   */
  getDisplayTitle(maxLength: number = 50): string {
    if (!this.title) return 'Untitled';

    if (this.title.length <= maxLength) {
      return this.title;
    }

    return this.title.substring(0, maxLength - 3) + '...';
  }

  /**
   * Get icon class based on content type
   */
  getIconClass(): string {
    switch (this.type) {
      case 'video':
        return 'video-icon';
      case 'image':
        return 'image-icon';
      case 'webpage':
        return 'web-icon';
      case 'widget':
        return 'widget-icon';
      default:
        return 'file-icon';
    }
  }

  /**
   * Convert to plain object for API calls
   */
  toJSON(): ContentData {
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
      widget_data: this.widget_data,
      created_at: this.created_at,
      updated_at: this.updated_at,
    };
  }

  /**
   * Create Content from API response
   */
  static fromAPI(data: any): Content {
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
      widget_data: data.widget_data,
      created_at: data.created_at,
      updated_at: data.updated_at,
    });
  }
}

SharedLogger.log('[Models/Content] Content model loaded');
