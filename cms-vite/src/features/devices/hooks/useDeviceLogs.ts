/**
 * React Query Hooks for Device Logs Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/lib/notifications/toast';
import { handleAPIError } from '@/lib/errors/errorHandler';
import { logsApi } from '../api/logsApi';
import type { LogFilters } from '../types/logs';
import { deviceKeys } from './useDevices';

// Query keys
export const logKeys = {
  all: ['device-logs'] as const,
  lists: () => [...logKeys.all, 'list'] as const,
  list: (deviceId: number, filters?: LogFilters) =>
    [...logKeys.lists(), deviceId, filters] as const,
  latest: (deviceId: number, count?: number) =>
    [...logKeys.all, 'latest', deviceId, count] as const,
};

// ========================================
// Console Logs Hooks
// ========================================

/**
 * Get device console logs with pagination and filters
 * Supports auto-refresh every 30 seconds
 */
export const useDeviceLogs = (
  deviceId: number,
  filters?: LogFilters,
  options?: {
    enabled?: boolean;
    autoRefresh?: boolean;
  }
) => {
  const { enabled = true, autoRefresh = true } = options || {};

  return useQuery({
    queryKey: logKeys.list(deviceId, filters),
    queryFn: () => logsApi.getDeviceLogs(deviceId, filters),
    enabled: enabled && deviceId > 0,
    staleTime: 10000, // 10 seconds
    refetchInterval: autoRefresh ? 30000 : false, // Auto-refresh every 30s if enabled
    refetchIntervalInBackground: false, // Don't refetch when tab is inactive
  });
};

/**
 * Get latest N console logs
 * Convenience hook for real-time monitoring
 */
export const useLatestLogs = (
  deviceId: number,
  count: number = 20,
  options?: {
    enabled?: boolean;
    autoRefresh?: boolean;
  }
) => {
  const { enabled = true, autoRefresh = true } = options || {};

  return useQuery({
    queryKey: logKeys.latest(deviceId, count),
    queryFn: () => logsApi.getLatestLogs(deviceId, count),
    enabled: enabled && deviceId > 0,
    staleTime: 5000, // 5 seconds
    refetchInterval: autoRefresh ? 10000 : false, // Auto-refresh every 10s if enabled
    refetchIntervalInBackground: false,
  });
};

/**
 * Clear all device console logs
 * Invalidates cache after successful deletion
 */
export const useClearLogs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deviceId: number) => logsApi.clearDeviceLogs(deviceId),
    onSuccess: (_, deviceId) => {
      // Invalidate all log queries for this device
      queryClient.invalidateQueries({ queryKey: logKeys.lists() });
      queryClient.invalidateQueries({ queryKey: logKeys.all });

      // Also invalidate device queries (last_seen_at might change)
      queryClient.invalidateQueries({ queryKey: deviceKeys.detail(deviceId) });

      toast.success('Console logs cleared successfully');
    },
    onError: (error: unknown) => {
      toast.error(handleAPIError(error).message);
    },
  });
};

// ========================================
// Connection Logs Hooks (Future)
// ========================================

/**
 * Get device connection logs (placeholder for future implementation)
 */
export const useConnectionLogs = (
  deviceId: number,
  filters?: {
    event_type?: string;
    limit?: number;
    skip?: number;
  },
  options?: {
    enabled?: boolean;
  }
) => {
  const { enabled = true } = options || {};

  return useQuery({
    queryKey: [...logKeys.all, 'connection', deviceId, filters],
    queryFn: () => logsApi.getConnectionLogs(deviceId, filters),
    enabled: enabled && deviceId > 0,
    staleTime: 30000,
  });
};
