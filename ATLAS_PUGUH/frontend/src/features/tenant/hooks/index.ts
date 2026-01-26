/**
 * Tenant Feature Hooks
 *
 * React Query hooks for tenant management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as tenantApi from '../api'
import type {
  CreateTenantRequest,
  UpdateTenantRequest,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  AcceptInvitationRequest,
  MemberRole,
} from '../types'

// ============================================
// Query Keys
// ============================================

export const tenantKeys = {
  all: ['tenants'] as const,
  lists: () => [...tenantKeys.all, 'list'] as const,
  list: (includeInactive: boolean) => [...tenantKeys.lists(), { includeInactive }] as const,
  details: () => [...tenantKeys.all, 'detail'] as const,
  detail: (id: string) => [...tenantKeys.details(), id] as const,
  members: (tenantId: string) => [...tenantKeys.all, 'members', tenantId] as const,
  invitations: (tenantId: string) => [...tenantKeys.all, 'invitations', tenantId] as const,
}

// ============================================
// Tenant Queries
// ============================================

/**
 * Hook to list user's tenants
 */
export function useTenants(includeInactive = false) {
  return useQuery({
    queryKey: tenantKeys.list(includeInactive),
    queryFn: () => tenantApi.listTenants(includeInactive),
  })
}

/**
 * Hook to get tenant details
 */
export function useTenant(tenantId: string) {
  return useQuery({
    queryKey: tenantKeys.detail(tenantId),
    queryFn: () => tenantApi.getTenant(tenantId),
    enabled: !!tenantId,
  })
}

/**
 * Hook to list tenant members
 */
export function useTenantMembers(tenantId: string, includeInvitations = true) {
  return useQuery({
    queryKey: tenantKeys.members(tenantId),
    queryFn: () => tenantApi.listMembers(tenantId, includeInvitations),
    enabled: !!tenantId,
  })
}

/**
 * Hook to list tenant invitations
 */
export function useTenantInvitations(tenantId: string, status?: string) {
  return useQuery({
    queryKey: tenantKeys.invitations(tenantId),
    queryFn: () => tenantApi.listInvitations(tenantId, status),
    enabled: !!tenantId,
  })
}

// ============================================
// Tenant Mutations
// ============================================

/**
 * Hook to create a tenant
 */
export function useCreateTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateTenantRequest) => tenantApi.createTenant(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

/**
 * Hook to update a tenant
 */
export function useUpdateTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ tenantId, data }: { tenantId: string; data: UpdateTenantRequest }) =>
      tenantApi.updateTenant(tenantId, data),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.detail(tenantId) })
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

/**
 * Hook to delete a tenant
 */
export function useDeleteTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (tenantId: string) => tenantApi.deleteTenant(tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

// ============================================
// Member Mutations
// ============================================

/**
 * Hook to update member role
 */
export function useUpdateMemberRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      tenantId,
      memberUserId,
      role,
    }: {
      tenantId: string
      memberUserId: string
      role: MemberRole
    }) => tenantApi.updateMemberRole(tenantId, memberUserId, { role }),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
    },
  })
}

/**
 * Hook to remove a member
 */
export function useRemoveMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      tenantId,
      memberUserId,
      reason,
    }: {
      tenantId: string
      memberUserId: string
      reason?: string
    }) => tenantApi.removeMember(tenantId, memberUserId, reason),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
    },
  })
}

/**
 * Hook to leave a tenant
 */
export function useLeaveTenant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (tenantId: string) => tenantApi.leaveTenant(tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

// ============================================
// Invitation Mutations
// ============================================

/**
 * Hook to invite a member
 */
export function useInviteMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ tenantId, data }: { tenantId: string; data: InviteMemberRequest }) =>
      tenantApi.inviteMember(tenantId, data),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
      queryClient.invalidateQueries({ queryKey: tenantKeys.invitations(tenantId) })
    },
  })
}

/**
 * Hook to accept an invitation
 */
export function useAcceptInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (token: string) => tenantApi.acceptInvitation({ token }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() })
    },
  })
}

/**
 * Hook to cancel an invitation
 */
export function useCancelInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ tenantId, invitationId }: { tenantId: string; invitationId: string }) =>
      tenantApi.cancelInvitation(tenantId, invitationId),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.members(tenantId) })
      queryClient.invalidateQueries({ queryKey: tenantKeys.invitations(tenantId) })
    },
  })
}
