/**
 * React Query Hooks for Device Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { useSelectedOrgId, deviceKeys as sharedDeviceKeys } from '@/shared/hooks';
import { deviceApi } from '../api/deviceApi';
import type {
  Device,
  MonitorRegisterRequest,
  TVRegisterRequest,
  ActivateDeviceRequest,
} from '../types/device';

// Re-export shared device keys for backward compatibility
export const deviceKeys = sharedDeviceKeys;

/**
 * Get list of devices with filters
 *
 * NOTE: Auto-polling removed for performance optimization.
 * Use refetch() from the returned query for manual refresh.
 * Data is considered fresh for 30 seconds (staleTime).
 *
 * Query key includes orgId for proper cache isolation between organizations.
 */
export const useDeviceList = (filters?: {
  status?: string;
  device_type?: string;
  skip?: number;
  limit?: number;
}) => {
  const orgId = useSelectedOrgId();

  return useQuery({
    queryKey: deviceKeys.list(orgId, filters),
    queryFn: () => deviceApi.list(filters),
    staleTime: 30000, // 30 seconds - data is fresh for this duration
    // Note: Backend handles org filtering via JWT (regular users) or X-Organization-Id header (super admin)
  });
};

/**
 * Get single device by ID
 */
export const useDevice = (id: number, enabled = true) => {
  return useQuery({
    queryKey: deviceKeys.detail(id),
    queryFn: () => deviceApi.get(id),
    enabled: enabled && id > 0,
  });
};

/**
 * Update device settings
 */
export const useUpdateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Device> }) =>
      deviceApi.update(id, data),
    onSuccess: (response, variables) => {
      // Invalidate specific device and list
      queryClient.invalidateQueries({ queryKey: deviceKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });

      // Invalidate dashboard queries (device status/health may change)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Device updated successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Delete device
 */
export const useDeleteDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deviceApi.delete(id),
    onMutate: async (deletedId) => {
      // Cancel outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: deviceKeys.lists() });

      // Snapshot previous values for rollback
      const previousData = queryClient.getQueriesData({ queryKey: deviceKeys.lists() });

      // Optimistically update all device list queries by removing the deleted device
      queryClient.setQueriesData(
        { queryKey: deviceKeys.lists() },
        (old: any) => {
          if (!old?.items) return old;
          return {
            ...old,
            items: old.items.filter((device: Device) => device.id !== deletedId),
            total: old.total - 1,
          };
        }
      );

      // Return context with previous data for potential rollback
      return { previousData };
    },
    onSuccess: async () => {
      // Invalidate to ensure server state is correct
      await queryClient.invalidateQueries({ queryKey: deviceKeys.all });
      toast.success('Device deleted successfully');
    },
    onError: (error: unknown, deletedId, context) => {
      // Rollback optimistic update on error
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
      toast.error(handleAPIError(error).message);
    },
    onSettled: () => {
      // Always refetch after error or success to sync with server
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
    },
  });
};

// ========================================
// Device Registration & Activation
// ========================================

/**
 * Register a TV device (WebOS/native)
 */
export const useTVRegister = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TVRegisterRequest) => deviceApi.tvRegister(data),
    onSuccess: (device) => {
      // Invalidate device list to refetch
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });

      // Invalidate dashboard queries (new device affects device count)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(`TV registered successfully. Activation code: ${device.unique_code}`);
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Register a monitor device (browser-based)
 */
export const useMonitorRegister = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MonitorRegisterRequest) => deviceApi.monitorRegister(data),
    onSuccess: () => {
      // Invalidate device list to refetch
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });

      // Invalidate dashboard queries (new device affects device count)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Monitor registered successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Activate device with code
 */
export const useActivateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ActivateDeviceRequest) => deviceApi.activate(data),
    onSuccess: (device) => {
      // Invalidate device list and specific device
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: deviceKeys.detail(device.id) });

      // Invalidate dashboard queries (device status changed)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success(`Device "${device.device_name}" activated successfully`);
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Check activation code validity
 */
export const useCheckActivation = (code: string, enabled = true) => {
  return useQuery({
    queryKey: [...deviceKeys.all, 'check-activation', code],
    queryFn: () => deviceApi.checkActivation(code),
    enabled: enabled && code.length === 6,
    staleTime: 0, // Always refetch
  });
};

// ========================================
// Device Monitoring
// ========================================

/**
 * Send heartbeat to update device status
 */
export const useHeartbeat = () => {
  return useMutation({
    mutationFn: (deviceId: number) => deviceApi.heartbeat(deviceId),
    onError: (error: unknown) => {
      console.error('Heartbeat failed:', error);
      // Don't show toast for heartbeat errors (silent background operation)
    },
  });
};

/**
 * Get device logs
 */
