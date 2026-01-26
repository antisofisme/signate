/**
 * Workflow Domain - API Hooks (TanStack Query)
 * Following ATLAS_PANDAWA standards
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
 * Approve a workflow
 */
export function useApproveWorkflow() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { workflowId: string; comment?: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/approve`, { comment: data.comment }),
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
    mutationFn: (data: { workflowId: string; reason: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/reject`, { reason: data.reason }),
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
    mutationFn: (data: { workflowId: string; reason: string }) =>
      api.post<Workflow>(`/workflows/${data.workflowId}/escalate`, { reason: data.reason }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.pending() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.stats() })
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(variables.workflowId) })
    },
  })
}
