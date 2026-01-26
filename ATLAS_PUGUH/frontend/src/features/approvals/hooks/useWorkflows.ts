/**
 * useWorkflows Hook - Phase A+
 * Custom hook for fetching workflows list
 */

import { useQuery } from '@tanstack/react-query'
import { getWorkflows } from '../api/workflows'

export function useWorkflows(state?: string) {
  return useQuery({
    queryKey: ['workflows', state],
    queryFn: () => getWorkflows(state),
    // Phase A+: Simple caching, no sophisticated strategies
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })
}
