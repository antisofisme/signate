/**
 * Configuration Hooks
 * React Query hooks for Configuration master data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getFunctionalAreas,
  createFunctionalArea,
  updateFunctionalArea,
  deleteFunctionalArea,
  getDecisionTypes,
  createDecisionType,
  updateDecisionType,
  deleteDecisionType,
  getApproverRoles,
  createApproverRole,
  updateApproverRole,
  deleteApproverRole
} from '../api/config'
import type {
  FunctionalAreaCreate,
  FunctionalAreaUpdate,
  DecisionTypeCreate,
  DecisionTypeUpdate,
  ApproverRoleCreate,
  ApproverRoleUpdate
} from '../types/Config'

// ============================================================================
// FUNCTIONAL AREAS
// ============================================================================

export function useFunctionalAreas(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['functional-areas', activeOnly],
    queryFn: () => getFunctionalAreas(activeOnly),
    staleTime: 30000,
  })
}

export function useCreateFunctionalArea() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: FunctionalAreaCreate) => createFunctionalArea(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['functional-areas'] })
    },
  })
}

export function useUpdateFunctionalArea() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ areaId, data }: { areaId: string; data: FunctionalAreaUpdate }) =>
      updateFunctionalArea(areaId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['functional-areas'] })
    },
  })
}

export function useDeleteFunctionalArea() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (areaId: string) => deleteFunctionalArea(areaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['functional-areas'] })
    },
  })
}

// ============================================================================
// DECISION TYPES
// ============================================================================

export function useDecisionTypes(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['decision-types', activeOnly],
    queryFn: () => getDecisionTypes(activeOnly),
    staleTime: 30000,
  })
}

export function useCreateDecisionType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: DecisionTypeCreate) => createDecisionType(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decision-types'] })
    },
  })
}

export function useUpdateDecisionType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ typeId, data }: { typeId: string; data: DecisionTypeUpdate }) =>
      updateDecisionType(typeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decision-types'] })
    },
  })
}

export function useDeleteDecisionType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (typeId: string) => deleteDecisionType(typeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decision-types'] })
    },
  })
}

// ============================================================================
// APPROVER ROLES
// ============================================================================

export function useApproverRoles(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['approver-roles', activeOnly],
    queryFn: () => getApproverRoles(activeOnly),
    staleTime: 30000,
  })
}

export function useCreateApproverRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ApproverRoleCreate) => createApproverRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approver-roles'] })
    },
  })
}

export function useUpdateApproverRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ roleId, data }: { roleId: string; data: ApproverRoleUpdate }) =>
      updateApproverRole(roleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approver-roles'] })
    },
  })
}

export function useDeleteApproverRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (roleId: string) => deleteApproverRole(roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approver-roles'] })
    },
  })
}
