/**
 * RBAC Types
 * Type definitions for Role-Based Access Control
 *
 * Note: This file is kept for backwards compatibility.
 * New code should use types from '../constants/permissions.ts'
 */

import type { Permissions } from '../constants/permissions';

// Re-export new types
export type { Permissions } from '../constants/permissions';

// ============================================================================
// Core Types (Updated for new format)
// ============================================================================

export type PermissionAction = 'view' | 'create' | 'edit' | 'delete' | 'manage';

export type PermissionResource =
  | 'dashboard'
  | 'devices'
  | 'device_groups'
  | 'contents'
  | 'playlists'
  | 'schedules'
  | 'tags'
  | 'menus'
  | 'analytics'
  | 'audit_logs'
  | 'users'
  | 'organizations'
  | 'roles'
  | 'sessions'
  | 'settings'
  | 'system';

// Legacy Permission interface (for backwards compatibility with old API)
export interface Permission {
  id: number;
  name: string;
  resource: string;
  action: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

// Updated Role interface with new permissions format
export interface Role {
  id: number;
  name: string;
  description?: string;
  is_system_role?: boolean;
  is_active?: boolean;
  organization_id?: number;
  created_at?: string;
  updated_at?: string;
  // Audit trail fields
  created_by_id?: number;
  updated_by_id?: number;
  // New format: {resource: [actions]}
  permissions?: Permissions;
  users_count?: number;
}

export interface RoleWithPermissions extends Role {
  permissions: Permissions;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface RoleListResponse {
  roles: Role[];
  total: number;
  page?: number;
  per_page?: number;
}

export interface CreateRoleRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  organization_id?: number;
  permissions?: Permissions;
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  permissions?: Permissions;
}

export interface RoleFilters {
  search?: string;
  is_system?: boolean;
  is_active?: boolean;
  organization_id?: number;
  skip?: number;
  limit?: number;
}

// ============================================================================
// Permission Checking
// ============================================================================

export interface PermissionCheck {
  resource: PermissionResource;
  action: PermissionAction;
}

export interface HasPermissionRequest {
  resource: PermissionResource;
  action: PermissionAction;
  user_id?: number;
}

export interface HasPermissionResponse {
  has_permission: boolean;
  reason?: string;
}

// ============================================================================
// Permission Matrix (legacy - now uses Permissions type directly)
// ============================================================================

export interface PermissionMatrix {
  [resource: string]: {
    [action: string]: boolean;
  };
}

export interface RolePermissionMatrix {
  role_id: number;
  role_name: string;
  matrix: PermissionMatrix;
}

// ============================================================================
// System Roles
// ============================================================================

export enum SystemRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  ADMIN = 'ADMIN',
  CONTENT_MANAGER = 'CONTENT_MANAGER',
  VIEWER = 'VIEWER',
}

// ============================================================================
// User Role Assignment
// ============================================================================

export interface UserRole {
  user_id: number;
  role_id: number;
  role_name: string;
  assigned_at: string;
  assigned_by?: number;
}

export interface UserWithRoles {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  roles: Role[];
}

// ============================================================================
// Permission Assignment Types (for API compatibility)
// ============================================================================

export interface AssignPermissionsRequest {
  permission_ids: number[];
}

export interface RemovePermissionsRequest {
  permission_ids: number[];
}

export interface AssignUsersToRoleRequest {
  user_ids: number[];
}

export interface RemoveUsersFromRoleRequest {
  user_ids: number[];
}

// ============================================================================
// Constants (use from constants/permissions.ts instead)
// ============================================================================

export const PERMISSION_ACTIONS: PermissionAction[] = [
  'view',
  'create',
  'edit',
  'delete',
  'manage',
];

export const PERMISSION_RESOURCES: PermissionResource[] = [
  'dashboard',
  'devices',
  'device_groups',
  'contents',
  'playlists',
  'schedules',
  'tags',
  'menus',
  'analytics',
  'audit_logs',
  'users',
  'organizations',
  'roles',
  'sessions',
  'settings',
  'system',
];

// ============================================================================
// Helper Types
// ============================================================================

export type PermissionString = `${PermissionResource}:${PermissionAction}`;

export interface PermissionDescription {
  resource: PermissionResource;
  action: PermissionAction;
  label: string;
  description: string;
  icon?: string;
}
