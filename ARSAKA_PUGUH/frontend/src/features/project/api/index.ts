/**
 * Project API Client
 */

import type {
  Project,
  ProjectListResponse,
  ProjectMemberListResponse,
  CreateProjectRequest,
  UpdateProjectRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
  ProjectMember,
  SuccessResponse,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(error.detail?.message || error.message || 'Request failed')
  }

  return response.json()
}

export const projectApi = {
  // Project CRUD
  list: async (tenantId: string, limit = 100, offset = 0): Promise<ProjectListResponse> => {
    return fetchApi<ProjectListResponse>(
      `/projects?tenant_id=${tenantId}&limit=${limit}&offset=${offset}`
    )
  },

  get: async (tenantId: string, projectId: string): Promise<Project> => {
    return fetchApi<Project>(`/projects/${projectId}?tenant_id=${tenantId}`)
  },

  getBySlug: async (tenantId: string, slug: string): Promise<Project> => {
    return fetchApi<Project>(`/projects/by-slug/${slug}?tenant_id=${tenantId}`)
  },

  create: async (tenantId: string, data: CreateProjectRequest, userId?: string): Promise<Project> => {
    const params = new URLSearchParams({ tenant_id: tenantId })
    if (userId) params.append('user_id', userId)

    return fetchApi<Project>(`/projects?${params}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update: async (tenantId: string, projectId: string, data: UpdateProjectRequest): Promise<Project> => {
    return fetchApi<Project>(`/projects/${projectId}?tenant_id=${tenantId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  delete: async (tenantId: string, projectId: string): Promise<SuccessResponse> => {
    return fetchApi<SuccessResponse>(`/projects/${projectId}?tenant_id=${tenantId}`, {
      method: 'DELETE',
    })
  },

  // Project Members
  listMembers: async (tenantId: string, projectId: string): Promise<ProjectMemberListResponse> => {
    return fetchApi<ProjectMemberListResponse>(
      `/projects/${projectId}/members?tenant_id=${tenantId}`
    )
  },

  addMember: async (
    tenantId: string,
    projectId: string,
    data: AddMemberRequest
  ): Promise<ProjectMember> => {
    return fetchApi<ProjectMember>(`/projects/${projectId}/members?tenant_id=${tenantId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  updateMemberRole: async (
    tenantId: string,
    projectId: string,
    userId: string,
    data: UpdateMemberRoleRequest
  ): Promise<ProjectMember> => {
    return fetchApi<ProjectMember>(
      `/projects/${projectId}/members/${userId}?tenant_id=${tenantId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      }
    )
  },

  removeMember: async (
    tenantId: string,
    projectId: string,
    userId: string
  ): Promise<SuccessResponse> => {
    return fetchApi<SuccessResponse>(
      `/projects/${projectId}/members/${userId}?tenant_id=${tenantId}`,
      {
        method: 'DELETE',
      }
    )
  },
}
