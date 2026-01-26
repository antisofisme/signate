/**
 * IAM Domain - TypeScript Types
 * Following ATLAS_PANDAWA standards
 */

// Re-export from shared
export type { User, UserRole, TenantMembership } from '@/shared/types'
import type { UserRole } from '@/shared/types'

// Domain-specific types
export interface UserFilters {
  search?: string
  role?: UserRole
  status?: 'active' | 'inactive'
}

export interface UserStats {
  total: number
  active: number
  admins: number
  recentlyAdded: number
}

export interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
  userCount: number
  createdAt: string
  updatedAt?: string
}

export interface Permission {
  id: string
  code: string
  name: string
  description: string
  module: string
}

export interface ServiceAccount {
  id: string
  name: string
  description?: string
  clientId: string
  permissions: string[]
  lastUsedAt?: string
  createdAt: string
}

// Role constants
export const USER_ROLE_LABELS: Record<UserRole, string> = {
  SUPER_ADMIN: 'Super Admin',
  ADMIN: 'Administrator',
  OPERATOR: 'Operator',
  VIEWER: 'Viewer',
}

export const USER_ROLE_COLORS: Record<UserRole, string> = {
  SUPER_ADMIN: 'destructive',
  ADMIN: 'default',
  OPERATOR: 'secondary',
  VIEWER: 'outline',
}
