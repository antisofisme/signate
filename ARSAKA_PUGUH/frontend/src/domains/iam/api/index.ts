/**
 * IAM Domain - API Hooks (TanStack Query)
 * Includes queries and mutations for role management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { User, PaginatedResponse } from '@/shared/types'
import type {
  UserFilters,
  UserStats,
  Role,
  Permission,
  ServiceAccount,
  CreateRoleRequest,
  UpdateRoleRequest,
  AssignRoleRequest,
} from '../types'

// Query Keys
export const iamKeys = {
  all: ['iam'] as const,
  users: () => [...iamKeys.all, 'users'] as const,
  userList: (filters: UserFilters) => [...iamKeys.users(), 'list', filters] as const,
  userDetail: (id: string) => [...iamKeys.users(), 'detail', id] as const,
  userStats: () => [...iamKeys.users(), 'stats'] as const,
  roles: () => [...iamKeys.all, 'roles'] as const,
  roleList: () => [...iamKeys.roles(), 'list'] as const,
  roleDetail: (id: string) => [...iamKeys.roles(), 'detail', id] as const,
  permissions: () => [...iamKeys.all, 'permissions'] as const,
  serviceAccounts: () => [...iamKeys.all, 'service-accounts'] as const,
}

// ============================================
// User Queries
// ============================================

export function useGetUsers(filters?: UserFilters) {
  return useQuery({
    queryKey: iamKeys.userList(filters || {}),
    queryFn: () => api.get<PaginatedResponse<User>>('/iam/users', { params: filters }),
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useGetUser(id: string) {
  return useQuery({
    queryKey: iamKeys.userDetail(id),
    queryFn: () => api.get<User>(`/iam/users/${id}`),
    enabled: !!id,
  })
}

export function useGetUserStats() {
  return useQuery({
    queryKey: iamKeys.userStats(),
    queryFn: () => api.get<UserStats>('/iam/users/stats'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// ============================================
// Role Queries
// ============================================

export function useGetRoles() {
  return useQuery({
    queryKey: iamKeys.roleList(),
    queryFn: () => api.get<Role[]>('/iam/roles'),
    staleTime: 5 * 60 * 1000,
  })
}

export function useGetRole(id: string) {
  return useQuery({
    queryKey: iamKeys.roleDetail(id),
    queryFn: () => api.get<Role>(`/iam/roles/${id}`),
    enabled: !!id,
  })
}

// ============================================
// Permission Queries
// ============================================

export function useGetPermissions() {
  return useQuery({
    queryKey: iamKeys.permissions(),
    queryFn: () => api.get<Permission[]>('/iam/permissions'),
    staleTime: 10 * 60 * 1000, // 10 minutes - rarely changes
  })
}

// ============================================
// Service Account Queries
// ============================================

export function useGetServiceAccounts() {
  return useQuery({
    queryKey: iamKeys.serviceAccounts(),
    queryFn: () => api.get<ServiceAccount[]>('/iam/service-accounts'),
    staleTime: 5 * 60 * 1000,
  })
}

// ============================================
// Role Mutations
// ============================================

export function useCreateRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateRoleRequest) =>
      api.post<Role>('/iam/roles', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roleList() })
    },
  })
}

export function useUpdateRole(roleId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateRoleRequest) =>
      api.put<Role>(`/iam/roles/${roleId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roleDetail(roleId) })
      queryClient.invalidateQueries({ queryKey: iamKeys.roleList() })
    },
  })
}

export function useDeleteRole(roleId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => api.delete(`/iam/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roleList() })
    },
  })
}

// ============================================
// User Role Assignment Mutations
// ============================================

export function useAssignRoleToUser(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: AssignRoleRequest) =>
      api.post(`/iam/users/${userId}/roles`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.userDetail(userId) })
      queryClient.invalidateQueries({ queryKey: iamKeys.users() })
      queryClient.invalidateQueries({ queryKey: iamKeys.roleList() })
    },
  })
}

export function useRevokeRoleFromUser(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (roleId: string) =>
      api.delete(`/iam/users/${userId}/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.userDetail(userId) })
      queryClient.invalidateQueries({ queryKey: iamKeys.users() })
      queryClient.invalidateQueries({ queryKey: iamKeys.roleList() })
    },
  })
}
