/**
 * Advanced Schedule API Client
 * API functions for advanced scheduling features
 */

import { apiClient } from '@/lib/api/client'
import type {
  CheckConflictRequest,
  CheckConflictResponse,
  ValidateScheduleRequest,
  ValidateScheduleResponse,
  CalculateNextOccurrenceRequest,
  CalculateNextOccurrenceResponse,
  ActiveScheduleRequest,
  ActiveScheduleResponse,
} from '../types/advanced'

/**
 * Check for schedule conflicts
 * POST /api/v1/schedules/check-conflict
 */
export const checkScheduleConflict = async (
  data: CheckConflictRequest
): Promise<CheckConflictResponse> => {
  const response = await apiClient.post('/api/v1/schedules/check-conflict', data)
  return response.data
}

/**
 * Validate schedule configuration
 * POST /api/v1/schedules/validate
 */
export const validateSchedule = async (
  data: ValidateScheduleRequest
): Promise<ValidateScheduleResponse> => {
  const response = await apiClient.post('/api/v1/schedules/validate', data)
  return response.data
}

/**
 * Calculate next occurrences of a schedule
 * POST /api/v1/schedules/{schedule_id}/next-occurrence
 */
export const calculateNextOccurrence = async (
  scheduleId: number,
  data?: CalculateNextOccurrenceRequest
): Promise<CalculateNextOccurrenceResponse> => {
  const response = await apiClient.post(
    `/api/v1/schedules/${scheduleId}/next-occurrence`,
    data || {}
  )
  return response.data
}

/**
 * Get active schedule at specific time
 * POST /api/v1/schedules/active
 */
export const getActiveSchedule = async (
  data?: ActiveScheduleRequest
): Promise<ActiveScheduleResponse> => {
  const response = await apiClient.post('/api/v1/schedules/active', data || {})
  return response.data
}
