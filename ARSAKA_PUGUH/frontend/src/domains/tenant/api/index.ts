/**
 * Tenant Domain - API Hooks (TanStack Query)
 * Includes queries and mutations for tenant management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Tenant, PaginatedResponse } from '@/shared/types'
import type {
  TenantFilters,
  TenantMember,
  IsolationCheckResult,
  CreateTenantRequest,
  UpdateTenantRequest,
  InviteMemberRequest,
  AcceptInvitationRequest,
  UpdateMemberRoleRequest,
  TenantInvitation,
} from '../types'

// Query Keys
export const tenantKeys = {
  all: ['tenants'] as const,
  lists: () => [...tenantKeys.all, 'list'] as const,
  list: (filters: TenantFilters) => [...tenantKeys.lists(), filters] as const,
  details: () => [...tenantKeys.all, 'detail'] as const,
  detail: (id: string) => [...tenantKeys.details(), id] as const,
  members: (id: string) => [...tenantKeys.all, 'members', id] as const,
  invitations: (id: string) => [...tenantKeys.all, 'invitations', id] as const,
  isolation: () => [...tenantKeys.all, 'isolation'] as const,
}

// ============================================
// Tenant Queries
// ============================================

export function useGetTenants(filters?: TenantFilters) {
  return useQuery({
    queryKey: tenantKeys.list(filters || {}),
    queryFn: () => api.get<PaginatedResponse<Tenant>>('/tenants', { params: filters }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useGetTenant(id: string) {
  return useQuery({
    queryKey: tenantKeys.detail(id),
    queryFn: () => api.get<Tenant>(`/tenants/${id}`),
    enabled: !!id,
  })
}

export function useGetTenantMembers(tenantId: string) {
  return useQuery({
    queryKey: tenantKeys.members(tenantId),
    queryFn: () => api.get<TenantMember[]>(`/tenants/${tenantId}/members`),
    enabled: !!tenantId,
  })
}

export function useGetTenantInvitations(tenantId: string) {
  return useQuery({
    queryKey: tenantKeys.invitations(tenantId),
    queryFn: () => api.get<TenantInvitation[]>(`/tenants/${tenantId}/invitations`),
    enabled: !!tenantId,
  })
}

export function useGetIsolationCheck() {
  return useQuery({
    queryKey: tenantKeys.isolation(),
    queryFn: () => api.get<IsolationCheckResult>('/tenants/isolation-check'),
    staleTime: 60 * 1000, // 1 minute
  })
}

// ============================================
// Tenant Mutations
// ============================================

export function useCreateTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateTenantRequest) =>
      api.post<Tenant>('/tenants', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

export function useUpdateTenant(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateTenantRequest) =>
      api.patch<Tenant>(`/tenants/${tenantId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.detail(tenantId) })
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

export function useDeleteTenant(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => api.delete(`/tenants/${tenantId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

// ============================================
// Member Management Mutations
// ============================================

export function useInviteMember(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InviteMemberRequest) =>
      api.post<TenantInvitation>(`/tenants/${tenantId}/invitations`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.invitations(tenantId) })
    },
  })
}

export function useAcceptInvitation() {
  return useMutation({
    mutationFn: (data: AcceptInvitationRequest) =>
      api.post<{ tenantId: string }>('/tenants/invitations/accept', data),
  })
}

export function useUpdateMemberRole(tenantId: string, userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateMemberRoleRequest) =>
      api.patch<TenantMember>(`/tenants/${tenantId}/members/${userId}/role`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
    },
  })
}

export function useRemoveMember(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) =>
      api.delete(`/tenants/${tenantId}/members/${userId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
    },
  })
}

export function useCancelInvitation(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (invitationId: string) =>
      api.delete(`/tenants/${tenantId}/invitations/${invitationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.invitations(tenantId) })
    },
  })
}
