/**
 * RBAC API Client
 * API functions for Role-Based Access Control management
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  Role,
  RoleWithPermissions,
  RoleListResponse,
  CreateRoleRequest,
  UpdateRoleRequest,
  RoleFilters,
  Permission,
  AssignPermissionsRequest,
  RemovePermissionsRequest,
  AssignUsersToRoleRequest,
  RemoveUsersFromRoleRequest,
  UserWithRoles,
  HasPermissionRequest,
  HasPermissionResponse,
} from '../types/rbac.types'

// ============================================================================
// Roles Management
// ============================================================================

/**
 * Get list of roles with optional filters
 */
export const getRoles = async (filters?: RoleFilters): Promise<RoleListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.LIST, {
    params: filters,
  })
  return response.data
}

/**
 * Get single role by ID
 */
export const getRole = async (id: number): Promise<Role> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.GET(id))
  return response.data
}

/**
 * Get role with its permissions
 */
export const getRoleWithPermissions = async (id: number): Promise<RoleWithPermissions> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.GET(id))
  return response.data
}

/**
 * Create new role
 */
export const createRole = async (data: CreateRoleRequest): Promise<Role> => {
  const response = await apiClient.post(API_ENDPOINTS.RBAC.ROLES.CREATE, data)
  return response.data
}

/**
 * Update existing role
 */
export const updateRole = async (id: number, data: UpdateRoleRequest): Promise<Role> => {
  const response = await apiClient.put(API_ENDPOINTS.RBAC.ROLES.UPDATE(id), data)
  return response.data
}

/**
 * Delete role
 */
export const deleteRole = async (id: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.RBAC.ROLES.DELETE(id))
}

/**
 * Get system roles
 */
export const getSystemRoles = async (): Promise<Role[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.SYSTEM)
  return response.data
}

// ============================================================================
// Role Permissions Management
// ============================================================================

/**
 * Get permissions for a role
 */
export const getRolePermissions = async (roleId: number): Promise<Permission[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.GET_PERMISSIONS(roleId))
  return response.data
}

/**
 * Add permissions to role
 */
export const addPermissionsToRole = async (
  roleId: number,
  data: AssignPermissionsRequest
): Promise<void> => {
  await apiClient.post(API_ENDPOINTS.RBAC.ROLES.ADD_PERMISSIONS(roleId), data)
}

/**
 * Remove permissions from role
 */
export const removePermissionsFromRole = async (
  roleId: number,
  data: RemovePermissionsRequest
): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.RBAC.ROLES.REMOVE_PERMISSIONS(roleId), {
    data,
  })
}

// ============================================================================
// Role Users Management
// ============================================================================

/**
 * Get users assigned to a role
 */
export const getRoleUsers = async (roleId: number): Promise<UserWithRoles[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.ROLES.GET_USERS(roleId))
  return response.data
}

/**
 * Assign users to role
 */
export const assignUsersToRole = async (
  roleId: number,
  data: AssignUsersToRoleRequest
): Promise<void> => {
  await apiClient.post(API_ENDPOINTS.RBAC.ROLES.ASSIGN_USERS(roleId), data)
}

/**
 * Remove users from role
 */
export const removeUsersFromRole = async (
  roleId: number,
  data: RemoveUsersFromRoleRequest
): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.RBAC.ROLES.REMOVE_USERS(roleId), {
    data,
  })
}

// ============================================================================
// Permissions Management
// ============================================================================

/**
 * Get all permissions
 */
export const getPermissions = async (): Promise<Permission[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.PERMISSIONS.LIST)
  return response.data
}

/**
 * Get single permission by ID
 */
export const getPermission = async (id: number): Promise<Permission> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.PERMISSIONS.GET(id))
  return response.data
}

/**
 * Get permissions by resource
 */
export const getPermissionsByResource = async (resource: string): Promise<Permission[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.PERMISSIONS.BY_RESOURCE(resource))
  return response.data
}

// ============================================================================
// User Permissions Management
// ============================================================================

/**
 * Get user's permissions
 */
export const getUserPermissions = async (userId: number): Promise<Permission[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.USER_PERMISSIONS.GET(userId))
  return response.data
}

/**
 * Check if user has specific permission
 */
export const checkUserPermission = async (
  userId: number,
  data: HasPermissionRequest
): Promise<HasPermissionResponse> => {
  const response = await apiClient.post(
    API_ENDPOINTS.RBAC.USER_PERMISSIONS.CHECK(userId),
    data
  )
  return response.data
}

/**
 * Get user's roles
 */
export const getUserRoles = async (userId: number): Promise<Role[]> => {
  const response = await apiClient.get(API_ENDPOINTS.RBAC.USER_PERMISSIONS.GET_ROLES(userId))
  return response.data
}

/**
 * Assign role to user
 */
export const assignRoleToUser = async (userId: number, roleId: number): Promise<void> => {
  await apiClient.post(API_ENDPOINTS.RBAC.USER_PERMISSIONS.ASSIGN_ROLE(userId), {
    role_id: roleId,
  })
}

/**
 * Remove role from user
 */
export const removeRoleFromUser = async (userId: number, roleId: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.RBAC.USER_PERMISSIONS.REMOVE_ROLE(userId, roleId))
}

// ============================================================================
// Export all functions
// ============================================================================

export default {
  // Roles
  getRoles,
  getRole,
  getRoleWithPermissions,
  createRole,
  updateRole,
  deleteRole,
  getSystemRoles,

  // Role Permissions
  getRolePermissions,
  addPermissionsToRole,
  removePermissionsFromRole,

  // Role Users
  getRoleUsers,
  assignUsersToRole,
  removeUsersFromRole,

  // Permissions
  getPermissions,
  getPermission,
  getPermissionsByResource,

  // User Permissions
  getUserPermissions,
  checkUserPermission,
  getUserRoles,
  assignRoleToUser,
  removeRoleFromUser,
}
