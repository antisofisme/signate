/**
 * Workflow Domain - API Hooks (TanStack Query)
 * Following ARSAKA_PANDAWA standards
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Workflow, PaginatedResponse } from '@/shared/types'
import type { WorkflowFilters, WorkflowStats } from '../types'

// Query Keys
export const workflowKeys = {
  all: ['workflows'] as const,
  lists: () => [...workflowKeys.all, 'list'] as const,
  list: (filters: WorkflowFilters) => [...workflowKeys.lists(), filters] as const,
  details: () => [...workflowKeys.all, 'detail'] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  pending: () => [...workflowKeys.all, 'pending'] as const,
  stats: () => [...workflowKeys.all, 'stats'] as const,
}

// ============================================
// Queries
// ============================================

/**
 * Get paginated list of workflows
 */
export function useGetWorkflows(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: workflowKeys.list(filters || {}),
    queryFn: () => api.get<PaginatedResponse<Workflow>>('/workflows', { params: filters }),
    select: (response) => response.data,
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Get pending workflows for current user
 */
export function useGetPendingWorkflows() {
  return useQuery({
    queryKey: workflowKeys.pending(),
    queryFn: () => api.get<Workflow[]>('/workflows/pending'),
    select: (response) => response.data,
    staleTime: 30 * 1000,
  })
}

/**
 * Get single workflow by ID
 */
export function useGetWorkflow(id: string) {
  return useQuery({
    queryKey: workflowKeys.detail(id),
    queryFn: () => api.get<Workflow>(`/workflows/${id}`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

/**
 * Get workflow statistics
 */
export function useGetWorkflowStats() {
  return useQuery({
    queryKey: workflowKeys.stats(),
    queryFn: () => api.get<WorkflowStats>('/workflows/stats'),
    select: (response) => response.data,
    staleTime: 60 * 1000, // 1 minute
  })
}

// ============================================
// Mutations
// ============================================

/**
 * Generate a unique idempotency key for mutations
 */
function generateIdempotencyKey(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
}

/**
 * Approve a workflow
 */
export function useApproveWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { workflowId: string; comment?: string; idempotencyKey?: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/approve`, {
        comment: data.comment,
        idempotency_key: data.idempotencyKey || generateIdempotencyKey(),
      }),
    onSuccess: (_, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: workflowKeys.pending() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(variables.workflowId) })
    },
  })
}

/**
 * Reject a workflow
 */
export function useRejectWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { workflowId: string; reason: string; idempotencyKey?: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/reject`, {
        reason: data.reason,
        idempotency_key: data.idempotencyKey || generateIdempotencyKey(),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.pending() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(variables.workflowId) })
    },
  })
}

/**
 * Escalate a workflow
 */
export function useEscalateWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { workflowId: string; escalateToUserId: string; reason: string; idempotencyKey?: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/escalate`, {
        escalate_to_user_id: data.escalateToUserId,
        reason: data.reason,
        idempotency_key: data.idempotencyKey || generateIdempotencyKey(),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.pending() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(variables.workflowId) })
    },
  })
}

/**
 * Delegate a workflow to another user
 */
export function useDelegateWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { workflowId: string; delegateToUserId: string; reason: string; idempotencyKey?: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/delegate`, {
        delegate_to_user_id: data.delegateToUserId,
        reason: data.reason,
        idempotency_key: data.idempotencyKey || generateIdempotencyKey(),
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.pending() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(variables.workflowId) })
    },
  })
}
