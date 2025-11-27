/**
 * usePermissions Hook
 * React Query hooks for permission management and checking
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getApiErrorMessage } from '@/shared/utils/types'
import { useAuthStore } from '@/lib/stores/authStore'
import * as rbacApi from '../api/rbacApi'
import type {
  Permission,
  PermissionResource,
  PermissionAction,
  HasPermissionRequest,
} from '../types/rbac.types'

// ============================================================================
// Query Keys
// ============================================================================

export const permissionKeys = {
  all: ['permissions'] as const,
  lists: () => [...permissionKeys.all, 'list'] as const,
  list: () => [...permissionKeys.lists()] as const,
  byResource: (resource: string) => [...permissionKeys.all, 'resource', resource] as const,
  userPermissions: (userId: number) => ['users', userId, 'permissions'] as const,
  userRoles: (userId: number) => ['users', userId, 'roles'] as const,
}

// ============================================================================
// Permissions Queries
// ============================================================================

/**
 * Get all permissions
 */
export function usePermissions() {
  return useQuery({
    queryKey: permissionKeys.list(),
    queryFn: () => rbacApi.getPermissions(),
    staleTime: 30 * 60 * 1000, // 30 minutes (permissions rarely change)
  })
}

/**
 * Get permissions by resource
 */
export function usePermissionsByResource(resource: string) {
  return useQuery({
    queryKey: permissionKeys.byResource(resource),
    queryFn: () => rbacApi.getPermissionsByResource(resource),
    staleTime: 30 * 60 * 1000,
  })
}

/**
 * Get user permissions
 */
export function useUserPermissions(userId: number | undefined) {
  return useQuery({
    queryKey: permissionKeys.userPermissions(userId!),
    queryFn: () => rbacApi.getUserPermissions(userId!),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Get user roles
 */
export function useUserRoles(userId: number | undefined) {
  return useQuery({
    queryKey: permissionKeys.userRoles(userId!),
    queryFn: () => rbacApi.getUserRoles(userId!),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  })
}

// ============================================================================
// Permission Checking Hook
// ============================================================================

/**
 * Check if user has specific permission
 * @param userId - User ID to check
 * @param resource - Resource to check
 * @param action - Action to check
 * @returns Object with hasPermission boolean and helper functions
 */
export function useHasPermission(
  userId: number | undefined,
  resource: PermissionResource,
  action: PermissionAction
) {
  const { data: permissions, isLoading } = useUserPermissions(userId)

  const hasPermission = permissions?.some(
    (p) => p.resource === resource && (p.action === action || p.action === 'manage')
  ) ?? false

  return {
    hasPermission,
    isLoading,
    permissions,
  }
}

/**
 * Check multiple permissions at once
 * @param userId - User ID to check
 * @param checks - Array of permission checks
 * @returns Object with results for each check
 */
export function useHasPermissions(
  userId: number | undefined,
  checks: Array<{ resource: PermissionResource; action: PermissionAction }>
) {
  const { data: permissions, isLoading } = useUserPermissions(userId)

  const results = checks.map(({ resource, action }) => ({
    resource,
    action,
    hasPermission:
      permissions?.some(
        (p) => p.resource === resource && (p.action === action || p.action === 'manage')
      ) ?? false,
  }))

  const hasAllPermissions = results.every((r) => r.hasPermission)
  const hasAnyPermission = results.some((r) => r.hasPermission)

  return {
    results,
    hasAllPermissions,
    hasAnyPermission,
    isLoading,
    permissions,
  }
}

/**
 * Check if user can perform action on resource
 * Helper hook for common permission checks
 */
export function useCanPerformAction(
  resource: PermissionResource,
  action: PermissionAction,
  userId?: number
) {
  // Get current user ID from auth store if not provided
  const authUser = useAuthStore((state) => state.user)
  const currentUserId = userId ?? authUser?.id

  // Return safe defaults if no user ID available
  if (currentUserId === undefined) {
    return {
      hasPermission: false,
      isLoading: false,
      permissions: undefined,
    }
  }

  return useHasPermission(currentUserId, resource, action)
}

// ============================================================================
// User Role Mutations
// ============================================================================

/**
 * Assign role to user mutation
 */
export function useAssignRoleToUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) =>
      rbacApi.assignRoleToUser(userId, roleId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.userRoles(variables.userId) })
      queryClient.invalidateQueries({
        queryKey: permissionKeys.userPermissions(variables.userId),
      })
      toast.success('Role assigned to user')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to assign role'))
    },
  })
}

/**
 * Remove role from user mutation
 */
export function useRemoveRoleFromUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) =>
      rbacApi.removeRoleFromUser(userId, roleId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.userRoles(variables.userId) })
      queryClient.invalidateQueries({
        queryKey: permissionKeys.userPermissions(variables.userId),
      })
      toast.success('Role removed from user')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to remove role'))
    },
  })
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get current user ID from auth store
 * Safe helper function that doesn't rely on JWT decoding
 * @deprecated Use useAuthStore directly in hooks instead
 */
function getCurrentUserId(): number | undefined {
  try {
    // Use auth store state directly (safer than JWT decoding)
    const authState = useAuthStore.getState()
    if (authState.user?.id) {
      return authState.user.id
    }

    // Fallback: Try to parse from localStorage (with proper validation)
    const authStorage = localStorage.getItem('auth-storage')
    if (!authStorage) return undefined

    const parsed = JSON.parse(authStorage)
    const userId = parsed?.state?.user?.id

    // Validate userId is a positive number
    if (typeof userId === 'number' && userId > 0) {
      return userId
    }

    return undefined
  } catch (error) {
    console.error('Failed to get user ID:', error)
    return undefined
  }
}

/**
 * Group permissions by resource
 */
export function groupPermissionsByResource(permissions: Permission[]) {
  return permissions.reduce((acc, permission) => {
    if (!acc[permission.resource]) {
      acc[permission.resource] = []
    }
    acc[permission.resource].push(permission)
    return acc
  }, {} as Record<string, Permission[]>)
}
