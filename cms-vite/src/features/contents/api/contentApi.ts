/**
 * Content API Service
 * All Content-related API calls
 */

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type {
  Content,
  ContentUploadData,
  ContentFilters,
  ContentListResponse,
  ContentResponse,
  DuplicateContentResponse,
} from '../types/content';

/**
 * Get list of content with filters
 * Includes cache-busting timestamp to ensure fresh data
 */
export const getContentList = async (
  filters?: ContentFilters
): Promise<ContentListResponse> => {
  const params = new URLSearchParams();

  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters?.content_type) params.append('content_type', filters.content_type);
  if (filters?.is_active !== undefined)
    params.append('is_active', filters.is_active.toString());
  if (filters?.tag_ids && filters.tag_ids.length > 0)
    params.append('tag_ids', filters.tag_ids.join(','));
  // Sorting
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_dir) params.append('sort_dir', filters.sort_dir);

  // Cache-busting: add timestamp to prevent browser/CDN caching
  params.append('_t', Date.now().toString());

  const url = `${API_ENDPOINTS.CONTENT.LIST}?${params.toString()}`;
  console.log('[contentApi] Fetching content with URL:', url);
  console.log('[contentApi] Filters received:', filters);

  const response = await apiClient.get<ContentListResponse>(url);

  console.log('[contentApi] Response received, items:', response.data.data?.length, 'total:', response.data.pagination?.total);

  return response.data;
};

/**
 * Get single content by ID
 */
export const getContent = async (id: number): Promise<ContentResponse> => {
  const response = await apiClient.get<ContentResponse>(
    API_ENDPOINTS.CONTENT.GET(id)
  );

  return response.data;
};

/**
 * Upload new content
 */
export const uploadContent = async (
  data: ContentUploadData,
  onProgress?: (progress: number) => void
): Promise<ContentResponse> => {
  const formData = new FormData();
  formData.append('file', data.file);
  formData.append('title', data.title);
  formData.append('duration', data.duration.toString());
  formData.append('is_active', data.is_active.toString());

  if (data.description) {
    formData.append('description', data.description);
  }

  const response = await apiClient.post<ContentResponse>(
    API_ENDPOINTS.CONTENT.UPLOAD,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    }
  );

  return response.data;
};

/**
 * Bulk upload multiple content files
 */
export const bulkUploadContent = async (
  files: File[],
  duration: number = 10,
  is_active: boolean = true,
  onProgress?: (progress: number) => void
): Promise<{
  success: boolean;
  data: {
    results: Array<{
      filename: string;
      status: 'success' | 'error';
      content?: Content;
      error?: string;
    }>;
    summary: {
      total: number;
      successful: number;
      failed: number;
    };
  };
  message: string;
}> => {
  const formData = new FormData();

  // Append all files
  files.forEach((file) => {
    formData.append('files', file);
  });

  formData.append('duration', duration.toString());
  formData.append('is_active', is_active.toString());

  const response = await apiClient.post(
    API_ENDPOINTS.CONTENT.BULK_UPLOAD,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    }
  );

  return response.data;
};

/**
 * Update content metadata
 */
export const updateContent = async (
  id: number,
  data: Partial<Content>
): Promise<ContentResponse> => {
  const response = await apiClient.put<ContentResponse>(
    API_ENDPOINTS.CONTENT.UPDATE(id),
    data
  );

  return response.data;
};

/**
 * Delete content
 */
export const deleteContent = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.CONTENT.DELETE(id));
};

/**
 * Download content file
 * Fetches file with auth header and triggers browser download
 */
export const downloadContent = async (id: number, filename: string): Promise<void> => {
  const response = await apiClient.get(API_ENDPOINTS.CONTENT.DOWNLOAD(id), {
    responseType: 'blob',
  });

  // Create blob URL and trigger download
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Bulk delete content
 */
export const bulkDeleteContent = async (ids: number[]): Promise<void> => {
  await apiClient.post(API_ENDPOINTS.CONTENT.BULK_DELETE, { content_ids: ids });
};

/**
 * Get list of deleted content (Recycle Bin)
 * Includes cache-busting timestamp to ensure fresh data
 */
export const getDeletedContentList = async (
  filters?: ContentFilters
): Promise<ContentListResponse> => {
  const params = new URLSearchParams();

  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters?.content_type) params.append('content_type', filters.content_type);

  // Cache-busting: add timestamp to prevent browser/CDN caching
  params.append('_t', Date.now().toString());

  const response = await apiClient.get<ContentListResponse>(
    `${API_ENDPOINTS.CONTENT.LIST_DELETED}?${params.toString()}`
  );

  return response.data;
};

/**
 * Restore deleted content from Recycle Bin
 */
export const restoreContent = async (id: number): Promise<ContentResponse> => {
  const response = await apiClient.post<ContentResponse>(
    API_ENDPOINTS.CONTENT.RESTORE(id)
  );
  return response.data;
};

/**
 * Permanently delete content (cannot be recovered)
 */
export const permanentDeleteContent = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.CONTENT.PERMANENT_DELETE(id));
};

/**
 * Get duplicate content groups with usage info
 */
export const getDuplicateContent = async (): Promise<DuplicateContentResponse> => {
  const response = await apiClient.get<DuplicateContentResponse>(
    API_ENDPOINTS.CONTENT.DUPLICATES
  );
  return response.data;
};

/**
 * Content stats data type (inner data after interceptor unwrap)
 * Note: API client interceptor unwraps { success, data } → just data
 */
export interface ContentStatsData {
  total_files: number;
  total_size_bytes: number;
  total_size_readable: string;
  by_type: {
    [key: string]: {
      count: number;
      size_bytes: number;
      size_readable: string;
    };
  };
}

/**
 * Get content statistics
 * Note: Returns unwrapped data (interceptor handles success/data wrapper)
 */
export const getContentStats = async (): Promise<ContentStatsData> => {
  const response = await apiClient.get(API_ENDPOINTS.CONTENT.STATS);
  return response.data;
};

/**
 * Format file size to human-readable string
 */
export const formatFileSize = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * Get file type from MIME type
 */
export const getFileTypeFromMime = (mimeType: string): 'image' | 'video' | 'audio' | 'unknown' => {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('audio/')) return 'audio';
  return 'unknown';
};

/**
 * Content playlist info (returned from reverse lookup)
 */
export interface ContentPlaylistInfo {
  id: number;
  item_id: number;  // For removal: DELETE /playlists/{id}/content/{item_id}
  name: string;
  description: string | null;
  is_active: boolean;
  content_count: number;
  order_index: number;
  duration: number | null;
  created_at: string | null;
}

/**
 * Get playlists containing this content (reverse lookup)
 * Returns playlists with item_id for removal operations
 */
export const getContentPlaylists = async (contentId: number): Promise<ContentPlaylistInfo[]> => {
  const response = await apiClient.get(API_ENDPOINTS.CONTENT.GET_PLAYLISTS(contentId));
  // Response structure: { success: true, data: [...], message: "..." }
  return response.data.data || response.data || [];
};
