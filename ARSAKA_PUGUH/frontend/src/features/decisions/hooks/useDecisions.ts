/**
 * useDecisions Hook - Phase A+
 * Custom hook for fetching decisions list
 */

import { useQuery } from '@tanstack/react-query'
import { getDecisions } from '../api/decisions'

export function useDecisions(limit = 100) {
  return useQuery({
    queryKey: ['decisions', limit],
    queryFn: () => getDecisions(limit),
    // Phase A+: Simple caching, no sophisticated strategies
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })
}
