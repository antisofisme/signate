/**
 * IAM Domain - API Hooks (TanStack Query)
 * READ-ONLY domain - no mutations
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { User, PaginatedResponse } from '@/shared/types'
import type { UserFilters, UserStats, Role, Permission, ServiceAccount } from '../types'

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
