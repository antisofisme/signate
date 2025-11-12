/**
 * PMS API Client
 *
 * API functions for PMS integration
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  PMSConfig,
  PMSGuest,
  PMSRoom,
  PMSSyncStatus,
  PMSStats,
  CreatePMSConfigRequest,
  UpdatePMSConfigRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  TriggerSyncRequest,
  PMSGuestListResponse,
  PMSRoomListResponse,
  MapRoomToDeviceRequest,
  PMSGuestFilters,
  PMSRoomFilters,
} from '../types/pms.types'

/**
 * Get PMS configuration for current organization
 */
export const getPMSConfig = async (): Promise<PMSConfig | null> => {
  const response = await apiClient.get<PMSConfig>(API_ENDPOINTS.PMS.CONFIG)
  return response.data
}

/**
 * Create PMS configuration
 */
export const createPMSConfig = async (data: CreatePMSConfigRequest): Promise<PMSConfig> => {
  const response = await apiClient.post<PMSConfig>(API_ENDPOINTS.PMS.CONFIG, data)
  return response.data
}

/**
 * Update PMS configuration
 */
export const updatePMSConfig = async (data: UpdatePMSConfigRequest): Promise<PMSConfig> => {
  const response = await apiClient.put<PMSConfig>(API_ENDPOINTS.PMS.CONFIG, data)
  return response.data
}

/**
 * Delete PMS configuration
 */
export const deletePMSConfig = async (): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.PMS.CONFIG)
}

/**
 * Test PMS connection
 */
export const testPMSConnection = async (
  data: TestConnectionRequest
): Promise<TestConnectionResponse> => {
  const response = await apiClient.post<TestConnectionResponse>(
    API_ENDPOINTS.PMS.TEST_CONNECTION,
    data
  )
  return response.data
}

/**
 * Get PMS sync status
 */
export const getPMSSyncStatus = async (): Promise<PMSSyncStatus> => {
  const response = await apiClient.get<PMSSyncStatus>(API_ENDPOINTS.PMS.SYNC_STATUS)
  return response.data
}

/**
 * Trigger PMS sync
 */
export const triggerPMSSync = async (data?: TriggerSyncRequest): Promise<PMSSyncStatus> => {
  const response = await apiClient.post<PMSSyncStatus>(API_ENDPOINTS.PMS.TRIGGER_SYNC, data || {})
  return response.data
}

/**
 * Get PMS statistics
 */
export const getPMSStats = async (): Promise<PMSStats> => {
  const response = await apiClient.get<PMSStats>(API_ENDPOINTS.PMS.STATS)
  return response.data
}

/**
 * Get PMS guests list
 */
export const getPMSGuests = async (filters?: PMSGuestFilters): Promise<PMSGuestListResponse> => {
  const response = await apiClient.get<PMSGuestListResponse>(API_ENDPOINTS.PMS.GUESTS, {
    params: filters,
  })
  return response.data
}

/**
 * Get current guests (checked-in)
 */
export const getCurrentGuests = async (): Promise<PMSGuest[]> => {
  const response = await apiClient.get<PMSGuest[]>(API_ENDPOINTS.PMS.CURRENT_GUESTS)
  return response.data
}

/**
 * Get single guest by ID
 */
export const getPMSGuest = async (guestId: number): Promise<PMSGuest> => {
  const response = await apiClient.get<PMSGuest>(API_ENDPOINTS.PMS.GUEST(guestId))
  return response.data
}

/**
 * Sync guests from PMS
 */
export const syncPMSGuests = async (): Promise<{ synced: number; errors: string[] }> => {
  const response = await apiClient.post<{ synced: number; errors: string[] }>(
    API_ENDPOINTS.PMS.SYNC_GUESTS
  )
  return response.data
}

/**
 * Get PMS rooms list
 */
export const getPMSRooms = async (filters?: PMSRoomFilters): Promise<PMSRoomListResponse> => {
  const response = await apiClient.get<PMSRoomListResponse>(API_ENDPOINTS.PMS.ROOMS, {
    params: filters,
  })
  return response.data
}

/**
 * Get single room by ID
 */
export const getPMSRoom = async (roomId: number): Promise<PMSRoom> => {
  const response = await apiClient.get<PMSRoom>(API_ENDPOINTS.PMS.ROOM(roomId))
  return response.data
}

/**
 * Sync rooms from PMS
 */
export const syncPMSRooms = async (): Promise<{ synced: number; errors: string[] }> => {
  const response = await apiClient.post<{ synced: number; errors: string[] }>(
    API_ENDPOINTS.PMS.SYNC_ROOMS
  )
  return response.data
}

/**
 * Map room to device
 */
export const mapRoomToDevice = async (data: MapRoomToDeviceRequest): Promise<PMSRoom> => {
  const response = await apiClient.post<PMSRoom>(API_ENDPOINTS.PMS.MAP_ROOM_DEVICE, data)
  return response.data
}

/**
 * Unmap room from device
 */
export const unmapRoomFromDevice = async (roomId: number): Promise<PMSRoom> => {
  const response = await apiClient.delete<PMSRoom>(API_ENDPOINTS.PMS.UNMAP_ROOM_DEVICE(roomId))
  return response.data
}
