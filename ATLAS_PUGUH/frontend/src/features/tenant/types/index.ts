/**
 * Tenant Feature Types
 *
 * Type definitions for tenant management API.
 */

// ============================================
// Enums & Constants
// ============================================

export type MemberRole = 'owner' | 'admin' | 'member' | 'viewer'
export type TenantStatus = 'active' | 'suspended' | 'trial'
export type TenantPlan = 'free' | 'starter' | 'pro' | 'enterprise'
export type MembershipStatus = 'active' | 'invited' | 'suspended'
export type InvitationStatus = 'pending' | 'accepted' | 'rejected' | 'expired' | 'cancelled'

// ============================================
// Core Entities
// ============================================

export interface TenantPlanLimits {
  max_projects: number
  max_members: number
  max_decisions_per_month: number
}

export interface Tenant {
  tenant_id: string
  name: string
  slug: string
  owner_user_id: string
  plan: TenantPlan
  status: TenantStatus
  settings: Record<string, unknown>
  billing_email: string | null
  limits: TenantPlanLimits
  created_at: string
  updated_at: string
}

export interface TenantMembership {
  membership_id: string
  user_id: string
  tenant_id: string
  role: MemberRole
  status: MembershipStatus
  invited_by_user_id: string | null
  invited_at: string | null
  joined_at: string | null
  created_at: string
}

export interface TenantMember {
  membership: TenantMembership
  user_email: string | null
  user_name: string | null
}

export interface Invitation {
  invitation_id: string
  email: string
  tenant_id: string
  role: MemberRole
  status: InvitationStatus
  invited_by_user_id: string
  message: string | null
  expires_at: string
  is_expired: boolean
  created_at: string
}

export interface TenantWithMembership {
  tenant: Tenant
  role: MemberRole
  member_count: number
}

// ============================================
// Request Types
// ============================================

export interface CreateTenantRequest {
  name: string
  slug?: string
  billing_email?: string
}

export interface UpdateTenantRequest {
  name?: string
  billing_email?: string
  settings?: Record<string, unknown>
}

export interface InviteMemberRequest {
  email: string
  role: MemberRole
  message?: string
}

export interface UpdateMemberRoleRequest {
  role: MemberRole
}

export interface AcceptInvitationRequest {
  token: string
}

// ============================================
// Response Types
// ============================================

export interface CreateTenantResponse {
  success: boolean
  data: {
    tenant: Tenant
    membership: TenantMembership
  }
  message: string
}

export interface TenantDetailResponse {
  success: boolean
  data: TenantWithMembership
}

export interface ListTenantsResponse {
  success: boolean
  data: TenantWithMembership[]
  meta: {
    total: number
  }
}

export interface ListMembersResponse {
  success: boolean
  data: {
    members: TenantMember[]
    pending_invitations: Invitation[]
  }
  meta: {
    total_members: number
    total_pending: number
  }
}

export interface ListInvitationsResponse {
  success: boolean
  data: Invitation[]
  meta: {
    limit: number
    offset: number
  }
}

export interface InvitationCreateResponse {
  success: boolean
  data: Invitation
  message: string
}

export interface InvitationAcceptResponse {
  success: boolean
  data: {
    membership: TenantMembership
    tenant_id: string
  }
  message: string
}

export interface MemberRoleUpdateResponse {
  success: boolean
  data: {
    old_role: MemberRole
    new_role: MemberRole
  }
  message: string
}

export interface SuccessResponse {
  success: boolean
  message: string
}
