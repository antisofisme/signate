/**
 * Audit API - Phase A+
 * API calls for audit trail
 */

import { apiClient } from '../../../shared/lib/axios'
import type { AuditEventListResponse } from '../types/AuditEvent'

/**
 * Get list of audit events
 */
export async function getAuditEvents(limit = 100): Promise<AuditEventListResponse> {
  const response = await apiClient.get<AuditEventListResponse>('/audit', {
    params: { limit },
  })
  return response.data
}
