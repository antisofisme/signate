/**
 * RBAC Types
 * Type definitions for Role-Based Access Control
 */

// ============================================================================
// Core Types
// ============================================================================

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'manage'

export type PermissionResource =
  | 'users'
  | 'roles'
  | 'organizations'
  | 'devices'
  | 'content'
  | 'playlists'
  | 'schedules'
  | 'widgets'
  | 'templates'
  | 'tags'
  | 'analytics'
  | 'audit'
  | 'translations'
  | 'pms'
  | 'weather'
  | 'settings'

export interface Permission {
  id: number
  name: string
  resource: PermissionResource
  action: PermissionAction
  description?: string
  created_at: string
  updated_at: string
}

export interface Role {
  id: number
  name: string
  description?: string
  is_system: boolean
  is_active: boolean
  organization_id?: number
  created_at: string
  updated_at: string
  // Audit trail fields (Migration 046)
  created_by_id?: number
  updated_by_id?: number
  permissions?: Permission[]
  users_count?: number
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[]
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface RoleListResponse {
  roles: Role[]
  total: number
  page?: number
  per_page?: number
}

export interface CreateRoleRequest {
  name: string
  description?: string
  is_active?: boolean
  organization_id?: number
}

export interface UpdateRoleRequest {
  name?: string
  description?: string
  is_active?: boolean
}

export interface RoleFilters {
  search?: string
  is_system?: boolean
  is_active?: boolean
  organization_id?: number
  skip?: number
  limit?: number
}

export interface AssignPermissionsRequest {
  permission_ids: number[]
}

export interface RemovePermissionsRequest {
  permission_ids: number[]
}

export interface AssignUsersToRoleRequest {
  user_ids: number[]
}

export interface RemoveUsersFromRoleRequest {
  user_ids: number[]
}

// ============================================================================
// Permission Checking
// ============================================================================

export interface PermissionCheck {
  resource: PermissionResource
  action: PermissionAction
}

export interface HasPermissionRequest {
  resource: PermissionResource
  action: PermissionAction
  user_id?: number
}

export interface HasPermissionResponse {
  has_permission: boolean
  reason?: string
}

// ============================================================================
// Permission Matrix
// ============================================================================

export interface PermissionMatrix {
  [resource: string]: {
    [action: string]: boolean
  }
}

export interface RolePermissionMatrix {
  role_id: number
  role_name: string
  matrix: PermissionMatrix
}

// ============================================================================
// System Roles
// ============================================================================

export enum SystemRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  MANAGER = 'manager',
  OPERATOR = 'operator',
  VIEWER = 'viewer',
}

// ============================================================================
// User Role Assignment
// ============================================================================

export interface UserRole {
  user_id: number
  role_id: number
  role_name: string
  assigned_at: string
  assigned_by?: number
}

export interface UserWithRoles {
  id: number
  username: string
  email: string
  full_name?: string
  roles: Role[]
}

// ============================================================================
// Constants
// ============================================================================

export const PERMISSION_ACTIONS: PermissionAction[] = [
  'create',
  'read',
  'update',
  'delete',
  'manage',
]

export const PERMISSION_RESOURCES: PermissionResource[] = [
  'users',
  'roles',
  'organizations',
  'devices',
  'content',
  'playlists',
  'schedules',
  'widgets',
  'templates',
  'tags',
  'analytics',
  'audit',
  'translations',
  'pms',
  'weather',
  'settings',
]

// ============================================================================
// Helper Types
// ============================================================================

export type PermissionString = `${PermissionResource}:${PermissionAction}`

export interface PermissionDescription {
  resource: PermissionResource
  action: PermissionAction
  label: string
  description: string
  icon?: string
}
