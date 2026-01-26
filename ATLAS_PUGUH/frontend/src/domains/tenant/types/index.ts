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
  role: string
  joinedAt: string
}

export interface IsolationCheckResult {
  passed: boolean
  checks: {
    name: string
    status: 'passed' | 'failed' | 'warning'
    message: string
  }[]
  checkedAt: string
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
