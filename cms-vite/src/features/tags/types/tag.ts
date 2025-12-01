/**
 * Tag Management Domain Types
 */

import type { SuccessResponse } from '@/lib/api/responseTypes';

export interface Tag {
  id: number;
  tag_name: string;
  description: string | null;
  color: string;
  organization_id: number;
  created_at: string;
  // Computed counts
  device_count: number;
  content_count: number;
}

export interface TagUsage {
  device_count: number;
  content_count: number;
}

export interface TagWithUsage {
  tag: Tag;
  usage: TagUsage;
}

export interface CreateTagRequest {
  tag_name: string;
  description?: string | null;
  color?: string;
}

export interface UpdateTagRequest {
  tag_name?: string;
  description?: string | null;
  color?: string;
}

export type TagSortBy = 'newest' | 'oldest' | 'name_asc' | 'name_desc';

export interface TagListData {
  data: Tag[];
  total: number;
}

export interface TagListFilters {
  sort_by?: TagSortBy;
}

export type TagResponse = SuccessResponse<Tag>;
export type TagListResponse = SuccessResponse<TagListData>;
export type TagWithUsageResponse = SuccessResponse<TagWithUsage>;
export type TagDeleteResponse = SuccessResponse<{ message: string }>;
