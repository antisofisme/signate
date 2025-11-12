/**
 * useDeviceWebSocket Hook
 * Real-time device updates via WebSocket
 */

import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocketEvents } from '@/lib/websocket'
import { toast } from 'sonner'
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
      console.log('[WS] Device status:', data)

      // Invalidate device list query
      queryClient.invalidateQueries({ queryKey: ['devices'] })

      // Invalidate specific device query
      queryClient.invalidateQueries({
        queryKey: ['devices', data.device_id]
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
      console.log('[WS] Device connected:', data)
      queryClient.invalidateQueries({ queryKey: ['devices'] })
      toast.success(`Device #${data.device_id} connected`)
    },

    // Device disconnected
    'device:disconnected': (data: DeviceStatusData) => {
      console.log('[WS] Device disconnected:', data)
      queryClient.invalidateQueries({ queryKey: ['devices'] })
      toast.info(`Device #${data.device_id} disconnected`)
    },

    // Device heartbeat
    'device:heartbeat': (data: DeviceHeartbeatData) => {
      console.log('[WS] Device heartbeat:', data.device_id)

      // Update cache without full refetch (optimistic update)
      queryClient.setQueryData(['devices', data.device_id], (oldData: any) => {
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
      console.log('[WS] Command acknowledged:', data)
      toast.info(`Device #${data.device_id} received command`)
    },

    // Command completed
    'command:complete': (data: CommandCompleteData) => {
      console.log('[WS] Command completed:', data)
      queryClient.invalidateQueries({
        queryKey: ['devices', data.device_id, 'commands']
      })
      toast.success(`Command completed on device #${data.device_id}`)
    },

    // Command error
    'command:error': (data: CommandErrorData) => {
      console.log('[WS] Command error:', data)
      toast.error(`Command failed on device #${data.device_id}: ${data.error}`)
    },
  })
}

/**
 * Hook to listen for device events for a specific device
 */
export function useDeviceWebSocketById(deviceId: number | undefined) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!deviceId) return

    // This hook will automatically filter events for the specific device
    // The WebSocket client will send all device events, but we only
    // invalidate queries for the device we're interested in
  }, [deviceId, queryClient])

  useWebSocketEvents({
    'device:status': (data: DeviceStatusData) => {
      if (data.device_id === deviceId) {
        queryClient.invalidateQueries({
          queryKey: ['devices', deviceId]
        })
      }
    },

    'device:heartbeat': (data: DeviceHeartbeatData) => {
      if (data.device_id === deviceId) {
        queryClient.setQueryData(['devices', deviceId], (oldData: any) => {
          if (!oldData) return oldData
          return {
            ...oldData,
            last_seen: data.timestamp,
            status: 'online',
            system_info: data.system_info || oldData.system_info,
          }
        })
      }
    },
  })
}
