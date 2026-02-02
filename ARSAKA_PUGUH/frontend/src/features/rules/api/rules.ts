/**
 * Rules API - Phase A+
 */

import { apiClient } from '../../../shared/lib/axios'
import type { RuleListResponse, Rule, CreateRuleRequest } from '../types/Rule'

const TENANT_ID = '550e8400-e29b-41d4-a716-446655440000'

export async function getRules(): Promise<RuleListResponse> {
  const response = await apiClient.get<RuleListResponse>('/rules', {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function getRuleById(ruleId: string): Promise<Rule> {
  const response = await apiClient.get<Rule>(`/rules/${ruleId}`, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function createRule(request: CreateRuleRequest): Promise<Rule> {
  const response = await apiClient.post<Rule>('/rules', {
    ...request,
    tenant_id: TENANT_ID
  })
  return response.data
}

export async function activateRule(ruleId: string): Promise<Rule> {
  const response = await apiClient.post<Rule>(`/rules/${ruleId}/activate`, {
    tenant_id: TENANT_ID
  })
  return response.data
}

export async function deactivateRule(ruleId: string): Promise<Rule> {
  const response = await apiClient.post<Rule>(`/rules/${ruleId}/deactivate`, {
    tenant_id: TENANT_ID
  })
  return response.data
}
