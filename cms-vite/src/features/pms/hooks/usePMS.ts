/**
 * PMS React Hooks
 *
 * Custom hooks for PMS integration using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import * as pmsApi from '../api/pmsApi'
import type {
  PMSConfig,
  PMSGuest,
  PMSRoom,
  PMSSyncStatus,
  PMSStats,
  CreatePMSConfigRequest,
  UpdatePMSConfigRequest,
  TestConnectionRequest,
  TriggerSyncRequest,
  MapRoomToDeviceRequest,
  PMSGuestFilters,
  PMSRoomFilters,
} from '../types/pms.types'

// ===================================
// Query Keys
// ===================================

export const PMS_KEYS = {
  all: ['pms'] as const,
  config: () => [...PMS_KEYS.all, 'config'] as const,
  syncStatus: () => [...PMS_KEYS.all, 'sync-status'] as const,
  stats: () => [...PMS_KEYS.all, 'stats'] as const,
  guests: (filters?: PMSGuestFilters) => [...PMS_KEYS.all, 'guests', filters] as const,
  guest: (id: number) => [...PMS_KEYS.all, 'guest', id] as const,
  currentGuests: () => [...PMS_KEYS.all, 'guests', 'current'] as const,
  rooms: (filters?: PMSRoomFilters) => [...PMS_KEYS.all, 'rooms', filters] as const,
  room: (id: number) => [...PMS_KEYS.all, 'room', id] as const,
}

// ===================================
// Configuration Hooks
// ===================================

/**
 * Get PMS configuration
 */
export function usePMSConfig() {
  return useQuery({
    queryKey: PMS_KEYS.config(),
    queryFn: pmsApi.getPMSConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Create PMS configuration
 */
export function useCreatePMSConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePMSConfigRequest) => pmsApi.createPMSConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.config() })
      toast.success('PMS configuration created successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create PMS configuration')
    },
  })
}

/**
 * Update PMS configuration
 */
export function useUpdatePMSConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdatePMSConfigRequest) => pmsApi.updatePMSConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.config() })
      toast.success('PMS configuration updated successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update PMS configuration')
    },
  })
}

/**
 * Delete PMS configuration
 */
export function useDeletePMSConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: pmsApi.deletePMSConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.config() })
      toast.success('PMS configuration deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete PMS configuration')
    },
  })
}

/**
 * Test PMS connection
 */
export function useTestPMSConnection() {
  return useMutation({
    mutationFn: (data: TestConnectionRequest) => pmsApi.testPMSConnection(data),
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Connection successful! Response time: ${data.response_time_ms}ms`)
      } else {
        toast.error(`Connection failed: ${data.message}`)
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Connection test failed')
    },
  })
}

// ===================================
// Sync Hooks
// ===================================

/**
 * Get PMS sync status
 */
export function usePMSSyncStatus() {
  return useQuery({
    queryKey: PMS_KEYS.syncStatus(),
    queryFn: pmsApi.getPMSSyncStatus,
    refetchInterval: (query) => {
      // Auto-refresh every 5 seconds if syncing
      return query.state.data?.is_syncing ? 5000 : false
    },
  })
}

/**
 * Trigger PMS sync
 */
export function useTriggerPMSSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data?: TriggerSyncRequest) => pmsApi.triggerPMSSync(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.syncStatus() })
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.stats() })
      toast.success('PMS sync triggered successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to trigger PMS sync')
    },
  })
}

/**
 * Get PMS statistics
 */
export function usePMSStats() {
  return useQuery({
    queryKey: PMS_KEYS.stats(),
    queryFn: pmsApi.getPMSStats,
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

// ===================================
// Guest Hooks
// ===================================

/**
 * Get PMS guests list
 */
export function usePMSGuests(filters?: PMSGuestFilters) {
  return useQuery({
    queryKey: PMS_KEYS.guests(filters),
    queryFn: () => pmsApi.getPMSGuests(filters),
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Get current guests (checked-in)
 */
export function useCurrentGuests() {
  return useQuery({
    queryKey: PMS_KEYS.currentGuests(),
    queryFn: pmsApi.getCurrentGuests,
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Get single guest
 */
export function usePMSGuest(guestId: number) {
  return useQuery({
    queryKey: PMS_KEYS.guest(guestId),
    queryFn: () => pmsApi.getPMSGuest(guestId),
    enabled: !!guestId,
  })
}

/**
 * Sync guests from PMS
 */
export function useSyncPMSGuests() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: pmsApi.syncPMSGuests,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.guests() })
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.stats() })
      toast.success(`Synced ${data.synced} guests successfully`)

      if (data.errors.length > 0) {
        toast.warning(`${data.errors.length} errors occurred during sync`)
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to sync guests')
    },
  })
}

// ===================================
// Room Hooks
// ===================================

/**
 * Get PMS rooms list
 */
export function usePMSRooms(filters?: PMSRoomFilters) {
  return useQuery({
    queryKey: PMS_KEYS.rooms(filters),
    queryFn: () => pmsApi.getPMSRooms(filters),
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Get single room
 */
export function usePMSRoom(roomId: number) {
  return useQuery({
    queryKey: PMS_KEYS.room(roomId),
    queryFn: () => pmsApi.getPMSRoom(roomId),
    enabled: !!roomId,
  })
}

/**
 * Sync rooms from PMS
 */
export function useSyncPMSRooms() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: pmsApi.syncPMSRooms,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.rooms() })
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.stats() })
      toast.success(`Synced ${data.synced} rooms successfully`)

      if (data.errors.length > 0) {
        toast.warning(`${data.errors.length} errors occurred during sync`)
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to sync rooms')
    },
  })
}

/**
 * Map room to device
 */
export function useMapRoomToDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MapRoomToDeviceRequest) => pmsApi.mapRoomToDevice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.rooms() })
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.stats() })

      // Invalidate device queries (device now mapped to room)
      queryClient.invalidateQueries({ queryKey: ['devices'] })

      toast.success('Room mapped to device successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to map room to device')
    },
  })
}

/**
 * Unmap room from device
 */
export function useUnmapRoomFromDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (roomId: number) => pmsApi.unmapRoomFromDevice(roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.rooms() })
      queryClient.invalidateQueries({ queryKey: PMS_KEYS.stats() })

      // Invalidate device queries (device no longer mapped to room)
      queryClient.invalidateQueries({ queryKey: ['devices'] })

      toast.success('Room unmapped from device successfully')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to unmap room from device')
    },
  })
}

// ===================================
// Helper Hooks
// ===================================

/**
 * Check if PMS is configured
 */
export function useHasPMSConfig() {
  const { data: config, isLoading } = usePMSConfig()
  return {
    hasConfig: !!config,
    isActive: config?.is_active || false,
    isLoading,
  }
}

/**
 * Check if PMS is syncing
 */
export function useIsPMSSyncing() {
  const { data: syncStatus } = usePMSSyncStatus()
  return syncStatus?.is_syncing || false
}

/**
 * Get unmapped rooms count
 */
export function useUnmappedRoomsCount() {
  const { data: stats } = usePMSStats()
  return stats?.unmapped_devices || 0
}
