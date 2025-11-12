/**
 * React Query Hooks for Playlist Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { playlistApi } from '../api/playlistApi';
import type {
  CreatePlaylistRequest,
  UpdatePlaylistRequest,
  AddContentRequest,
  ReorderContentRequest,
  AssignDevicesRequest,
  AssignTagsRequest,
} from '../types/playlist';

// Query keys factory
export const playlistKeys = {
  all: ['playlists'] as const,
  lists: () => [...playlistKeys.all, 'list'] as const,
  list: (filters?: any) => [...playlistKeys.lists(), filters] as const,
  details: () => [...playlistKeys.all, 'detail'] as const,
  detail: (id: number) => [...playlistKeys.details(), id] as const,
  content: (id: number) => [...playlistKeys.detail(id), 'content'] as const,
  assignments: (id: number) => [...playlistKeys.detail(id), 'assignments'] as const,
};

/**
 * Get list of playlists
 */
export const usePlaylistList = (filters?: { is_active?: boolean; skip?: number; limit?: number }) => {
  return useQuery({
    queryKey: playlistKeys.list(filters),
    queryFn: () => playlistApi.list(filters),
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Get single playlist by ID
 */
export const usePlaylist = (id: number, enabled = true) => {
  return useQuery({
    queryKey: playlistKeys.detail(id),
    queryFn: () => playlistApi.get(id),
    enabled: enabled && id > 0,
  });
};

/**
 * Get playlist content items
 */
export const usePlaylistContent = (id: number, enabled = true) => {
  return useQuery({
    queryKey: playlistKeys.content(id),
    queryFn: () => playlistApi.getContent(id),
    enabled: enabled && id > 0,
  });
};

/**
 * Get playlist assignments (devices & tags)
 */
export const usePlaylistAssignments = (id: number, enabled = true) => {
  return useQuery({
    queryKey: playlistKeys.assignments(id),
    queryFn: () => playlistApi.getAssignments(id),
    enabled: enabled && id > 0,
  });
};

/**
 * Create new playlist
 */
export const useCreatePlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePlaylistRequest) => playlistApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists() });
      toast.success('Playlist created successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to create playlist');
    },
  });
};

/**
 * Update playlist
 */
export const useUpdatePlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlaylistRequest }) =>
      playlistApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists() });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.id) });
      toast.success('Playlist updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to update playlist');
    },
  });
};

/**
 * Delete playlist
 */
export const useDeletePlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => playlistApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists() });
      toast.success('Playlist deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to delete playlist');
    },
  });
};

// ========================================
// Content Management Hooks
// ========================================

/**
 * Add content to playlist
 */
export const useAddContentToPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AddContentRequest }) =>
      playlistApi.addContent(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.id) });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.id) });

      if (result.skipped_missing && result.skipped_missing.length > 0) {
        toast.warning(`${result.added} items added, ${result.skipped_missing.length} not found`);
      } else if (result.skipped_duplicate && result.skipped_duplicate.length > 0) {
        toast.warning(`${result.added} items added, ${result.skipped_duplicate.length} already exist`);
      } else {
        toast.success(`${result.added} content items added`);
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to add content');
    },
  });
};

/**
 * Remove content from playlist
 */
export const useRemoveContentFromPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ playlistId, itemId }: { playlistId: number; itemId: number }) =>
      playlistApi.removeContent(playlistId, itemId),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.playlistId) });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.playlistId) });
      toast.success('Content removed from playlist');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to remove content');
    },
  });
};

/**
 * Reorder playlist content
 */
export const useReorderPlaylistContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ReorderContentRequest }) =>
      playlistApi.reorderContent(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.id) });
      toast.success('Content reordered successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to reorder content');
    },
  });
};

// ========================================
// Assignment Management Hooks
// ========================================

/**
 * Assign playlist to devices
 */
export const useAssignPlaylistToDevices = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignDevicesRequest }) =>
      playlistApi.assignDevices(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });
      toast.success(`Assigned to ${result.assigned} devices`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to assign devices');
    },
  });
};

/**
 * Assign playlist to tags
 */
export const useAssignPlaylistToTags = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignTagsRequest }) =>
      playlistApi.assignTags(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });
      toast.success(`Assigned to ${result.assigned} tags`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to assign tags');
    },
  });
};

/**
 * Unassign playlist from devices
 */
export const useUnassignPlaylistFromDevices = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignDevicesRequest }) =>
      playlistApi.unassignDevices(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });
      toast.success(`Unassigned from ${result.removed} devices`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to unassign devices');
    },
  });
};

/**
 * Unassign playlist from tags
 */
export const useUnassignPlaylistFromTags = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignTagsRequest }) =>
      playlistApi.unassignTags(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });
      toast.success(`Unassigned from ${result.removed} tags`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to unassign tags');
    },
  });
};
