/**
 * Content Types
 * TypeScript interfaces for Content feature
 */

export type ContentType = 'image' | 'video' | 'audio';
export type TranscodingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type UploadStatus = 'pending' | 'completed' | 'failed';

export interface Content {
  id: number;
  title: string;
  description?: string;
  content_type: ContentType;

  // URLs
  file_url: string;
  thumbnail_url?: string;
  hls_master_playlist_url?: string;

  // Display settings
  duration: number;
  is_active: boolean;

  // File metadata
  file_size: number;
  mime_type: string;
  original_filename: string;
  resolution?: string;

  // Transcoding status
  transcoding_status: TranscodingStatus;
  transcoding_progress: number;
  upload_status: UploadStatus;

  // Multi-tenant
  organization_id: number;
  uploaded_by?: number;

  // Timestamps
  created_at: string;
  updated_at?: string;
  deleted_at?: string;
  deleted_by_id?: number;
}

export interface ContentUploadData {
  file: File;
  title: string;
  description?: string;
  duration: number;
  is_active: boolean;
}

export interface ContentFilters {
  skip?: number;
  limit?: number;
  content_type?: ContentType;
  is_active?: boolean;
}

export interface ContentListResponse {
  success: boolean;
  data: Content[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  timestamp: string;
}

export interface ContentResponse {
  success: boolean;
  data: Content;
  message?: string;
  timestamp: string;
}

// Duplicate Detection Types
export interface ContentUsage {
  playlists: { id: number; name: string }[];
  tags: { id: number; name: string; color: string }[];
  devices: { id: number; name: string; via: string }[];
}

export interface DuplicateContentItem {
  id: number;
  title: string;
  original_filename: string;
  created_at: string;
  is_active: boolean;
  usage: ContentUsage;
}

export interface DuplicateGroup {
  file_hash: string;
  file_size: number;
  content_type: ContentType;
  thumbnail_url?: string;
  duplicate_count: number;
  contents: DuplicateContentItem[];
}

export interface DuplicateContentResponse {
  success: boolean;
  data: DuplicateGroup[];
  message: string;
}
