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
} from '../types/content';

/**
 * Get list of content with filters
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

  const response = await apiClient.get<ContentListResponse>(
    `${API_ENDPOINTS.CONTENT.LIST}?${params.toString()}`
  );

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
  await apiClient.post(API_ENDPOINTS.CONTENT.BULK_DELETE, { ids });
};

/**
 * Get content statistics
 */
export const getContentStats = async (): Promise<{
  success: boolean;
  data: {
    total_files: number;
    total_size: number;
    by_type: {
      image: { count: number; size: number };
      video: { count: number; size: number };
      audio: { count: number; size: number };
    };
  };
}> => {
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
