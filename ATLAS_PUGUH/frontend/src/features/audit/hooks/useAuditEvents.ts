/**
 * useAuditEvents Hook - Phase A+
 * Custom hook for fetching audit events
 */

import { useQuery } from '@tanstack/react-query'
import { getAuditEvents } from '../api/audit'

export function useAuditEvents(limit = 100) {
  return useQuery({
    queryKey: ['audit-events', limit],
    queryFn: () => getAuditEvents(limit),
    // Phase A+: Simple caching, no sophisticated strategies
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })
}
