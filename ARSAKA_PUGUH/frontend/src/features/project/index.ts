/**
 * Project Feature Module
 *
 * Exports all project-related functionality.
 */

// Types
export type {
  Project,
  ProjectEnvironment,
  ProjectMember,
  ProjectRole,
  ProjectListResponse,
  ProjectMemberListResponse,
  CreateProjectRequest,
  UpdateProjectRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
  SuccessResponse,
} from './types'

// API
export { projectApi } from './api'

// Hooks
export {
  projectKeys,
  useProjects,
  useProject,
  useProjectBySlug,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  useProjectMembers,
  useAddProjectMember,
  useUpdateMemberRole,
  useRemoveProjectMember,
} from './hooks'

// Components
export { ProjectSelector } from './components/ProjectSelector'

// Pages
export { ProjectListPage } from './pages/ProjectList'
export { ProjectSettingsPage } from './pages/ProjectSettings'
export { ProjectMembersPage } from './pages/ProjectMembers'
