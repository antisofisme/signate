/**
 * Project Feature Types
 */

export interface Project {
  project_id: string
  tenant_id: string
  name: string
  slug: string
  description: string | null
  environment: ProjectEnvironment
  settings: Record<string, unknown>
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export type ProjectEnvironment = 'production' | 'staging' | 'development' | 'testing'

export interface ProjectMember {
  project_id: string
  user_id: string
  role: ProjectRole
  created_at: string | null
  updated_at: string | null
}

export type ProjectRole = 'admin' | 'member' | 'viewer'

export interface ProjectListResponse {
  projects: Project[]
  total: number
  limit: number
  offset: number
}

export interface ProjectMemberListResponse {
  members: ProjectMember[]
  total: number
}

export interface CreateProjectRequest {
  name: string
  description?: string
  environment?: ProjectEnvironment
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  environment?: ProjectEnvironment
  settings?: Record<string, unknown>
  is_active?: boolean
}

export interface AddMemberRequest {
  user_id: string
  role?: ProjectRole
}

export interface UpdateMemberRoleRequest {
  role: ProjectRole
}

export interface SuccessResponse {
  success: boolean
  message: string
  data?: Record<string, unknown>
}
