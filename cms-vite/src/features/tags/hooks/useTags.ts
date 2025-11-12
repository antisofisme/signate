/**
 * Tags Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for tag management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tagsApi } from '@/features/tags/api/tagsApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';
import type {
  CreateTagRequest,
  UpdateTagRequest,
  TagListFilters,
} from '../types/tag';

/**
 * Get all tags with optional sorting
 */
export function useTags(filters?: TagListFilters) {
  return useQuery({
    queryKey: ['tags', filters],
    queryFn: () => tagsApi.list(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Get single tag
 */
export function useTag(id: number) {
  return useQuery({
    queryKey: ['tags', id],
    queryFn: () => tagsApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id,
  });
}

/**
 * Get tag with usage statistics
 */
export function useTagUsage(id: number) {
  return useQuery({
    queryKey: ['tags', id, 'usage'],
    queryFn: () => tagsApi.getUsage(id),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!id,
  });
}

/**
 * Create tag mutation
 */
export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tagData: CreateTagRequest) => tagsApi.create(tagData),
    onSuccess: (data) => {
      // Invalidate tag list
      queryClient.invalidateQueries({ queryKey: ['tags'] });

      // Show success toast
      toast.success(`Tag "${data.tag_name}" berhasil dibuat`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Update tag mutation
 */
export function useUpdateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTagRequest }) =>
      tagsApi.update(id, data),
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.id] });

      // Show success toast
      toast.success(`Tag "${data.tag_name}" berhasil diupdate`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Delete tag mutation
 */
export function useDeleteTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force }: { id: number; force?: boolean }) =>
      tagsApi.delete(id, force),
    onSuccess: (_, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.removeQueries({ queryKey: ['tags', variables.id] });

      // Show success toast
      toast.success('Tag berhasil dihapus');
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Assign tag to contents mutation (bulk)
 */
export function useAssignTagToContents() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.assignToContents(tagId, contentIds),
    onSuccess: (result, variables) => {
      // Invalidate tag queries to update usage counts
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId] });

      // Invalidate content tags for all affected content
      variables.contentIds.forEach(contentId => {
        queryClient.invalidateQueries({ queryKey: ['content', contentId, 'tags'] });
      });

      // Show success toast with details
      if (result.failed > 0) {
        toast.warning(`${result.assigned} content tagged, ${result.skipped} already tagged, ${result.failed} failed`);
      } else if (result.skipped > 0) {
        toast.info(`${result.assigned} content tagged, ${result.skipped} already tagged`);
      } else {
        toast.success(`Successfully tagged ${result.assigned} content items`);
      }
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Unassign tag from contents mutation (bulk)
 */
export function useUnassignTagFromContents() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.unassignFromContents(tagId, contentIds),
    onSuccess: (result, variables) => {
      // Invalidate tag queries to update usage counts
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId] });

      // Invalidate content tags for all affected content
      variables.contentIds.forEach(contentId => {
        queryClient.invalidateQueries({ queryKey: ['content', contentId, 'tags'] });
      });

      // Show success toast
      toast.success(`Untagged ${result.unassigned} content items`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Get content tags query
 */
export function useContentTags(contentId: number) {
  return useQuery({
    queryKey: ['content', contentId, 'tags'],
    queryFn: () => tagsApi.getContentTags(contentId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!contentId,
  });
}
