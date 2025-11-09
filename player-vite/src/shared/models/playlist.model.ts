/**
 * Playlist Model
 *
 * Represents a scheduled content playlist with validation,
 * computed properties, and download progress tracking.
 *
 * @features
 * - Schedule-based activation (start/end time)
 * - Default playlist fallback
 * - Total duration and file size calculation
 * - Download progress tracking
 * - Content filtering by type
 */

import { SharedLogger } from '@shared/logger';
import type { Content } from './content.model';

/**
 * Playlist data interface
 */
export interface PlaylistData {
  id?: number | null;
  name?: string | null;
  schedule_start?: string | null;
  schedule_end?: string | null;
  is_default?: boolean;
  organization_id?: number | null;
  contents?: any[];
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
 * Playlist Model Class
 */
export class Playlist {
  id: number | null;
  name: string | null;
  schedule_start: string | null;
  schedule_end: string | null;
  is_default: boolean;
  organization_id: number | null;
  contents: any[];
  created_at: string | null;
  updated_at: string | null;

  constructor(data: PlaylistData = {}) {
    this.id = data.id ?? null;
    this.name = data.name ?? null;
    this.schedule_start = data.schedule_start ?? null;
    this.schedule_end = data.schedule_end ?? null;
    this.is_default = data.is_default ?? false;
    this.organization_id = data.organization_id ?? null;
    this.contents = data.contents ?? [];
    this.created_at = data.created_at ?? null;
    this.updated_at = data.updated_at ?? null;
  }

  /**
   * Validate playlist data
   */
  validate(): ValidationResult {
    const errors: string[] = [];

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
      errors,
    };
  }

  /**
   * Get total duration of all contents (in seconds)
   */
  getTotalDuration(): number {
    return this.contents.reduce((sum, content) => {
      return sum + (content.duration || 0);
    }, 0);
  }

  /**
   * Get total file size of all contents (in bytes)
   */
  getTotalSize(): number {
    return this.contents.reduce((sum, content) => {
      return sum + (content.file_size || 0);
    }, 0);
  }

  /**
   * Get total file size in human-readable format
   */
  getTotalSizeFormatted(): string {
    const bytes = this.getTotalSize();

    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get number of contents
   */
  getContentCount(): number {
    return this.contents.length;
  }

  /**
   * Get contents by type
   */
  getContentsByType(type: string): any[] {
    return this.contents.filter((content) => content.type === type);
  }

  /**
   * Check if playlist is currently active based on schedule
   */
  isActive(): boolean {
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
   */
  isFullyDownloaded(downloadedIds: number[] = []): boolean {
    return this.contents.every((content) => downloadedIds.includes(content.id));
  }

  /**
   * Get download progress percentage
   */
  getDownloadProgress(downloadedIds: number[] = []): number {
    if (this.contents.length === 0) return 100;

    const downloadedCount = this.contents.filter((content) =>
      downloadedIds.includes(content.id)
    ).length;

    return Math.round((downloadedCount / this.contents.length) * 100);
  }

  /**
   * Convert to plain object for API calls
   */
  toJSON(): PlaylistData {
    return {
      id: this.id,
      name: this.name,
      schedule_start: this.schedule_start,
      schedule_end: this.schedule_end,
      is_default: this.is_default,
      organization_id: this.organization_id,
      contents: this.contents,
      created_at: this.created_at,
      updated_at: this.updated_at,
    };
  }

  /**
   * Create Playlist from API response
   */
  static fromAPI(data: any): Playlist {
    return new Playlist({
      id: data.id,
      name: data.name,
      schedule_start: data.schedule_start,
      schedule_end: data.schedule_end,
      is_default: data.is_default,
      organization_id: data.organization_id,
      contents: data.contents || data.playlist_contents || [],
      created_at: data.created_at,
      updated_at: data.updated_at,
    });
  }
}

SharedLogger.log('[Models/Playlist] Playlist model loaded');
