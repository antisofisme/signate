/**
 * Tags Hooks
 *
 * LAYER 2: BUSINESS LOGIC
 * React Query hooks for tag management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tagsApi } from '@/features/tags/api/tagsApi';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/shared/utils/toast';
import { useSelectedOrgId, tagKeys, contentKeys } from '@/shared/hooks';
import type {
  CreateTagRequest,
  UpdateTagRequest,
  TagListFilters,
} from '../types/tag';

// Export tag keys for use in other components
export { tagKeys };

/**
 * Get all tags with optional sorting
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export function useTags(filters?: TagListFilters) {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: tagKeys.list(orgId, filters),
    queryFn: () => tagsApi.list(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    // Note: Backend handles org filtering via JWT or X-Organization-Id header
  });
}

/**
 * Get single tag
 */
export function useTag(id: number) {
  return useQuery({
    queryKey: tagKeys.detail(id),
    queryFn: () => tagsApi.get(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!id && id > 0,
  });
}

/**
 * Get tag with usage statistics
 */
export function useTagUsage(id: number) {
  return useQuery({
    queryKey: tagKeys.usage(id),
    queryFn: () => tagsApi.getUsage(id),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!id && id > 0,
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
      queryClient.invalidateQueries({ queryKey: tagKeys.all });

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
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.id) });

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
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.removeQueries({ queryKey: tagKeys.detail(variables.id) });

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
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.assignToContents(tagId, contentIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries to update usage counts
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });

      // Force refetch ALL content list queries - more aggressive than invalidate
      // This ensures the UI updates immediately after assign
      await queryClient.refetchQueries({
        queryKey: contentKeys.all,
        exact: false,
        type: 'active'
      });

      // Invalidate content tags for all affected content
      variables.contentIds.forEach(contentId => {
        queryClient.invalidateQueries({ queryKey: ['content', 'tags', contentId] });
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
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.unassignFromContents(tagId, contentIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries to update usage counts
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });

      // Force refetch ALL content list queries - more aggressive than invalidate
      // This ensures the UI updates immediately after unassign
      await queryClient.refetchQueries({
        queryKey: contentKeys.all,
        exact: false,
        type: 'active'
      });

      // Invalidate content tags for all affected content
      variables.contentIds.forEach(contentId => {
        queryClient.invalidateQueries({ queryKey: ['content', 'tags', contentId] });
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
    queryKey: ['content', 'tags', contentId],
    queryFn: () => tagsApi.getContentTags(contentId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: !!contentId && contentId > 0,
  });
}

// =============================================================================
// DEVICE-TAG HOOKS
// =============================================================================

/**
 * Get devices assigned to a tag
 */
export function useTagDevices(tagId: number) {
  return useQuery({
    queryKey: ['tags', tagId, 'devices'],
    queryFn: () => tagsApi.getTagDevices(tagId),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!tagId && tagId > 0,
  });
}

/**
 * Assign tag to devices mutation
 */
export function useAssignTagToDevices() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, deviceIds }: { tagId: number; deviceIds: number[] }) =>
      tagsApi.assignToDevices(tagId, deviceIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId, 'devices'] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Show success toast
      if (result.failed > 0) {
        toast.warning(`${result.assigned} device(s) tagged, ${result.skipped} already tagged, ${result.failed} failed`);
      } else if (result.skipped > 0) {
        toast.info(`${result.assigned} device(s) tagged, ${result.skipped} already tagged`);
      } else {
        toast.success(`Successfully tagged ${result.assigned} device(s)`);
      }
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Unassign tag from devices mutation
 */
export function useUnassignTagFromDevices() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, deviceIds }: { tagId: number; deviceIds: number[] }) =>
      tagsApi.unassignFromDevices(tagId, deviceIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId, 'devices'] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Show success toast
      toast.success(`Untagged ${result.unassigned} device(s)`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

// =============================================================================
// PLAYBACK CONTENT ASSIGNMENT HOOKS (content_assignments.tag_id)
// Different from categorization (content_tags table)
// =============================================================================

/**
 * Get playback content assigned to a tag
 * (content from content_assignments table, NOT content_tags)
 */
export function useTagPlaybackContents(tagId: number) {
  return useQuery({
    queryKey: ['tags', tagId, 'playback-contents'],
    queryFn: () => tagsApi.getPlaybackContents(tagId),
    staleTime: 1 * 60 * 1000, // 1 minute
    enabled: !!tagId && tagId > 0,
  });
}

/**
 * Assign content to tag for PLAYBACK mutation
 * This inserts into content_assignments table (for playback on devices),
 * NOT into content_tags table (which is for categorization).
 */
export function useAssignPlaybackContentsToTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.assignPlaybackContents(tagId, contentIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId, 'playback-contents'] });

      // Invalidate device content queries (devices with this tag will get new content)
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: contentKeys.all });

      // Show success toast
      if (result.failed > 0) {
        toast.warning(`${result.assigned} content assigned for playback, ${result.skipped} already assigned, ${result.failed} failed`);
      } else if (result.skipped > 0) {
        toast.info(`${result.assigned} content assigned for playback, ${result.skipped} already assigned`);
      } else {
        toast.success(`Successfully assigned ${result.assigned} content for playback to tag`);
      }
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}

/**
 * Unassign content from tag for PLAYBACK mutation
 */
export function useUnassignPlaybackContentsFromTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, contentIds }: { tagId: number; contentIds: number[] }) =>
      tagsApi.unassignPlaybackContents(tagId, contentIds),
    onSuccess: async (result, variables) => {
      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: tagKeys.all });
      queryClient.invalidateQueries({ queryKey: tagKeys.detail(variables.tagId) });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId, 'playback-contents'] });

      // Invalidate device content queries
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: contentKeys.all });

      // Show success toast
      toast.success(`Removed ${result.unassigned} content from tag playback`);
    },
    onError: (error) => {
      const appError = handleAPIError(error);
      toast.error(appError.message);
    },
  });
}
