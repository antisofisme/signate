/**
 * Configuration Master Data API Client
 * CRUD operations for customer-defined master data
 */

import { apiClient } from '../../../shared/lib/axios'
import type {
  FunctionalAreasResponse,
  FunctionalArea,
  FunctionalAreaCreate,
  FunctionalAreaUpdate,
  DecisionTypesResponse,
  DecisionType,
  DecisionTypeCreate,
  DecisionTypeUpdate,
  ApproverRolesResponse,
  ApproverRole,
  ApproverRoleCreate,
  ApproverRoleUpdate
} from '../types/Config'

const TENANT_ID = '550e8400-e29b-41d4-a716-446655440000'

// ============================================================================
// FUNCTIONAL AREAS
// ============================================================================

export async function getFunctionalAreas(activeOnly: boolean = true): Promise<FunctionalAreasResponse> {
  const response = await apiClient.get<FunctionalAreasResponse>('/config/functional-areas', {
    params: { tenant_id: TENANT_ID, active_only: activeOnly }
  })
  return response.data
}

export async function createFunctionalArea(data: FunctionalAreaCreate): Promise<FunctionalArea> {
  const response = await apiClient.post<FunctionalArea>('/config/functional-areas', data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function updateFunctionalArea(areaId: string, data: FunctionalAreaUpdate): Promise<FunctionalArea> {
  const response = await apiClient.patch<FunctionalArea>(`/config/functional-areas/${areaId}`, data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function deleteFunctionalArea(areaId: string): Promise<void> {
  await apiClient.delete(`/config/functional-areas/${areaId}`, {
    params: { tenant_id: TENANT_ID }
  })
}

// ============================================================================
// DECISION TYPES
// ============================================================================

export async function getDecisionTypes(activeOnly: boolean = true): Promise<DecisionTypesResponse> {
  const response = await apiClient.get<DecisionTypesResponse>('/config/decision-types', {
    params: { tenant_id: TENANT_ID, active_only: activeOnly }
  })
  return response.data
}

export async function createDecisionType(data: DecisionTypeCreate): Promise<DecisionType> {
  const response = await apiClient.post<DecisionType>('/config/decision-types', data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function updateDecisionType(typeId: string, data: DecisionTypeUpdate): Promise<DecisionType> {
  const response = await apiClient.patch<DecisionType>(`/config/decision-types/${typeId}`, data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function deleteDecisionType(typeId: string): Promise<void> {
  await apiClient.delete(`/config/decision-types/${typeId}`, {
    params: { tenant_id: TENANT_ID }
  })
}

// ============================================================================
// APPROVER ROLES
// ============================================================================

export async function getApproverRoles(activeOnly: boolean = true): Promise<ApproverRolesResponse> {
  const response = await apiClient.get<ApproverRolesResponse>('/config/approver-roles', {
    params: { tenant_id: TENANT_ID, active_only: activeOnly }
  })
  return response.data
}

export async function createApproverRole(data: ApproverRoleCreate): Promise<ApproverRole> {
  const response = await apiClient.post<ApproverRole>('/config/approver-roles', data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function updateApproverRole(roleId: string, data: ApproverRoleUpdate): Promise<ApproverRole> {
  const response = await apiClient.patch<ApproverRole>(`/config/approver-roles/${roleId}`, data, {
    params: { tenant_id: TENANT_ID }
  })
  return response.data
}

export async function deleteApproverRole(roleId: string): Promise<void> {
  await apiClient.delete(`/config/approver-roles/${roleId}`, {
    params: { tenant_id: TENANT_ID }
  })
}
