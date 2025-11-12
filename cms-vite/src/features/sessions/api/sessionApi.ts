/**
 * Session API Client
 * API functions for session management
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  Session,
  SessionListResponse,
  SessionStatsResponse,
  SessionFilters,
  RevokeSessionRequest,
  RevokeAllSessionsRequest,
} from '../types/session.types'

// ============================================================================
// Session Queries
// ============================================================================

/**
 * Get current user's sessions
 */
export const getSessions = async (filters?: SessionFilters): Promise<SessionListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.LIST, {
    params: filters,
  })
  return response.data
}

/**
 * Get single session by ID
 */
export const getSession = async (id: string): Promise<Session> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.GET(id))
  return response.data
}

/**
 * Get session statistics
 */
export const getSessionStats = async (): Promise<SessionStatsResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.STATS)
  return response.data
}

/**
 * Get active sessions only
 */
export const getActiveSessions = async (): Promise<SessionListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.ACTIVE)
  return response.data
}

/**
 * Get sessions for specific user (admin only)
 */
export const getUserSessions = async (userId: number): Promise<SessionListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.USER_SESSIONS(userId))
  return response.data
}

/**
 * Get sessions by IP address (admin only)
 */
export const getSessionsByIP = async (ip: string): Promise<SessionListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.SESSIONS.IP_SESSIONS(ip))
  return response.data
}

// ============================================================================
// Session Actions
// ============================================================================

/**
 * Revoke specific session (logout from device)
 */
export const revokeSession = async (data: RevokeSessionRequest): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.SESSIONS.DELETE(data.session_id), {
    data: { reason: data.reason },
  })
}

/**
 * Revoke all sessions except current (logout from all devices)
 */
export const revokeAllSessions = async (
  data?: RevokeAllSessionsRequest
): Promise<{ revoked_count: number }> => {
  const response = await apiClient.post(API_ENDPOINTS.SESSIONS.REVOKE_ALL, data)
  return response.data
}

// ============================================================================
// Export all functions
// ============================================================================

export default {
  getSessions,
  getSession,
  getSessionStats,
  getActiveSessions,
  getUserSessions,
  getSessionsByIP,
  revokeSession,
  revokeAllSessions,
}
