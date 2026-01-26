/**
 * Project Feature React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectApi } from '../api'
import type {
  CreateProjectRequest,
  UpdateProjectRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
} from '../types'

// Query keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (tenantId: string) => [...projectKeys.lists(), tenantId] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (tenantId: string, projectId: string) =>
    [...projectKeys.details(), tenantId, projectId] as const,
  detailBySlug: (tenantId: string, slug: string) =>
    [...projectKeys.details(), tenantId, 'slug', slug] as const,
  members: (tenantId: string, projectId: string) =>
    [...projectKeys.all, 'members', tenantId, projectId] as const,
}

// List projects
export function useProjects(tenantId: string, limit = 100, offset = 0) {
  return useQuery({
    queryKey: projectKeys.list(tenantId),
    queryFn: () => projectApi.list(tenantId, limit, offset),
    enabled: !!tenantId,
    staleTime: 1000 * 60, // 1 minute
  })
}

// Get single project
export function useProject(tenantId: string, projectId: string) {
  return useQuery({
    queryKey: projectKeys.detail(tenantId, projectId),
    queryFn: () => projectApi.get(tenantId, projectId),
    enabled: !!tenantId && !!projectId,
    staleTime: 1000 * 60, // 1 minute
  })
}

// Get project by slug
export function useProjectBySlug(tenantId: string, slug: string) {
  return useQuery({
    queryKey: projectKeys.detailBySlug(tenantId, slug),
    queryFn: () => projectApi.getBySlug(tenantId, slug),
    enabled: !!tenantId && !!slug,
    staleTime: 1000 * 60, // 1 minute
  })
}

// Create project
export function useCreateProject(tenantId: string, userId?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProjectRequest) => projectApi.create(tenantId, data, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.list(tenantId) })
    },
  })
}

// Update project
export function useUpdateProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateProjectRequest) => projectApi.update(tenantId, projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(tenantId, projectId) })
      queryClient.invalidateQueries({ queryKey: projectKeys.list(tenantId) })
    },
  })
}

// Delete project
export function useDeleteProject(tenantId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (projectId: string) => projectApi.delete(tenantId, projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.list(tenantId) })
    },
  })
}

// List project members
export function useProjectMembers(tenantId: string, projectId: string) {
  return useQuery({
    queryKey: projectKeys.members(tenantId, projectId),
    queryFn: () => projectApi.listMembers(tenantId, projectId),
    enabled: !!tenantId && !!projectId,
    staleTime: 1000 * 60, // 1 minute
  })
}

// Add project member
export function useAddProjectMember(tenantId: string, projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: AddMemberRequest) => projectApi.addMember(tenantId, projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.members(tenantId, projectId) })
    },
  })
}

// Update member role
export function useUpdateMemberRole(tenantId: string, projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UpdateMemberRoleRequest }) =>
      projectApi.updateMemberRole(tenantId, projectId, userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.members(tenantId, projectId) })
    },
  })
}

// Remove project member
export function useRemoveProjectMember(tenantId: string, projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => projectApi.removeMember(tenantId, projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.members(tenantId, projectId) })
    },
  })
}
