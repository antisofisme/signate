/**
 * Project Settings Page
 *
 * Manage project configuration, members, and danger zone (delete).
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  useProjectBySlug,
  useUpdateProject,
  useDeleteProject,
  useProjectMembers,
  useRemoveProjectMember,
} from '../hooks'
import type { ProjectEnvironment, UpdateProjectRequest } from '../types'

const ENVIRONMENT_OPTIONS: { value: ProjectEnvironment; label: string }[] = [
  { value: 'development', label: 'Development' },
  { value: 'testing', label: 'Testing' },
  { value: 'staging', label: 'Staging' },
  { value: 'production', label: 'Production' },
]

export function ProjectSettingsPage() {
  const { tenantSlug, projectSlug } = useParams<{ tenantSlug: string; projectSlug: string }>()
  const navigate = useNavigate()

  // Get tenant ID from context (simplified)
  const tenantId = '550e8400-e29b-41d4-a716-446655440000' // TODO: Get from auth context

  const { data: project, isLoading, error } = useProjectBySlug(tenantId, projectSlug || '')
  const updateProject = useUpdateProject(tenantId, project?.project_id || '')
  const deleteProject = useDeleteProject(tenantId)
  const { data: membersData } = useProjectMembers(tenantId, project?.project_id || '')
  const removeMember = useRemoveProjectMember(tenantId, project?.project_id || '')

  const [formData, setFormData] = useState<UpdateProjectRequest>({})
  const [deleteConfirm, setDeleteConfirm] = useState('')

  // Initialize form when project loads
  if (project && !formData.name) {
    setFormData({
      name: project.name,
      description: project.description || '',
      environment: project.environment,
      is_active: project.is_active,
    })
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await updateProject.mutateAsync(formData)
      alert('Project updated successfully')
    } catch (err) {
      alert(`Failed to update project: ${err}`)
    }
  }

  const handleDelete = async () => {
    if (!project) return
    if (deleteConfirm !== project.name) {
      alert('Please type the project name to confirm deletion')
      return
    }

    try {
      await deleteProject.mutateAsync(project.project_id)
      navigate(`/app/${tenantSlug}/projects`)
    } catch (err) {
      alert(`Failed to delete project: ${err}`)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load project
      </div>
    )
  }

  return (
    <div className="max-w-3xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Project Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage settings for <strong>{project.name}</strong>
        </p>
      </div>

      {/* General Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">General</h2>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name
            </label>
            <input
              type="text"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Environment
            </label>
            <select
              value={formData.environment || 'development'}
              onChange={(e) =>
                setFormData({ ...formData, environment: e.target.value as ProjectEnvironment })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ENVIRONMENT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active ?? true}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
              Project is active
            </label>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={updateProject.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {updateProject.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>

      {/* Project Info */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Info</h2>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Project ID</dt>
            <dd className="font-mono text-gray-900">{project.project_id}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Slug</dt>
            <dd className="font-mono text-gray-900">{project.slug}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd className="text-gray-900">
              {project.created_at
                ? new Date(project.created_at).toLocaleDateString()
                : 'Unknown'}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Last Updated</dt>
            <dd className="text-gray-900">
              {project.updated_at
                ? new Date(project.updated_at).toLocaleDateString()
                : 'Never'}
            </dd>
          </div>
        </dl>
      </div>

      {/* Members */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Members ({membersData?.total || 0})
        </h2>
        {membersData?.members && membersData.members.length > 0 ? (
          <div className="space-y-3">
            {membersData.members.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                    U
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      User {member.user_id.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-gray-500 capitalize">{member.role}</div>
                  </div>
                </div>
                <button
                  onClick={() => removeMember.mutate(member.user_id)}
                  className="text-sm text-red-600 hover:text-red-800"
                  disabled={removeMember.isPending}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No explicit members. All tenant members have access.</p>
        )}
      </div>

      {/* Danger Zone */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-2">Danger Zone</h2>
        <p className="text-sm text-red-700 mb-4">
          Once you delete a project, there is no going back. Please be certain.
        </p>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-red-700 mb-1">
              Type <strong>{project.name}</strong> to confirm:
            </label>
            <input
              type="text"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              className="w-full px-3 py-2 border border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              placeholder={project.name}
            />
          </div>
          <button
            onClick={handleDelete}
            disabled={deleteConfirm !== project.name || deleteProject.isPending}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {deleteProject.isPending ? 'Deleting...' : 'Delete Project'}
          </button>
        </div>
      </div>
    </div>
  )
}
