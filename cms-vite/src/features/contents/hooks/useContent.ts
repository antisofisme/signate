/**
 * React Query Hooks for Content Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/lib/notifications/toast';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { useSelectedOrgId, contentKeys as sharedContentKeys } from '@/shared/hooks';
import { useAuthStore } from '@/lib/stores/authStore';
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
  getDeletedContentList,
  restoreContent,
  permanentDeleteContent,
  getDuplicateContent,
} from '../api/contentApi';

// Re-export shared content keys for backward compatibility
export const contentKeys = sharedContentKeys;

/**
 * Get list of content with filters
 *
 * Query key includes orgId for proper cache isolation between organizations.
 * CRITICAL: Only fetch when orgId is available (after auth store hydration)
 * to prevent query key mismatch between undefined and actual orgId.
 */
export const useContentList = (filters?: ContentFilters) => {
  const orgId = useSelectedOrgId();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  return useQuery({
    queryKey: contentKeys.list(orgId, filters),
    queryFn: () => {
      console.log('[useContentList] Fetching content list, orgId:', orgId);
      return getContentList(filters);
    },
    // CRITICAL: Disable all caching to ensure fresh data
    staleTime: 0,
    gcTime: 0, // Don't cache at all
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    // Wait for auth store hydration AND orgId
    enabled: hasHydrated && !!orgId,
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
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({
      data,
      onProgress,
    }: {
      data: ContentUploadData;
      onProgress?: (progress: number) => void;
    }) => uploadContent(data, onProgress),
    onSuccess: () => {
      // Refetch content list so new upload appears immediately
      queryClient.invalidateQueries({
        queryKey: contentKeys.lists(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });
      // Stats can be lazy-loaded (not critical for UX)
      queryClient.invalidateQueries({
        queryKey: contentKeys.stats(orgId),
        refetchType: 'none'
      });
      // Invalidate quota since storage changed
      queryClient.invalidateQueries({
        queryKey: ['organization-quota'],
        refetchType: 'none'
      });

      toast.success('Content uploaded successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Bulk upload multiple content files
 */
export const useBulkUploadContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

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
      // Refetch content list so new uploads appear immediately
      queryClient.invalidateQueries({
        queryKey: contentKeys.lists(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });
      // Stats can be lazy-loaded (not critical for UX)
      queryClient.invalidateQueries({
        queryKey: contentKeys.stats(orgId),
        refetchType: 'none'
      });
      queryClient.invalidateQueries({
        queryKey: ['organization-quota'],
        refetchType: 'none'
      });

      const { summary } = response.data;
      if (summary.failed > 0) {
        toast.warning(
          `${summary.successful} uploaded, ${summary.failed} failed. Check results for details.`
        );
      } else {
        toast.success(`${summary.successful} files uploaded successfully`);
      }
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Update content metadata
 */
export const useUpdateContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      updateContent(id, data),
    onSuccess: (response, variables) => {
      // Invalidate specific content and list
      queryClient.invalidateQueries({ queryKey: contentKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: contentKeys.lists(orgId) });
      toast.success('Content updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Delete content with optimistic update for instant UI feedback
 */
export const useDeleteContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (id: number) => deleteContent(id),
    // Optimistic update: Remove from UI immediately
    onMutate: async (deletedId: number) => {
      // Cancel any outgoing refetches to prevent race conditions
      // Use orgId to match the exact query keys used by useContentList
      await queryClient.cancelQueries({ queryKey: contentKeys.lists(orgId) });

      // Snapshot previous value for rollback
      const previousLists = queryClient.getQueriesData({ queryKey: contentKeys.lists(orgId) });

      // Optimistically update all content list caches
      // Handle both response formats: { data: [...] } or { data: { items: [...] } }
      queryClient.setQueriesData(
        { queryKey: contentKeys.lists(orgId) },
        (old: any) => {
          if (!old?.data) return old;

          // Format 1: data is array directly (API response)
          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.filter((item: any) => item.id !== deletedId),
            };
          }

          // Format 2: data has items array (paginated response)
          if (old.data.items) {
            return {
              ...old,
              data: {
                ...old.data,
                items: old.data.items.filter((item: any) => item.id !== deletedId),
                total: Math.max(0, (old.data.total || 0) - 1),
              },
            };
          }

          return old;
        }
      );

      return { previousLists };
    },
    onSuccess: () => {
      // Show toast
      toast.success('Content deleted successfully');

      // Invalidate deleted content list so recycle bin updates immediately
      queryClient.invalidateQueries({
        queryKey: contentKeys.deletedLists(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });

      // Invalidate duplicates - count will change after delete
      queryClient.invalidateQueries({
        queryKey: contentKeys.duplicates(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });

      // Mark stats as stale (will refetch on next view, not immediately)
      queryClient.invalidateQueries({
        queryKey: contentKeys.stats(orgId),
        refetchType: 'none'  // Don't refetch now, just mark stale
      });
    },
    onError: (error: unknown, _deletedId, context) => {
      // Rollback on error
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Bulk delete content with optimistic update
 */
export const useBulkDeleteContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (ids: number[]) => bulkDeleteContent(ids),
    // Optimistic update: Remove from UI immediately
    onMutate: async (deletedIds: number[]) => {
      // Use orgId to match the exact query keys used by useContentList
      await queryClient.cancelQueries({ queryKey: contentKeys.lists(orgId) });

      const previousLists = queryClient.getQueriesData({ queryKey: contentKeys.lists(orgId) });

      // Handle both response formats
      queryClient.setQueriesData(
        { queryKey: contentKeys.lists(orgId) },
        (old: any) => {
          if (!old?.data) return old;

          // Format 1: data is array directly
          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.filter((item: any) => !deletedIds.includes(item.id)),
            };
          }

          // Format 2: data has items array
          if (old.data.items) {
            return {
              ...old,
              data: {
                ...old.data,
                items: old.data.items.filter((item: any) => !deletedIds.includes(item.id)),
                total: Math.max(0, (old.data.total || 0) - deletedIds.length),
              },
            };
          }

          return old;
        }
      );

      return { previousLists };
    },
    onSuccess: (_, ids) => {
      // Show toast
      toast.success(`${ids.length} content(s) deleted successfully`);

      // Invalidate deleted content list so recycle bin updates immediately
      queryClient.invalidateQueries({
        queryKey: contentKeys.deletedLists(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });

      // Invalidate duplicates - count will change after delete
      queryClient.invalidateQueries({
        queryKey: contentKeys.duplicates(orgId),
        refetchType: 'active'  // Refetch active queries immediately
      });

      // Mark stats as stale (will refetch on next view)
      queryClient.invalidateQueries({
        queryKey: contentKeys.stats(orgId),
        refetchType: 'none'
      });
    },
    onError: (error: unknown, _deletedIds, context) => {
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Get content statistics
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export const useContentStats = () => {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: contentKeys.stats(orgId),
    queryFn: () => getContentStats(),
    staleTime: 60000, // 1 minute
    // Note: Backend handles org filtering via JWT or X-Organization-Id header
  });
};

// ==============================================================================
// Deleted Content (Recycle Bin) Hooks
// ==============================================================================

/**
 * Get list of deleted content (Recycle Bin)
 */
export const useDeletedContentList = (filters?: ContentFilters) => {
  const orgId = useSelectedOrgId();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);

  return useQuery({
    queryKey: contentKeys.deleted(orgId, filters),
    queryFn: () => getDeletedContentList(filters),
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    enabled: hasHydrated && !!orgId,
  });
};

/**
 * Restore deleted content from Recycle Bin
 */
export const useRestoreContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (id: number) => restoreContent(id),
    onSuccess: () => {
      // Invalidate both active and deleted lists
      queryClient.invalidateQueries({ queryKey: contentKeys.lists(orgId) });
      queryClient.invalidateQueries({ queryKey: contentKeys.deletedLists(orgId) });
      queryClient.invalidateQueries({ queryKey: contentKeys.stats(orgId), refetchType: 'none' });
      toast.success('Content restored successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Permanently delete content (cannot be recovered)
 */
export const usePermanentDeleteContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (id: number) => permanentDeleteContent(id),
    // Optimistic update: Remove from UI immediately
    onMutate: async (deletedId: number) => {
      await queryClient.cancelQueries({ queryKey: contentKeys.deletedLists(orgId) });
      const previousLists = queryClient.getQueriesData({ queryKey: contentKeys.deletedLists(orgId) });

      queryClient.setQueriesData(
        { queryKey: contentKeys.deletedLists(orgId) },
        (old: any) => {
          if (!old?.data) return old;

          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.filter((item: any) => item.id !== deletedId),
            };
          }

          if (old.data.items) {
            return {
              ...old,
              data: {
                ...old.data,
                items: old.data.items.filter((item: any) => item.id !== deletedId),
                total: Math.max(0, (old.data.total || 0) - 1),
              },
            };
          }

          return old;
        }
      );

      return { previousLists };
    },
    onSuccess: () => {
      toast.success('Content permanently deleted');
      queryClient.invalidateQueries({ queryKey: contentKeys.stats(orgId), refetchType: 'none' });
    },
    onError: (error: unknown, _deletedId, context) => {
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Bulk permanently delete content (cannot be recovered)
 * Deletes multiple items sequentially
 */
export const useBulkPermanentDeleteContent = () => {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: async (ids: number[]) => {
      // Delete each item sequentially
      for (const id of ids) {
        await permanentDeleteContent(id);
      }
    },
    // Optimistic update: Remove from UI immediately
    onMutate: async (deletedIds: number[]) => {
      await queryClient.cancelQueries({ queryKey: contentKeys.deletedLists(orgId) });
      const previousLists = queryClient.getQueriesData({ queryKey: contentKeys.deletedLists(orgId) });

      queryClient.setQueriesData(
        { queryKey: contentKeys.deletedLists(orgId) },
        (old: any) => {
          if (!old?.data) return old;

          if (Array.isArray(old.data)) {
            return {
              ...old,
              data: old.data.filter((item: any) => !deletedIds.includes(item.id)),
              pagination: old.pagination ? {
                ...old.pagination,
                total: Math.max(0, (old.pagination.total || 0) - deletedIds.length),
              } : undefined,
            };
          }

          return old;
        }
      );

      return { previousLists };
    },
    onSuccess: (_, ids) => {
      toast.success(`${ids.length} item(s) permanently deleted`);
      queryClient.invalidateQueries({ queryKey: contentKeys.stats(orgId), refetchType: 'none' });
    },
    onError: (error: unknown, _deletedIds, context) => {
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      toast.error(handleAPIError(error).message);
    },
  });
};

// ==============================================================================
// Duplicate Content Detection Hooks
// ==============================================================================

/**
 * Get duplicate content groups with usage info
 * Shows content that share the same file hash (identical files)
 */
export const useDuplicateContent = () => {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: contentKeys.duplicates(orgId),
    queryFn: () => getDuplicateContent(),
    staleTime: 60000, // 1 minute
    enabled: !!orgId,
  });
};
