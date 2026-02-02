/**
 * Workflows API - Phase A+
 * API calls for approval workflow management
 */

import { apiClient } from '../../../shared/lib/axios'
import type { WorkflowListResponse } from '../types/Workflow'

/**
 * Get list of workflows (optionally filtered by state)
 */
export async function getWorkflows(state?: string): Promise<WorkflowListResponse> {
  const response = await apiClient.get<WorkflowListResponse>('/workflows', {
    params: state ? { state } : undefined,
  })
  return response.data
}
