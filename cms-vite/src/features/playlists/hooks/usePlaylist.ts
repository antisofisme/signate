/**
 * React Query Hooks for Playlist Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/shared/utils/types';
import { useSelectedOrgId, playlistKeys as sharedPlaylistKeys } from '@/shared/hooks';
import { playlistApi } from '../api/playlistApi';
import type {
  CreatePlaylistRequest,
  UpdatePlaylistRequest,
  AddContentRequest,
  ReorderContentRequest,
  AssignDevicesRequest,
} from '../types/playlist';

// Re-export shared playlist keys for backward compatibility
export const playlistKeys = sharedPlaylistKeys;

/**
 * Get list of playlists
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export const usePlaylistList = (filters?: { is_active?: boolean; skip?: number; limit?: number }) => {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: playlistKeys.list(orgId, filters),
    queryFn: () => playlistApi.list(filters),
    staleTime: 30000, // 30 seconds
    // Note: Backend handles org filtering via JWT or X-Organization-Id header
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
 * Get playlist assignments (devices only)
 * NOTE: Tag assignments have been removed - Tags are NOT assigned to Playlists
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
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (data: CreatePlaylistRequest) => playlistApi.create(data),
    onSuccess: () => {
      // Invalidate with orgId to match the actual query key
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      // Invalidate dashboard queries (playlist count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(t('playlists.messages.createSuccess'));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.createError')));
    },
  });
};

/**
 * Update playlist
 */
export const useUpdatePlaylist = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlaylistRequest }) =>
      playlistApi.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate with orgId to match the actual query key
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.id) });
      toast.success(t('playlists.messages.updateSuccess'));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.updateError')));
    },
  });
};

/**
 * Delete playlist
 */
export const useDeletePlaylist = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: (id: number) => playlistApi.delete(id),
    onSuccess: () => {
      // Invalidate with orgId to match the actual query key
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      // Invalidate device queries (devices may have had this playlist assigned)
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Invalidate device-side playlist queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'playlists'] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'playlists'] });

      // Invalidate schedule queries (schedules may reference this playlist)
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] });
      queryClient.invalidateQueries({ queryKey: ['playlist-schedules'] });

      // Invalidate dashboard queries (playlist count and active playlists change)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(t('playlists.messages.deleteSuccess'));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.deleteError')));
    },
  });
};

/**
 * Duplicate playlist with all contents
 */
export const useDuplicatePlaylist = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, newName }: { id: number; newName?: string }) =>
      playlistApi.duplicate(id, newName),
    onSuccess: (newPlaylist) => {
      // Invalidate with orgId to match the actual query key
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      // Invalidate dashboard queries (playlist count changes)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(t('playlists.messages.duplicateSuccess', { name: newPlaylist.name }));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.duplicateError')));
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
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AddContentRequest }) =>
      playlistApi.addContent(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.id) });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.id) });
      // Also refresh playlist list to update content_count
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      if (result.skipped_missing && result.skipped_missing.length > 0) {
        toast.warning(t('playlists.messages.addContentPartialMissing', { added: result.added, missing: result.skipped_missing.length }));
      } else if (result.skipped_duplicate && result.skipped_duplicate.length > 0) {
        toast.warning(t('playlists.messages.addContentPartialDuplicate', { added: result.added, duplicate: result.skipped_duplicate.length }));
      } else {
        toast.success(t('playlists.messages.addContentSuccess', { count: result.added }));
      }
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.addContentError')));
    },
  });
};

/**
 * Remove content from playlist
 */
export const useRemoveContentFromPlaylist = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ playlistId, itemId }: { playlistId: number; itemId: number }) =>
      playlistApi.removeContent(playlistId, itemId),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.playlistId) });
      queryClient.invalidateQueries({ queryKey: playlistKeys.detail(variables.playlistId) });
      // Also refresh playlist list to update content_count
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });
      toast.success(t('playlists.messages.removeContentSuccess'));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.removeContentError')));
    },
  });
};

/**
 * Reorder playlist content
 */
export const useReorderPlaylistContent = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ReorderContentRequest }) =>
      playlistApi.reorderContent(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.content(variables.id) });
      toast.success(t('playlists.messages.reorderSuccess'));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.reorderError')));
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
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignDevicesRequest }) =>
      playlistApi.assignDevices(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });

      // Also refresh playlist list to update device_count
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      // Invalidate device queries (assigned devices need to show new playlist)
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Invalidate device-side playlist queries (both patterns)
      queryClient.invalidateQueries({ queryKey: ['devices', 'playlists'] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'playlists'] });

      // Invalidate schedule queries (schedules reference playlists)
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] });

      // Invalidate dashboard queries (active playlists may change)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(t('playlists.messages.assignDevicesSuccess', { count: result.assigned }));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.assignDevicesError')));
    },
  });
};

/**
 * Unassign playlist from devices
 */
export const useUnassignPlaylistFromDevices = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AssignDevicesRequest }) =>
      playlistApi.unassignDevices(id, data),
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({ queryKey: playlistKeys.assignments(variables.id) });

      // Also refresh playlist list to update device_count
      queryClient.invalidateQueries({ queryKey: playlistKeys.lists(orgId) });

      // Invalidate device queries (devices no longer have this playlist)
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Invalidate device-side playlist queries (both patterns)
      queryClient.invalidateQueries({ queryKey: ['devices', 'playlists'] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'playlists'] });

      // Invalidate schedule queries (schedules reference playlists)
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['device-schedules'] });

      // Invalidate dashboard queries (active playlists may change)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(t('playlists.messages.unassignDevicesSuccess', { count: result.removed }));
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, t('playlists.messages.unassignDevicesError')));
    },
  });
};

