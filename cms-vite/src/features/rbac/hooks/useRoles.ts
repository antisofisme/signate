/**
 * useRoles Hook
 * React Query hooks for role management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getApiErrorMessage } from '@/shared/utils/types'
import * as rbacApi from '../api/rbacApi'
import type {
  Role,
  RoleFilters,
  CreateRoleRequest,
  UpdateRoleRequest,
  AssignPermissionsRequest,
  RemovePermissionsRequest,
} from '../types/rbac.types'

// ============================================================================
// Query Keys
// ============================================================================

export const roleKeys = {
  all: ['roles'] as const,
  lists: () => [...roleKeys.all, 'list'] as const,
  list: (filters?: RoleFilters) => [...roleKeys.lists(), filters] as const,
  details: () => [...roleKeys.all, 'detail'] as const,
  detail: (id: number) => [...roleKeys.details(), id] as const,
  permissions: (id: number) => [...roleKeys.detail(id), 'permissions'] as const,
  users: (id: number) => [...roleKeys.detail(id), 'users'] as const,
  system: () => [...roleKeys.all, 'system'] as const,
}

// ============================================================================
// Roles Queries
// ============================================================================

/**
 * Get list of roles
 */
export function useRoles(filters?: RoleFilters) {
  return useQuery({
    queryKey: roleKeys.list(filters),
    queryFn: () => rbacApi.getRoles(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Get single role by ID
 */
export function useRole(id: number | undefined) {
  return useQuery({
    queryKey: roleKeys.detail(id!),
    queryFn: () => rbacApi.getRole(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get role with permissions
 */
export function useRoleWithPermissions(id: number | undefined) {
  return useQuery({
    queryKey: roleKeys.permissions(id!),
    queryFn: () => rbacApi.getRoleWithPermissions(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get system roles
 */
export function useSystemRoles() {
  return useQuery({
    queryKey: roleKeys.system(),
    queryFn: () => rbacApi.getSystemRoles(),
    staleTime: 30 * 60 * 1000, // 30 minutes (system roles rarely change)
  })
}

/**
 * Get role permissions
 */
export function useRolePermissions(roleId: number | undefined) {
  return useQuery({
    queryKey: roleKeys.permissions(roleId!),
    queryFn: () => rbacApi.getRolePermissions(roleId!),
    enabled: !!roleId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get role users
 */
export function useRoleUsers(roleId: number | undefined) {
  return useQuery({
    queryKey: roleKeys.users(roleId!),
    queryFn: () => rbacApi.getRoleUsers(roleId!),
    enabled: !!roleId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// ============================================================================
// Roles Mutations
// ============================================================================

/**
 * Create role mutation
 */
export function useCreateRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateRoleRequest) => rbacApi.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() })
      toast.success('Role created successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create role'))
    },
  })
}

/**
 * Update role mutation
 */
export function useUpdateRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRoleRequest }) =>
      rbacApi.updateRole(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() })
      queryClient.invalidateQueries({ queryKey: roleKeys.detail(variables.id) })
      toast.success('Role updated successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update role'))
    },
  })
}

/**
 * Delete role mutation
 */
export function useDeleteRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => rbacApi.deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() })
      toast.success('Role deleted successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete role'))
    },
  })
}

// ============================================================================
// Role Permissions Mutations
// ============================================================================

/**
 * Add permissions to role mutation
 */
export function useAddPermissionsToRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ roleId, data }: { roleId: number; data: AssignPermissionsRequest }) =>
      rbacApi.addPermissionsToRole(roleId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: roleKeys.permissions(variables.roleId) })
      queryClient.invalidateQueries({ queryKey: roleKeys.detail(variables.roleId) })
      toast.success('Permissions added to role')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to add permissions'))
    },
  })
}

/**
 * Remove permissions from role mutation
 */
export function useRemovePermissionsFromRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ roleId, data }: { roleId: number; data: RemovePermissionsRequest }) =>
      rbacApi.removePermissionsFromRole(roleId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: roleKeys.permissions(variables.roleId) })
      queryClient.invalidateQueries({ queryKey: roleKeys.detail(variables.roleId) })
      toast.success('Permissions removed from role')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to remove permissions'))
    },
  })
}
