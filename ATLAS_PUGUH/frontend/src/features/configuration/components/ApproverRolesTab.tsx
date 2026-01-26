/**
 * Approver Roles Tab - Configuration Menu
 * CRUD for customer-defined approver roles (used in approval workflow rules)
 */

import { useState } from 'react'
import {
  useApproverRoles,
  useCreateApproverRole,
  useDeleteApproverRole
} from '../hooks/useConfig'
import type { ApproverRoleCreate } from '../types/Config'

export function ApproverRolesTab() {
  const { data, isLoading, error } = useApproverRoles(false) // Show all including inactive
  const createMutation = useCreateApproverRole()
  const deleteMutation = useDeleteApproverRole()

  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<ApproverRoleCreate>({
    role_code: '',
    role_name: '',
    description: '',
    is_active: true,
    display_order: 0
  })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createMutation.mutateAsync(formData)
      setIsCreating(false)
      setFormData({ role_code: '', role_name: '', description: '', is_active: true, display_order: 0 })
    } catch (err) {
      console.error('Create failed:', err)
    }
  }

  const handleDelete = async (roleId: string) => {
    if (!confirm('Delete this approver role? Approval rules using it may need to be updated.')) {
      return
    }
    try {
      await deleteMutation.mutateAsync(roleId)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><div className="text-gray-500">Loading...</div></div>
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4">
        <div className="text-red-800 font-semibold">Error loading approver roles</div>
        <div className="text-red-600 text-sm mt-1">{error instanceof Error ? error.message : 'Unknown error'}</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Approver Roles</h2>
          <p className="text-sm text-gray-600 mt-1">
            Customer-defined roles used in approval workflow rules
          </p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded font-semibold hover:bg-blue-700"
        >
          + Add Approver Role
        </button>
      </div>

      {/* Create Form */}
      {isCreating && (
        <div className="bg-gray-50 border rounded p-4">
          <h3 className="font-semibold mb-3">New Approver Role</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Role Code (uppercase, snake_case)</label>
                <input
                  type="text"
                  value={formData.role_code}
                  onChange={(e) => setFormData({ ...formData, role_code: e.target.value.toUpperCase() })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="CFO"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Role Name</label>
                <input
                  type="text"
                  value={formData.role_name}
                  onChange={(e) => setFormData({ ...formData, role_name: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="Chief Financial Officer"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded px-3 py-2"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Display Order</label>
                <input
                  type="number"
                  value={formData.display_order}
                  onChange={(e) => setFormData({ ...formData, display_order: parseInt(e.target.value) })}
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">Active</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded font-semibold hover:bg-green-700 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded font-semibold hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white border rounded overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Description</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Order</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.approver_roles.map((role) => (
              <tr key={role.approver_role_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{role.role_code}</td>
                <td className="px-4 py-3 text-sm font-semibold">{role.role_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{role.description || '-'}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{role.display_order}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${role.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {role.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <button
                    onClick={() => handleDelete(role.approver_role_id)}
                    className="text-red-600 hover:text-red-800 font-medium"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {data?.approver_roles.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg font-semibold mb-2">No approver roles</div>
            <p className="text-sm">Add your first approver role to get started.</p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
        <strong>Approver Roles:</strong> Define custom roles used in approval workflow rules.
        These roles determine who can approve requests at different workflow stages.
      </div>
    </div>
  )
}
