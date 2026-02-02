/**
 * Tenant API Functions
 *
 * API functions for tenant management.
 */

import apiClient from '@/shared/api/client'
import type {
  CreateTenantRequest,
  CreateTenantResponse,
  UpdateTenantRequest,
  ListTenantsResponse,
  TenantDetailResponse,
  SuccessResponse,
  InviteMemberRequest,
  InvitationCreateResponse,
  AcceptInvitationRequest,
  InvitationAcceptResponse,
  ListMembersResponse,
  ListInvitationsResponse,
  UpdateMemberRoleRequest,
  MemberRoleUpdateResponse,
  Tenant,
} from '../types'

const BASE_URL = '/tenants'

// ============================================
// Tenant CRUD
// ============================================

/**
 * Create a new tenant
 */
export async function createTenant(data: CreateTenantRequest): Promise<CreateTenantResponse> {
  const response = await apiClient.post<CreateTenantResponse>(BASE_URL, data)
  return response.data
}

/**
 * List user's tenants
 */
export async function listTenants(includeInactive = false): Promise<ListTenantsResponse> {
  const response = await apiClient.get<ListTenantsResponse>(BASE_URL, {
    params: { include_inactive: includeInactive },
  })
  return response.data
}

/**
 * Get tenant by ID
 */
export async function getTenant(tenantId: string): Promise<TenantDetailResponse> {
  const response = await apiClient.get<TenantDetailResponse>(`${BASE_URL}/${tenantId}`)
  return response.data
}

/**
 * Update tenant
 */
export async function updateTenant(
  tenantId: string,
  data: UpdateTenantRequest
): Promise<{ success: boolean; data: Tenant; message: string }> {
  const response = await apiClient.patch<{ success: boolean; data: Tenant; message: string }>(
    `${BASE_URL}/${tenantId}`,
    data
  )
  return response.data
}

/**
 * Delete tenant (soft delete)
 */
export async function deleteTenant(tenantId: string): Promise<SuccessResponse> {
  const response = await apiClient.delete<SuccessResponse>(`${BASE_URL}/${tenantId}`)
  return response.data
}

// ============================================
// Members
// ============================================

/**
 * List tenant members
 */
export async function listMembers(
  tenantId: string,
  includeInvitations = true
): Promise<ListMembersResponse> {
  const response = await apiClient.get<ListMembersResponse>(`${BASE_URL}/${tenantId}/members`, {
    params: { include_invitations: includeInvitations },
  })
  return response.data
}

/**
 * Update member role
 */
export async function updateMemberRole(
  tenantId: string,
  memberUserId: string,
  data: UpdateMemberRoleRequest
): Promise<MemberRoleUpdateResponse> {
  const response = await apiClient.patch<MemberRoleUpdateResponse>(
    `${BASE_URL}/${tenantId}/members/${memberUserId}/role`,
    data
  )
  return response.data
}

/**
 * Remove member from tenant
 */
export async function removeMember(
  tenantId: string,
  memberUserId: string,
  reason?: string
): Promise<SuccessResponse> {
  const response = await apiClient.delete<SuccessResponse>(
    `${BASE_URL}/${tenantId}/members/${memberUserId}`,
    { params: { reason } }
  )
  return response.data
}

/**
 * Leave tenant
 */
export async function leaveTenant(tenantId: string): Promise<SuccessResponse> {
  const response = await apiClient.post<SuccessResponse>(`${BASE_URL}/${tenantId}/leave`)
  return response.data
}

// ============================================
// Invitations
// ============================================

/**
 * Invite member to tenant
 */
export async function inviteMember(
  tenantId: string,
  data: InviteMemberRequest
): Promise<InvitationCreateResponse> {
  const response = await apiClient.post<InvitationCreateResponse>(
    `${BASE_URL}/${tenantId}/invitations`,
    data
  )
  return response.data
}

/**
 * List tenant invitations
 */
export async function listInvitations(
  tenantId: string,
  status?: string,
  limit = 50,
  offset = 0
): Promise<ListInvitationsResponse> {
  const response = await apiClient.get<ListInvitationsResponse>(
    `${BASE_URL}/${tenantId}/invitations`,
    { params: { status, limit, offset } }
  )
  return response.data
}

/**
 * Accept invitation
 */
export async function acceptInvitation(
  data: AcceptInvitationRequest
): Promise<InvitationAcceptResponse> {
  const response = await apiClient.post<InvitationAcceptResponse>(
    `${BASE_URL}/invitations/accept`,
    data
  )
  return response.data
}

/**
 * Cancel invitation
 */
export async function cancelInvitation(
  tenantId: string,
  invitationId: string
): Promise<void> {
  await apiClient.delete(`${BASE_URL}/${tenantId}/invitations/${invitationId}`)
}
