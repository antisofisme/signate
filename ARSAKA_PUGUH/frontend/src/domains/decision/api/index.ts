/**
 * Decision Domain - API Hooks (TanStack Query)
 * 4 MUTATIONS: Create Rule Draft, Request Activation, Update Rule, Delete Rule
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { Rule, Decision, PaginatedResponse } from '@/shared/types'
import type { RuleFilters, CreateRuleDraftRequest, ActivationRequest, UpdateRuleRequest, DecisionFilters } from '../types'

// Query Keys
export const decisionKeys = {
  all: ['decision'] as const,
  rules: () => [...decisionKeys.all, 'rules'] as const,
  ruleList: (filters: RuleFilters) => [...decisionKeys.rules(), 'list', filters] as const,
  ruleDetail: (id: string) => [...decisionKeys.rules(), 'detail', id] as const,
  ruleVersions: (id: string) => [...decisionKeys.rules(), 'versions', id] as const,
  types: () => [...decisionKeys.all, 'types'] as const,
  history: (filters: DecisionFilters) => [...decisionKeys.all, 'history', filters] as const,
  decisionDetail: (id: string) => [...decisionKeys.all, 'detail', id] as const,
}

// ============================================
// Rule Queries
// ============================================

export function useGetRules(filters?: RuleFilters) {
  return useQuery({
    queryKey: decisionKeys.ruleList(filters || {}),
    queryFn: () => api.get<PaginatedResponse<Rule>>('/decision/rules', { params: filters }),
    select: (response) => response.data,
    staleTime: 30 * 1000,
  })
}

export function useGetRule(id: string) {
  return useQuery({
    queryKey: decisionKeys.ruleDetail(id),
    queryFn: () => api.get<Rule>(`/decision/rules/${id}`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

export function useGetRuleVersions(id: string) {
  return useQuery({
    queryKey: decisionKeys.ruleVersions(id),
    queryFn: () => api.get<Rule[]>(`/decision/rules/${id}/versions`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

export function useGetDecisionTypes() {
  return useQuery({
    queryKey: decisionKeys.types(),
    queryFn: () => api.get<string[]>('/decision/types'),
    select: (response) => response.data,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// ============================================
// Decision History Queries
// ============================================

export function useGetDecisionHistory(filters?: DecisionFilters) {
  return useQuery({
    queryKey: decisionKeys.history(filters || {}),
    queryFn: () => api.get<PaginatedResponse<Decision>>('/decision/history', { params: filters }),
    select: (response) => response.data,
    staleTime: 60 * 1000,
  })
}

export function useGetDecision(id: string) {
  return useQuery({
    queryKey: decisionKeys.decisionDetail(id),
    queryFn: () => api.get<Decision>(`/decision/history/${id}`),
    select: (response) => response.data,
    enabled: !!id,
  })
}

// ============================================
// Mutations (4 total)
// ============================================

/**
 * MUTATION 1: Create Rule Draft
 * Creates a new rule in DRAFT status
 */
export function useCreateRuleDraft() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateRuleDraftRequest) => api.post<Rule>('/decision/rules', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: decisionKeys.rules() })
    },
  })
}

/**
 * MUTATION 2: Request Activation
 * Requests activation of a rule, creates approval workflow
 */
export function useRequestActivation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ActivationRequest) =>
      api.post<Rule>(`/decision/rules/${data.ruleId}/activate`, {
        version: data.version,
        reason: data.reason,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: decisionKeys.ruleDetail(variables.ruleId) })
      queryClient.invalidateQueries({ queryKey: decisionKeys.rules() })
    },
  })
}

/**
 * MUTATION 3: Update Rule
 * Updates a rule in DRAFT status only
 */
export function useUpdateRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: string; data: UpdateRuleRequest }) =>
      api.put<Rule>(`/decision/rules/${ruleId}`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: decisionKeys.ruleDetail(variables.ruleId) })
      queryClient.invalidateQueries({ queryKey: decisionKeys.rules() })
    },
  })
}

/**
 * MUTATION 4: Delete Rule
 * Soft deletes a rule
 */
export function useDeleteRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ruleId: string) => api.delete<void>(`/decision/rules/${ruleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: decisionKeys.rules() })
    },
  })
}
