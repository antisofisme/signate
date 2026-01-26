/**
 * Tenant Domain - API Hooks (TanStack Query)
 * READ-ONLY domain - no mutations
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Tenant, PaginatedResponse } from '@/shared/types'
import type { TenantFilters, TenantMember, IsolationCheckResult } from '../types'

// Query Keys
export const tenantKeys = {
  all: ['tenants'] as const,
  lists: () => [...tenantKeys.all, 'list'] as const,
  list: (filters: TenantFilters) => [...tenantKeys.lists(), filters] as const,
  details: () => [...tenantKeys.all, 'detail'] as const,
  detail: (id: string) => [...tenantKeys.details(), id] as const,
  members: (id: string) => [...tenantKeys.all, 'members', id] as const,
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

export function useGetIsolationCheck() {
  return useQuery({
    queryKey: tenantKeys.isolation(),
    queryFn: () => api.get<IsolationCheckResult>('/tenants/isolation-check'),
    staleTime: 60 * 1000, // 1 minute
  })
}
