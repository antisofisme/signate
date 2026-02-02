/**
 * Project Members Page
 *
 * Manage project members: list, add, update role, remove.
 */

import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  useProjectBySlug,
  useProjectMembers,
  useAddProjectMember,
  useUpdateMemberRole,
  useRemoveProjectMember,
} from '../hooks'
import { useAuthStore } from '@/stores/authStore'
import type { ProjectRole, AddMemberRequest } from '../types'

const ROLE_OPTIONS: { value: ProjectRole; label: string; description: string }[] = [
  { value: 'admin', label: 'Admin', description: 'Full access to project settings and members' },
  { value: 'member', label: 'Member', description: 'Can view and edit project resources' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to project' },
]

const ROLE_COLORS: Record<ProjectRole, string> = {
  admin: 'bg-purple-100 text-purple-800 border-purple-200',
  member: 'bg-blue-100 text-blue-800 border-blue-200',
  viewer: 'bg-gray-100 text-gray-800 border-gray-200',
}

interface MemberWithUserInfo {
  user_id: string
  project_id: string
  role: ProjectRole
  created_at: string | null
  updated_at: string | null
  // Extended user info (if available)
  email?: string
  name?: string
}

export function ProjectMembersPage() {
  const { tenantSlug, projectSlug } = useParams<{ tenantSlug: string; projectSlug: string }>()

  // Get tenant ID from auth context
  const activeTenantId = useAuthStore((state) => state.activeTenantId)
  const tenantId = activeTenantId || ''

  // Project data
  const { data: project, isLoading: projectLoading, error: projectError } = useProjectBySlug(
    tenantId,
    projectSlug || ''
  )
  const projectId = project?.project_id || ''

  // Members data
  const { data: membersData, isLoading: membersLoading } = useProjectMembers(tenantId, projectId)
  const members = (membersData?.members || []) as MemberWithUserInfo[]

  // Mutations
  const addMember = useAddProjectMember(tenantId, projectId)
  const updateRole = useUpdateMemberRole(tenantId, projectId)
  const removeMember = useRemoveProjectMember(tenantId, projectId)

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [newMember, setNewMember] = useState<AddMemberRequest>({
    user_id: '',
    role: 'member',
  })

  // Remove confirmation state
  const [removeConfirm, setRemoveConfirm] = useState<string | null>(null)

  // Role edit state
  const [editingRole, setEditingRole] = useState<string | null>(null)

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMember.user_id.trim()) {
      alert('Please enter a user ID')
      return
    }

    try {
      await addMember.mutateAsync(newMember)
      setShowAddModal(false)
      setNewMember({ user_id: '', role: 'member' })
    } catch (err) {
      alert(`Failed to add member: ${err}`)
    }
  }

  const handleUpdateRole = async (userId: string, newRole: ProjectRole) => {
    try {
      await updateRole.mutateAsync({ userId, data: { role: newRole } })
      setEditingRole(null)
    } catch (err) {
      alert(`Failed to update role: ${err}`)
    }
  }

  const handleRemoveMember = async (userId: string) => {
    try {
      await removeMember.mutateAsync(userId)
      setRemoveConfirm(null)
    } catch (err) {
      alert(`Failed to remove member: ${err}`)
    }
  }

  // Loading state
  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Error state
  if (projectError || !project) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load project
      </div>
    )
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Link
              to={`/app/${tenantSlug}/${projectSlug}/settings`}
              className="hover:text-blue-600"
            >
              {project.name}
            </Link>
            <span>/</span>
            <span>Members</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Project Members</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage who has access to this project and their roles.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
            />
          </svg>
          Add Member
        </button>
      </div>

      {/* Members Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Members ({members.length})
          </h2>
        </div>

        {membersLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : members.length === 0 ? (
          <div className="p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No members yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Add members to collaborate on this project.
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Member
            </button>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Added
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {members.map((member) => (
                <tr key={member.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {(member.name || member.email || member.user_id).charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {member.name || `User ${member.user_id.slice(0, 8)}...`}
                        </div>
                        {member.email && (
                          <div className="text-sm text-gray-500">{member.email}</div>
                        )}
                        {!member.email && (
                          <div className="text-xs text-gray-400 font-mono">
                            {member.user_id}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingRole === member.user_id ? (
                      <select
                        value={member.role}
                        onChange={(e) => handleUpdateRole(member.user_id, e.target.value as ProjectRole)}
                        onBlur={() => setEditingRole(null)}
                        className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoFocus
                      >
                        {ROLE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <button
                        onClick={() => setEditingRole(member.user_id)}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded border ${ROLE_COLORS[member.role]} hover:opacity-80`}
                        title="Click to change role"
                      >
                        {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {member.created_at
                      ? new Date(member.created_at).toLocaleDateString()
                      : 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    {removeConfirm === member.user_id ? (
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-gray-500 text-xs">Remove?</span>
                        <button
                          onClick={() => handleRemoveMember(member.user_id)}
                          className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                          disabled={removeMember.isPending}
                        >
                          {removeMember.isPending ? '...' : 'Yes'}
                        </button>
                        <button
                          onClick={() => setRemoveConfirm(null)}
                          className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setRemoveConfirm(member.user_id)}
                        className="text-red-600 hover:text-red-800"
                        title="Remove member"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Role Descriptions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Role Permissions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {ROLE_OPTIONS.map((role) => (
            <div key={role.value} className="flex items-start gap-3">
              <span className={`px-2 py-1 text-xs font-medium rounded border ${ROLE_COLORS[role.value]}`}>
                {role.label}
              </span>
              <p className="text-sm text-gray-600">{role.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Back to Settings Link */}
      <div className="pt-4">
        <Link
          to={`/app/${tenantSlug}/${projectSlug}/settings`}
          className="text-sm text-blue-600 hover:underline flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Project Settings
        </Link>
      </div>

      {/* Add Member Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-black/50"
              onClick={() => setShowAddModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Add Project Member
              </h2>
              <form onSubmit={handleAddMember} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    User ID
                  </label>
                  <input
                    type="text"
                    value={newMember.user_id}
                    onChange={(e) => setNewMember({ ...newMember, user_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter user ID (UUID)"
                    required
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Enter the UUID of the user you want to add.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={newMember.role}
                    onChange={(e) => setNewMember({ ...newMember, role: e.target.value as ProjectRole })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {ROLE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label} - {opt.description}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={addMember.isPending || !newMember.user_id.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {addMember.isPending ? 'Adding...' : 'Add Member'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
