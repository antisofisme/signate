/**
 * Tenant Feature Module
 *
 * Export all tenant-related types, API functions, and hooks.
 */

// Types
export type {
  MemberRole,
  TenantStatus,
  TenantPlan,
  MembershipStatus,
  InvitationStatus,
  TenantPlanLimits,
  Tenant,
  TenantMembership,
  TenantMember,
  Invitation,
  TenantWithMembership,
  CreateTenantRequest,
  UpdateTenantRequest,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  AcceptInvitationRequest,
  CreateTenantResponse,
  TenantDetailResponse,
  ListTenantsResponse,
  ListMembersResponse,
  ListInvitationsResponse,
  InvitationCreateResponse,
  InvitationAcceptResponse,
  MemberRoleUpdateResponse,
  SuccessResponse,
} from './types'

// API
export * as tenantApi from './api'

// Hooks
export {
  tenantKeys,
  useTenants,
  useTenant,
  useTenantMembers,
  useTenantInvitations,
  useCreateTenant,
  useUpdateTenant,
  useDeleteTenant,
  useUpdateMemberRole,
  useRemoveMember,
  useLeaveTenant,
  useInviteMember,
  useAcceptInvitation,
  useCancelInvitation,
} from './hooks'
