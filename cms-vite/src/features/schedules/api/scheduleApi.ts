/**
 * Schedule API Client
 * API functions for schedule management
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  Schedule,
  ScheduleFilters,
  ScheduleListResponse,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ConflictCheckRequest,
  ConflictCheckResponse,
  GetOccurrencesRequest,
  GetOccurrencesResponse,
} from '../types/schedule.types'

/**
 * Get list of schedules with optional filters
 */
export const getSchedules = async (
  filters?: ScheduleFilters
): Promise<ScheduleListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SCHEDULES.LIST, {
    params: filters,
  })
  return response.data
}

/**
 * Get single schedule by ID
 */
export const getSchedule = async (id: number): Promise<Schedule> => {
  const response = await apiClient.get(API_ENDPOINTS.SCHEDULES.GET(id))
  return response.data
}

/**
 * Create new schedule
 */
export const createSchedule = async (
  data: CreateScheduleRequest
): Promise<Schedule> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.CREATE, data)
  return response.data
}

/**
 * Update existing schedule
 */
export const updateSchedule = async (
  id: number,
  data: UpdateScheduleRequest
): Promise<Schedule> => {
  const response = await apiClient.put(API_ENDPOINTS.SCHEDULES.UPDATE(id), data)
  return response.data
}

/**
 * Delete schedule
 */
export const deleteSchedule = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.SCHEDULES.DELETE(id))
}

/**
 * Activate schedule
 */
export const activateSchedule = async (id: number): Promise<Schedule> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.ACTIVATE(id))
  return response.data
}

/**
 * Deactivate schedule
 */
export const deactivateSchedule = async (id: number): Promise<Schedule> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.DEACTIVATE(id))
  return response.data
}

/**
 * Pause schedule
 */
export const pauseSchedule = async (id: number): Promise<Schedule> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.PAUSE(id))
  return response.data
}

/**
 * Check for schedule conflicts
 */
export const checkConflicts = async (
  data: ConflictCheckRequest
): Promise<ConflictCheckResponse> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.CHECK_CONFLICTS, data)
  return response.data
}

/**
 * Get schedule occurrences for calendar view
 */
export const getOccurrences = async (
  data: GetOccurrencesRequest
): Promise<GetOccurrencesResponse> => {
  const response = await apiClient.post(API_ENDPOINTS.SCHEDULES.GET_OCCURRENCES, data)
  return response.data
}

/**
 * Get schedules for specific device
 */
export const getDeviceSchedules = async (deviceId: number): Promise<ScheduleListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SCHEDULES.GET_BY_DEVICE(deviceId))
  return response.data
}

/**
 * Get schedules for specific playlist
 */
export const getPlaylistSchedules = async (playlistId: number): Promise<ScheduleListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SCHEDULES.GET_BY_PLAYLIST(playlistId))
  return response.data
}
