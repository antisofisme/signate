/**
 * Device Hooks
 * React Query hooks for device management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi } from '../services/deviceApi';
import type { ActivateDeviceRequest, UpdateDeviceRequest, DeviceFilters } from '../types/device';

// Query keys
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (orgId: number, filters?: DeviceFilters) => [...deviceKeys.lists(), orgId, filters] as const,
  details: () => [...deviceKeys.all, 'detail'] as const,
  detail: (id: number) => [...deviceKeys.details(), id] as const,
};

/**
 * List devices
 */
export function useDevices(organizationId: number, filters?: DeviceFilters) {
  return useQuery({
    queryKey: deviceKeys.list(organizationId, filters),
    queryFn: () => deviceApi.list(organizationId, filters),
    enabled: !!organizationId,
  });
}

/**
 * Get device by ID
 */
export function useDevice(deviceId: number) {
  return useQuery({
    queryKey: deviceKeys.detail(deviceId),
    queryFn: () => deviceApi.get(deviceId),
    enabled: !!deviceId,
  });
}

/**
 * Activate device mutation
 */
export function useActivateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ActivateDeviceRequest) => deviceApi.activate(request),
    onSuccess: () => {
      // Invalidate all device lists
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
    },
  });
}

/**
 * Update device mutation
 */
export function useUpdateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, request }: { deviceId: number; request: UpdateDeviceRequest }) =>
      deviceApi.update(deviceId, request),
    onSuccess: (data) => {
      // Invalidate lists and update detail cache
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      queryClient.setQueryData(deviceKeys.detail(data.id), data);
    },
  });
}

/**
 * Delete device mutation
 */
export function useDeleteDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (deviceId: number) => deviceApi.delete(deviceId),
    onSuccess: () => {
      // Invalidate all device queries
      queryClient.invalidateQueries({ queryKey: deviceKeys.all });
    },
  });
}
