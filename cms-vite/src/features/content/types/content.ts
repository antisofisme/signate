/**
 * Content Domain Types
 */

export type ContentType = 'image' | 'video' | 'webpage';

export interface Content {
  id: number;
  title: string;
  description?: string;
  file_type: ContentType;
  file_path: string;
  file_size?: number;
  duration?: number; // seconds for video, display duration for image
  thumbnail_path?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  organization_id: number;

  // Metadata
  width?: number;
  height?: number;
  mime_type?: string;

  // Relationships
  tags?: ContentTag[];
  translations?: ContentTranslation[];
}

export interface ContentTag {
  id: number;
  tag_name: string;
  color?: string;
}

export interface ContentTranslation {
  id: number;
  content_id: number;
  language_code: string;
  title: string;
  description?: string;
}

export interface UploadContentRequest {
  file: File;
  title: string;
  description?: string;
  duration?: number;
  tags?: number[];
}

export interface UpdateContentRequest {
  title?: string;
  description?: string;
  duration?: number;
  is_active?: boolean;
  tags?: number[];
}

export interface ContentStats {
  total_content: number;
  total_images: number;
  total_videos: number;
  total_webpages: number;
  total_size: number; // bytes
}