export const useDeviceLogs = (
  id: number,
  filters?: {
    event_type?: string;
    skip?: number;
    limit?: number;
  },
  enabled = true
) => {
  return useQuery({
    queryKey: [...deviceKeys.logs(id), filters],
    queryFn: () => deviceApi.getLogs(id, filters),
    enabled: enabled && id > 0,
    staleTime: 10000, // 10 seconds
  });
};

// ========================================
// Remote Commands
// ========================================

/**
 * Get device commands
 */
export const useDeviceCommands = (
  id: number,
  filters?: {
    status?: string;
    skip?: number;
    limit?: number;
  },
  enabled = true
) => {
  return useQuery({
    queryKey: [...deviceKeys.commands(id), filters],
    queryFn: () => deviceApi.getCommands(id, filters),
    enabled: enabled && id > 0,
    staleTime: 5000, // 5 seconds
  });
};

/**
 * Send command to device
 */
export const useSendCommand = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      commandData,
    }: {
      id: number;
      commandData: {
        command_type: 'reboot' | 'screenshot' | 'volume' | 'brightness' | 'refresh';
        parameters?: Record<string, any>;
      };
    }) => deviceApi.sendCommand(id, commandData),
    onSuccess: (command, variables) => {
      // Invalidate commands list for this device
      queryClient.invalidateQueries({ queryKey: deviceKeys.commands(variables.id) });
      toast.success(`Command "${command.command_type}" sent successfully`);
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

// ========================================
// Device Assignments
// ========================================

/**
 * Get tags assigned to device
 */
export const useDeviceTags = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: [...deviceKeys.all, 'tags', deviceId],
    queryFn: () => deviceApi.getTags(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000,
  });
};

/**
 * Assign tag to device
 */
export const useAssignTag = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, tagId }: { deviceId: number; tagId: number }) =>
      deviceApi.assignTag(deviceId, tagId),
    onSuccess: (_, variables) => {
      // Invalidate device tags (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'tags', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'tags', variables.deviceId] });

      // Invalidate tag queries (usage count changes)
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId] });

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
      deviceApi.unassignTag(deviceId, tagId),
    onSuccess: (_, variables) => {
      // Invalidate device tags (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'tags', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'tags', variables.deviceId] });

      // Invalidate tag queries (usage count changes)
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      queryClient.invalidateQueries({ queryKey: ['tags', variables.tagId] });

      toast.success('Tag removed successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Get content assigned to device
 */
export const useDeviceContents = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: [...deviceKeys.all, 'contents', deviceId],
    queryFn: () => deviceApi.getContents(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000,
  });
};

/**
 * Assign content to device
 */
export const useAssignContent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      deviceId,
      contentId,
      priority,
    }: {
      deviceId: number;
      contentId: number;
      priority?: number;
    }) => deviceApi.assignContent(deviceId, contentId, priority),
    onSuccess: (_, variables) => {
      // Invalidate device contents (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'contents', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'contents', variables.deviceId] });

      // Invalidate content queries (assignment count may change)
      queryClient.invalidateQueries({ queryKey: ['content', variables.contentId] });

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
      deviceApi.unassignContent(deviceId, contentId),
    onSuccess: (_, variables) => {
      // Invalidate device contents (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'contents', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'contents', variables.deviceId] });

      // Invalidate content queries (assignment count may change)
      queryClient.invalidateQueries({ queryKey: ['content', variables.contentId] });

      // Invalidate dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Content removed successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

/**
 * Get playlists assigned to device
 */
export const useDevicePlaylists = (deviceId: number, enabled = true) => {
  return useQuery({
    queryKey: [...deviceKeys.all, 'playlists', deviceId],
    queryFn: () => deviceApi.getPlaylists(deviceId),
    enabled: enabled && deviceId > 0,
    staleTime: 30000,
  });
};

/**
 * Assign playlist to device
 */
export const useAssignPlaylist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, playlistId }: { deviceId: number; playlistId: number }) =>
      deviceApi.assignPlaylist(deviceId, playlistId),
    onSuccess: (_, variables) => {
      // Invalidate device playlists (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'playlists', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'playlists', variables.deviceId] });

      // Invalidate playlist queries (assignment count changes)
      queryClient.invalidateQueries({ queryKey: ['playlists'] });
      queryClient.invalidateQueries({ queryKey: ['playlist', variables.playlistId] });

      // Invalidate dashboard queries (active playlists may change)
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
      deviceApi.unassignPlaylist(deviceId, playlistId),
    onSuccess: (_, variables) => {
      // Invalidate device playlists (both patterns for consistency)
      queryClient.invalidateQueries({ queryKey: [...deviceKeys.all, 'playlists', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['device-assignments', 'playlists', variables.deviceId] });

      // Invalidate playlist queries (assignment count changes)
      queryClient.invalidateQueries({ queryKey: ['playlists'] });
      queryClient.invalidateQueries({ queryKey: ['playlist', variables.playlistId] });

      // Invalidate dashboard queries (active playlists may change)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      toast.success('Playlist removed successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};
