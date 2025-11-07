/**
 * React Query Hooks for Device Management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { deviceApi } from '../services/deviceApi';
import type {
  Device,
  MonitorRegisterRequest,
  TVRegisterRequest,
  ActivateDeviceRequest,
} from '../types/device';

// Query keys
export const deviceKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceKeys.all, 'list'] as const,
  list: (filters?: {
    status?: string;
    device_type?: string;
    skip?: number;
    limit?: number;
  }) => [...deviceKeys.lists(), filters] as const,
  details: () => [...deviceKeys.all, 'detail'] as const,
  detail: (id: number) => [...deviceKeys.details(), id] as const,
  logs: (id: number) => [...deviceKeys.all, 'logs', id] as const,
  commands: (id: number) => [...deviceKeys.all, 'commands', id] as const,
};

/**
 * Get list of devices with filters
 */
export const useDeviceList = (filters?: {
  status?: string;
  device_type?: string;
  skip?: number;
  limit?: number;
}) => {
  return useQuery({
    queryKey: deviceKeys.list(filters),
    queryFn: () => deviceApi.list(filters),
    staleTime: 30000, // 30 seconds
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
      toast.success('Device updated successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to update device';
      toast.error(message);
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
    onSuccess: () => {
      // Invalidate device list to refetch
      queryClient.invalidateQueries({ queryKey: deviceKeys.lists() });
      toast.success('Device deleted successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to delete device';
      toast.error(message);
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
      toast.success(`TV registered successfully. Activation code: ${device.unique_code}`);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to register TV';
      toast.error(message);
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
      toast.success('Monitor registered successfully');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to register monitor';
      toast.error(message);
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
      toast.success(`Device "${device.device_name}" activated successfully`);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to activate device';
      toast.error(message);
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
    onError: (error: any) => {
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
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to send command';
      toast.error(message);
    },
  });
};
