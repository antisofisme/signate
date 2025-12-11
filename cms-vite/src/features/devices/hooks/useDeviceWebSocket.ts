/**
 * useDeviceWebSocket Hook
 * Real-time device updates via WebSocket
 */

import { useQueryClient } from '@tanstack/react-query'
import { useWebSocketEvents } from '@/lib/websocket'
import { toast } from '@/shared/utils/toast'
import { logger } from '@/shared/utils/logger'
import { deviceKeys } from './useDevices'
import type {
  DeviceStatusData,
  DeviceHeartbeatData,
  CommandAckData,
  CommandCompleteData,
  CommandErrorData,
} from '@/lib/websocket/types'

/**
 * Hook to listen for device WebSocket events
 * Automatically invalidates device queries when updates are received
 */
export function useDeviceWebSocket() {
  const queryClient = useQueryClient()

  useWebSocketEvents({
    // Device status changed (online/offline)
    'device:status': (data: DeviceStatusData) => {
      logger.debug('[WS] Device status:', data)

      // Invalidate ALL device queries (using deviceKeys.all for proper matching)
      void queryClient.invalidateQueries({
        queryKey: deviceKeys.all,
        refetchType: 'all',
      })

      // Show toast notification
      if (data.status === 'online') {
        toast.success(`Device #${data.device_id} is now online`)
      } else if (data.status === 'offline') {
        toast.warning(`Device #${data.device_id} went offline`)
      } else if (data.status === 'error') {
        toast.error(`Device #${data.device_id} reported an error`)
      }
    },

    // Device connected
    'device:connected': (data: DeviceStatusData) => {
      logger.debug('[WS] Device connected:', data)
      void queryClient.invalidateQueries({
        queryKey: deviceKeys.all,
        refetchType: 'all',
      })
      toast.success(`Device #${data.device_id} connected`)
    },

    // Device disconnected
    'device:disconnected': (data: DeviceStatusData) => {
      logger.debug('[WS] Device disconnected:', data)
      void queryClient.invalidateQueries({
        queryKey: deviceKeys.all,
        refetchType: 'all',
      })
      toast.info(`Device #${data.device_id} disconnected`)
    },

    // Device heartbeat
    'device:heartbeat': (data: DeviceHeartbeatData) => {
      logger.debug('[WS] Device heartbeat:', data.device_id)

      // Update cache without full refetch (optimistic update)
      queryClient.setQueryData(deviceKeys.detail(data.device_id), (oldData: any) => {
        if (!oldData) return oldData
        return {
          ...oldData,
          last_seen: data.timestamp,
          status: 'online',
          system_info: data.system_info || oldData.system_info,
        }
      })
    },

    // Command acknowledged
    'command:ack': (data: CommandAckData) => {
      logger.debug('[WS] Command acknowledged:', data)
      toast.info(`Device #${data.device_id} received command`)
    },

    // Command completed
    'command:complete': (data: CommandCompleteData) => {
      logger.debug('[WS] Command completed:', data)
      void queryClient.invalidateQueries({
        queryKey: deviceKeys.commands(data.device_id),
      })
      toast.success(`Command completed on device #${data.device_id}`)
    },

    // Command error
    'command:error': (data: CommandErrorData) => {
      logger.debug('[WS] Command error:', data)
      toast.error(`Command failed on device #${data.device_id}: ${data.error}`)
    },
  })
}

/**
 * Hook to listen for device events for a specific device
 * Automatically invalidates device and health queries on updates
 */
export function useDeviceWebSocketById(deviceId: number | undefined) {
  const queryClient = useQueryClient()

  useWebSocketEvents({
    'device:status': (data: DeviceStatusData) => {
      if (data.device_id === deviceId) {
        void queryClient.invalidateQueries({
          queryKey: deviceKeys.detail(deviceId),
        })
        // Also invalidate health when status changes
        void queryClient.invalidateQueries({
          queryKey: [...deviceKeys.all, 'health', deviceId],
        })
      }
    },

    'device:heartbeat': (data: DeviceHeartbeatData) => {
      if (data.device_id === deviceId) {
        // Update device data optimistically
        queryClient.setQueryData(deviceKeys.detail(deviceId), (oldData: any) => {
          if (!oldData) return oldData
          return {
            ...oldData,
            last_seen: data.timestamp,
            status: 'online',
            system_info: data.system_info || oldData.system_info,
          }
        })
        // Invalidate health query for fresh metrics
        void queryClient.invalidateQueries({
          queryKey: [...deviceKeys.all, 'health', deviceId],
        })
      }
    },
  })
}
