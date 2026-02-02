/**
 * Rules Hooks - Phase A+
 */

import { useQuery } from '@tanstack/react-query'
import { getRules } from '../api/rules'

export function useRules() {
  return useQuery({
    queryKey: ['rules'],
    queryFn: getRules,
    staleTime: 30000,
  })
}
