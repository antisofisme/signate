/**
 * Tenant Domain - TypeScript Types
 */

// Re-export from shared
export type { Tenant, TenantStatus } from '@/shared/types'
import type { TenantStatus } from '@/shared/types'

// Domain-specific types
export interface TenantFilters {
  search?: string
  status?: TenantStatus
}

export interface TenantMember {
  id: string
  userId: string
  userName: string
  userEmail: string
  role: TenantRole
  joinedAt: string
}

export type TenantRole = 'OWNER' | 'ADMIN' | 'OPERATOR' | 'VIEWER'

export interface IsolationCheckResult {
  passed: boolean
  checks: {
    name: string
    status: 'passed' | 'failed' | 'warning'
    message: string
  }[]
  checkedAt: string
}

// ============================================
// Mutation Request Types
// ============================================

export interface CreateTenantRequest {
  name: string
  slug: string
  settings?: TenantSettings
}

export interface UpdateTenantRequest {
  name?: string
  settings?: TenantSettings
}

export interface TenantSettings {
  timezone?: string
  currency?: string
  language?: string
}

export interface InviteMemberRequest {
  email: string
  role: TenantRole
}

export interface AcceptInvitationRequest {
  token: string
}

export interface UpdateMemberRoleRequest {
  role: TenantRole
}

export interface TenantInvitation {
  id: string
  email: string
  role: TenantRole
  status: 'pending' | 'accepted' | 'expired'
  expiresAt: string
  createdAt: string
}

// Constants
export const TENANT_STATUS_LABELS: Record<TenantStatus, string> = {
  active: 'Active',
  suspended: 'Suspended',
  pending: 'Pending',
}

export const TENANT_STATUS_COLORS: Record<TenantStatus, string> = {
  active: 'success',
  suspended: 'destructive',
  pending: 'warning',
}

export const TENANT_ROLE_LABELS: Record<TenantRole, string> = {
  OWNER: 'Owner',
  ADMIN: 'Admin',
  OPERATOR: 'Operator',
  VIEWER: 'Viewer',
}

export const TENANT_ROLE_DESCRIPTIONS: Record<TenantRole, string> = {
  OWNER: 'Full access, can delete tenant',
  ADMIN: 'Full access, cannot delete tenant',
  OPERATOR: 'Can manage rules and workflows',
  VIEWER: 'Read-only access',
}
