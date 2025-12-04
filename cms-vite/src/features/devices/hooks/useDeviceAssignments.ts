/**
 * React Query Hooks for Device Assignments
 *
 * Comprehensive hooks for managing device assignments:
 * - Playlist assignments
 * - Content assignments (with expiry support)
 * - Tag assignments
 * - Bulk operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { deviceAssignmentsApi } from '../api/deviceAssignmentsApi';
import type {
  PlaylistAssignment,
  ContentAssignment,
  TagAssignment,
  AssignContentRequest,
  AssignPlaylistRequest,
  AssignTagRequest,
  BulkAssignPlaylistRequest,
} from '../types/assignment';

// Query keys for assignment-related queries
export const assignmentKeys = {
  all: ['device-assignments'] as const,
  playlists: (deviceId: number) => [...assignmentKeys.all, 'playlists', deviceId] as const,
  contents: (deviceId: number) => [...assignmentKeys.all, 'contents', deviceId] as const,
  tags: (deviceId: number) => [...assignmentKeys.all, 'tags', deviceId] as const,
};

// ========================================
// Playlist Assignment Hooks
// ========================================

/**
 * Get playlists assigned to device
 */
export const useDevicePlaylists = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: assignmentKeys.playlists(deviceId),
    queryFn: () => deviceAssignmentsApi.getDevicePlaylists(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Assign playlist to device
 */
export const useAssignPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: number; data: AssignPlaylistRequest }) =>
      deviceAssignmentsApi.assignPlaylistToDevice(deviceId, data),
    onSuccess: (_, variables) => {
      // Invalidate device playlists (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.playlists(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'playlists', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate playlist queries
      queryClient.invalidateQueries({ queryKey: ['playlists'] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Playlist assigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Unassign playlist from device
 */
export const useUnassignPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, playlistId }: { deviceId: number; playlistId: number }) =>
      deviceAssignmentsApi.unassignPlaylistFromDevice(deviceId, playlistId),
    onSuccess: (_, variables) => {
      // Invalidate device playlists (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.playlists(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'playlists', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate playlist queries
      queryClient.invalidateQueries({ queryKey: ['playlists'] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Playlist unassigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Bulk assign playlist to multiple devices
 */
export const useBulkAssignPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ playlistId, data }: { playlistId: number; data: BulkAssignPlaylistRequest }) =>
      deviceAssignmentsApi.bulkAssignPlaylistToDevices(playlistId, data),
    onSuccess: (result, variables) => {
      // Invalidate all device playlists (we don't know which devices were affected)
      queryClient.invalidateQueries({ queryKey: [...assignmentKeys.all, 'playlists'] });

      // Invalidate all devices
      queryClient.invalidateQueries({ queryKey: ['devices'] });

      // Invalidate playlist queries
      queryClient.invalidateQueries({ queryKey: ['playlists', 'detail', variables.playlistId] });
      queryClient.invalidateQueries({ queryKey: ['playlists', 'list'] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      if (result.failed > 0) {
        toast.warning(
          `Assigned to ${result.assigned} devices, ${result.failed} failed`
        );
      } else {
        toast.success(`Playlist assigned to ${result.assigned} devices`);
      }
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

// ========================================
// Content Assignment Hooks
// ========================================

/**
 * Get content assigned to device
 */
export const useDeviceContents = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: assignmentKeys.contents(deviceId),
    queryFn: () => deviceAssignmentsApi.getDeviceContents(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Assign content to device (with optional expiry)
 */
export const useAssignContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: number; data: AssignContentRequest }) =>
      deviceAssignmentsApi.assignContentToDevice(deviceId, data),
    onSuccess: (_, variables) => {
      // Invalidate device contents (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.contents(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'contents', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate content queries
      queryClient.invalidateQueries({ queryKey: ['content'] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Content assigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Unassign content from device
 */
export const useUnassignContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, contentId }: { deviceId: number; contentId: number }) =>
      deviceAssignmentsApi.unassignContentFromDevice(deviceId, contentId),
    onSuccess: (_, variables) => {
      // Invalidate device contents (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.contents(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'contents', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate content queries
      queryClient.invalidateQueries({ queryKey: ['content'] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Content unassigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

// ========================================
// Tag Assignment Hooks
// ========================================

/**
 * Get tags assigned to device
 */
export const useDeviceTags = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: assignmentKeys.tags(deviceId),
    queryFn: () => deviceAssignmentsApi.getDeviceTags(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Assign tag to device
 */
export const useAssignTag = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: number; data: AssignTagRequest }) =>
      deviceAssignmentsApi.assignTagToDevice(deviceId, data),
    onSuccess: (_, variables) => {
      // Invalidate device tags (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.tags(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'tags', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });

      toast.success('Tag assigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Unassign tag from device
 */
export const useUnassignTag = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, tagId }: { deviceId: number; tagId: number }) =>
      deviceAssignmentsApi.unassignTagFromDevice(deviceId, tagId),
    onSuccess: (_, variables) => {
      // Invalidate device tags (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: assignmentKeys.tags(variables.deviceId) });
      queryClient.invalidateQueries({ queryKey: ['devices', 'tags', variables.deviceId] });

      // Invalidate device queries
      queryClient.invalidateQueries({ queryKey: ['devices', 'detail', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });

      // Invalidate tag queries
      queryClient.invalidateQueries({ queryKey: ['tags'] });

      toast.success('Tag unassigned successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};
