/**
 * Decisions API - Phase A+
 * API calls for decision management
 */

import { apiClient } from '../../../shared/lib/axios'
import type {
  DecisionListResponse,
  DecisionDetail,
  CreateDecisionRequest,
  CreateDecisionResponse
} from '../types/Decision'

/**
 * Get list of all decisions
 */
export async function getDecisions(limit = 100): Promise<DecisionListResponse> {
  const response = await apiClient.get<DecisionListResponse>('/decisions', {
    params: { limit }
  })
  return response.data
}

/**
 * Get decision detail with workflow info
 */
export async function getDecisionDetail(decisionId: string): Promise<DecisionDetail> {
  const response = await apiClient.get<DecisionDetail>(`/decisions/${decisionId}`)
  return response.data
}

/**
 * Create new decision
 */
export async function createDecision(
  request: CreateDecisionRequest
): Promise<CreateDecisionResponse> {
  const response = await apiClient.post<CreateDecisionResponse>('/api/v1/decisions', request)
  return response.data
}
