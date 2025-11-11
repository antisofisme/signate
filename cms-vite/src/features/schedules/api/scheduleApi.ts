/**
 * Schedule API Client
 * API functions for schedule management
 */

import axios from 'axios'
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

const API_BASE = '/api/v1'

/**
 * Get list of schedules with optional filters
 */
export const getSchedules = async (
  filters?: ScheduleFilters
): Promise<ScheduleListResponse> => {
  const response = await axios.get(`${API_BASE}/schedules`, {
    params: filters,
  })
  return response.data
}

/**
 * Get single schedule by ID
 */
export const getSchedule = async (id: number): Promise<Schedule> => {
  const response = await axios.get(`${API_BASE}/schedules/${id}`)
  return response.data
}

/**
 * Create new schedule
 */
export const createSchedule = async (
  data: CreateScheduleRequest
): Promise<Schedule> => {
  const response = await axios.post(`${API_BASE}/schedules`, data)
  return response.data
}

/**
 * Update existing schedule
 */
export const updateSchedule = async (
  id: number,
  data: UpdateScheduleRequest
): Promise<Schedule> => {
  const response = await axios.put(`${API_BASE}/schedules/${id}`, data)
  return response.data
}

/**
 * Delete schedule
 */
export const deleteSchedule = async (id: number): Promise<void> => {
  await axios.delete(`${API_BASE}/schedules/${id}`)
}

/**
 * Activate schedule
 */
export const activateSchedule = async (id: number): Promise<Schedule> => {
  const response = await axios.post(`${API_BASE}/schedules/${id}/activate`)
  return response.data
}

/**
 * Deactivate schedule
 */
export const deactivateSchedule = async (id: number): Promise<Schedule> => {
  const response = await axios.post(`${API_BASE}/schedules/${id}/deactivate`)
  return response.data
}

/**
 * Pause schedule
 */
export const pauseSchedule = async (id: number): Promise<Schedule> => {
  const response = await axios.post(`${API_BASE}/schedules/${id}/pause`)
  return response.data
}

/**
 * Check for schedule conflicts
 */
export const checkConflicts = async (
  data: ConflictCheckRequest
): Promise<ConflictCheckResponse> => {
  const response = await axios.post(`${API_BASE}/schedules/check-conflicts`, data)
  return response.data
}

/**
 * Get schedule occurrences for calendar view
 */
export const getOccurrences = async (
  data: GetOccurrencesRequest
): Promise<GetOccurrencesResponse> => {
  const response = await axios.post(`${API_BASE}/schedules/occurrences`, data)
  return response.data
}

/**
 * Get schedules for specific device
 */
export const getDeviceSchedules = async (deviceId: number): Promise<ScheduleListResponse> => {
  const response = await axios.get(`${API_BASE}/schedules/device/${deviceId}`)
  return response.data
}

/**
 * Get schedules for specific playlist
 */
export const getPlaylistSchedules = async (playlistId: number): Promise<ScheduleListResponse> => {
  const response = await axios.get(`${API_BASE}/schedules/playlist/${playlistId}`)
  return response.data
}
