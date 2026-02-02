/**
 * useDecisionDetail Hook - Phase A+
 * Custom hook for fetching single decision detail
 */

import { useQuery } from '@tanstack/react-query'
import { getDecisionDetail } from '../api/decisions'

export function useDecisionDetail(decisionId: string | undefined) {
  return useQuery({
    queryKey: ['decision', decisionId],
    queryFn: () => {
      if (!decisionId) {
        throw new Error('Decision ID is required')
      }
      return getDecisionDetail(decisionId)
    },
    enabled: !!decisionId, // Only run if decisionId exists
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })
}
