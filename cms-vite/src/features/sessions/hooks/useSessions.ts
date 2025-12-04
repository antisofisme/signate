/**
 * useSessions Hook
 * React Query hooks for session management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from '@/shared/utils/toast'
import * as sessionApi from '../api/sessionApi'
import type {
  SessionFilters,
  RevokeSessionRequest,
  RevokeAllSessionsRequest,
  AllSessionsParams,
} from '../types/session.types'
import { getApiErrorMessage } from '@/shared/utils/types'

// ============================================================================
// Query Keys
// ============================================================================

export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters?: SessionFilters) => [...sessionKeys.lists(), filters] as const,
  details: () => [...sessionKeys.all, 'detail'] as const,
  detail: (id: number) => [...sessionKeys.details(), id] as const,
  stats: () => [...sessionKeys.all, 'stats'] as const,
  active: () => [...sessionKeys.all, 'active'] as const,
  allActive: (params?: AllSessionsParams) => [...sessionKeys.all, 'all-active', params] as const,
  userSessions: (userId: number) => ['users', userId, 'sessions'] as const,
}

// ============================================================================
// Session Queries
// ============================================================================

/**
 * Get current user's sessions
 */
export function useSessions(filters?: SessionFilters) {
  return useQuery({
    queryKey: sessionKeys.list(filters),
    queryFn: () => sessionApi.getSessions(filters),
    staleTime: 1 * 60 * 1000, // 1 minute (sessions change frequently)
  })
}

/**
 * Get single session by ID
 */
export function useSession(id: number | undefined) {
  return useQuery({
    queryKey: sessionKeys.detail(id!),
    queryFn: () => sessionApi.getSession(id!),
    enabled: !!id,
    staleTime: 1 * 60 * 1000,
  })
}

/**
 * Get session statistics
 */
export function useSessionStats() {
  return useQuery({
    queryKey: sessionKeys.stats(),
    queryFn: () => sessionApi.getSessionStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Get active sessions only
 */
export function useActiveSessions() {
  return useQuery({
    queryKey: sessionKeys.active(),
    queryFn: () => sessionApi.getActiveSessions(),
    staleTime: 30 * 1000, // 30 seconds (active sessions change frequently)
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  })
}

/**
 * Get sessions for specific user (admin only)
 */
export function useUserSessions(userId: number | undefined) {
  return useQuery({
    queryKey: sessionKeys.userSessions(userId!),
    queryFn: () => sessionApi.getUserSessions(userId!),
    enabled: !!userId,
    staleTime: 1 * 60 * 1000,
  })
}

/**
 * Get all active sessions with user and organization info (admin only)
 * - Super Admin: sees all sessions from all organizations
 * - Admin: sees sessions from their organization only
 */
export function useAllActiveSessions(params?: AllSessionsParams) {
  return useQuery({
    queryKey: sessionKeys.allActive(params),
    queryFn: () => sessionApi.getAllActiveSessions(params),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  })
}

// ============================================================================
// Session Mutations
// ============================================================================

/**
 * Revoke specific session (logout from device)
 */
export function useRevokeSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RevokeSessionRequest) => sessionApi.revokeSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: sessionKeys.active() })
      queryClient.invalidateQueries({ queryKey: sessionKeys.stats() })
      toast.success('Session revoked successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to revoke session'))
    },
  })
}

/**
 * Revoke all sessions except current (logout from all devices)
 */
export function useRevokeAllSessions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data?: RevokeAllSessionsRequest) => sessionApi.revokeAllSessions(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() })
      queryClient.invalidateQueries({ queryKey: sessionKeys.active() })
      queryClient.invalidateQueries({ queryKey: sessionKeys.stats() })
      toast.success(`${data.revoked_count} session(s) revoked successfully`)
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to revoke sessions'))
    },
  })
}

// ============================================================================
// Helper Hooks
// ============================================================================

/**
 * Get current session info
 */
export function useCurrentSession() {
  const { data: sessions, isLoading } = useSessions()

  const currentSession = sessions?.sessions.find((s) => s.is_current)

  return {
    currentSession,
    isLoading,
  }
}

/**
 * Get session count
 */
export function useSessionCount() {
  const { data: sessions } = useSessions()

  return {
    total: sessions?.total || 0,
    active: sessions?.active_count || 0,
  }
}

/**
 * Check if user has multiple active sessions
 */
export function useHasMultipleSessions() {
  const { data: sessions } = useActiveSessions()

  return {
    hasMultiple: (sessions?.active_count || 0) > 1,
    count: sessions?.active_count || 0,
  }
}
