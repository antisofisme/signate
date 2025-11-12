/**
 * React Query Hooks for Content Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type { ContentFilters, ContentUploadData } from '../types/content';
import {
  getContentList,
  getContent,
  uploadContent,
  bulkUploadContent,
  updateContent,
  deleteContent,
  bulkDeleteContent,
  getContentStats,
} from '../api/contentApi';

// Query keys
export const contentKeys = {
  all: ['content'] as const,
  lists: () => [...contentKeys.all, 'list'] as const,
  list: (filters?: ContentFilters) => [...contentKeys.lists(), filters] as const,
  details: () => [...contentKeys.all, 'detail'] as const,
  detail: (id: number) => [...contentKeys.details(), id] as const,
  stats: () => [...contentKeys.all, 'stats'] as const,
};

/**
 * Get list of content with filters
 */
export const useContentList = (filters?: ContentFilters) => {
  return useQuery({
    queryKey: contentKeys.list(filters),
    queryFn: () => getContentList(filters),
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Get single content by ID
 */
export const useContent = (id: number, enabled = true) => {
  return useQuery({
    queryKey: contentKeys.detail(id),
    queryFn: () => getContent(id),
    enabled: enabled && id > 0,
  });
};

/**
 * Upload new content
 */
export const useUploadContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      data,
      onProgress,
    }: {
      data: ContentUploadData;
      onProgress?: (progress: number) => void;
    }) => uploadContent(data, onProgress),
    onSuccess: () => {
      // Invalidate content list to refetch
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats() });
      toast.success('Content uploaded successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to upload content';
      toast.error(message);
    },
  });
};

/**
 * Bulk upload multiple content files
 */
export const useBulkUploadContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      files,
      duration,
      is_active,
      onProgress,
    }: {
      files: File[];
      duration?: number;
      is_active?: boolean;
      onProgress?: (progress: number) => void;
    }) => bulkUploadContent(files, duration, is_active, onProgress),
    onSuccess: (response) => {
      // Invalidate content list to refetch
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats() });

      const { summary } = response.data;
      if (summary.failed > 0) {
        toast.warning(
          `${summary.successful} uploaded, ${summary.failed} failed. Check results for details.`
        );
      } else {
        toast.success(`${summary.successful} files uploaded successfully`);
      }
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to upload files';
      toast.error(message);
    },
  });
};

/**
 * Update content metadata
 */
export const useUpdateContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      updateContent(id, data),
    onSuccess: (response, variables) => {
      // Invalidate specific content and list
      queryClient.invalidateQueries({ queryKey: contentKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      toast.success('Content updated successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to update content';
      toast.error(message);
    },
  });
};

/**
 * Delete content
 */
export const useDeleteContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteContent(id),
    onSuccess: () => {
      // Invalidate content list to refetch
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats() });
      toast.success('Content deleted successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to delete content';
      toast.error(message);
    },
  });
};

/**
 * Bulk delete content
 */
export const useBulkDeleteContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => bulkDeleteContent(ids),
    onSuccess: (_, ids) => {
      // Invalidate content list to refetch
      queryClient.invalidateQueries({ queryKey: contentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats() });
      toast.success(`${ids.length} content(s) deleted successfully`);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to delete content';
      toast.error(message);
    },
  });
};

/**
 * Get content statistics
 */
export const useContentStats = () => {
  return useQuery({
    queryKey: contentKeys.stats(),
    queryFn: () => getContentStats(),
    staleTime: 60000, // 1 minute
  });
};
