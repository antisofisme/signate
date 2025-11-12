/**
 * Roles Management Page
 * Main page for managing roles and permissions
 */

import React, { useState } from 'react'
import { Plus, Search, Shield } from 'lucide-react'
import { PageHeader } from '@/shared/components'
import { RoleCard } from '@/features/rbac/components/RoleCard'
import { RoleForm } from '@/features/rbac/components/RoleForm'
import { PermissionMatrix } from '@/features/rbac/components/PermissionMatrix'
import {
  useRoles,
  useCreateRole,
  useUpdateRole,
  useDeleteRole,
  useAddPermissionsToRole,
  useRemovePermissionsFromRole,
} from '@/features/rbac/hooks/useRoles'
import {
  usePermissions,
} from '@/features/rbac/hooks/usePermissions'
import type { Role, CreateRoleRequest, UpdateRoleRequest } from '@/features/rbac/types/rbac.types'

export default function RolesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [managingPermissions, setManagingPermissions] = useState<Role | null>(null)

  // Queries
  const { data: rolesData, isLoading: rolesLoading } = useRoles()
  const { data: allPermissions = [] } = usePermissions()

  // Mutations
  const createRoleMutation = useCreateRole()
  const updateRoleMutation = useUpdateRole()
  const deleteRoleMutation = useDeleteRole()
  const addPermissionsMutation = useAddPermissionsToRole()
  const removePermissionsMutation = useRemovePermissionsFromRole()

  // Filter roles
  const filteredRoles = rolesData?.roles?.filter((role) =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  // Handlers
  const handleCreateRole = (data: CreateRoleRequest) => {
    createRoleMutation.mutate(data, {
      onSuccess: () => {
        setShowCreateForm(false)
      },
    })
  }

  const handleUpdateRole = (data: UpdateRoleRequest) => {
    if (!editingRole) return

    updateRoleMutation.mutate(
      { id: editingRole.id, data },
      {
        onSuccess: () => {
          setEditingRole(null)
        },
      }
    )
  }

  const handleDeleteRole = (role: Role) => {
    if (role.is_system) {
      alert('Cannot delete system roles')
      return
    }

    if (confirm(`Are you sure you want to delete the role "${role.name}"?`)) {
      deleteRoleMutation.mutate(role.id)
    }
  }

  const handleViewDetails = (role: Role) => {
    setManagingPermissions(role)
  }

  const handlePermissionToggle = (permissionId: number) => {
    if (!managingPermissions) return

    const currentPermissions = managingPermissions.permissions?.map((p) => p.id) || []
    const isSelected = currentPermissions.includes(permissionId)

    if (isSelected) {
      // Remove permission
      removePermissionsMutation.mutate({
        roleId: managingPermissions.id,
        data: { permission_ids: [permissionId] },
      })
    } else {
      // Add permission
      addPermissionsMutation.mutate({
        roleId: managingPermissions.id,
        data: { permission_ids: [permissionId] },
      })
    }
  }

  // Loading state
  if (rolesLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 dark:text-gray-400">Loading roles...</div>
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Roles & Permissions"
        description="Manage user roles and their permissions"
        icon={Shield}
      />

      <div className="space-y-6">
        {/* Search and Actions */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search roles..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Create Button */}
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create Role
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {rolesData?.total || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Roles</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {rolesData?.roles?.filter((r) => r.is_system).length || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">System Roles</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {allPermissions.length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Permissions</div>
          </div>
        </div>

        {/* Roles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRoles.map((role) => (
            <RoleCard
              key={role.id}
              role={role}
              onEdit={setEditingRole}
              onDelete={handleDeleteRole}
              onViewDetails={handleViewDetails}
            />
          ))}
        </div>

        {/* Empty State */}
        {filteredRoles.length === 0 && (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No roles found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {searchTerm ? 'Try adjusting your search' : 'Create your first role to get started'}
            </p>
            {!searchTerm && (
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Role
              </button>
            )}
          </div>
        )}
      </div>

      {/* Create Role Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <RoleForm
            onSubmit={handleCreateRole}
            onCancel={() => setShowCreateForm(false)}
            isLoading={createRoleMutation.isPending}
          />
        </div>
      )}

      {/* Edit Role Modal */}
      {editingRole && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <RoleForm
            role={editingRole}
            onSubmit={handleUpdateRole}
            onCancel={() => setEditingRole(null)}
            isLoading={updateRoleMutation.isPending}
          />
        </div>
      )}

      {/* Permission Management Modal */}
      {managingPermissions && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Manage Permissions: {managingPermissions.name}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Select permissions to grant to this role
                </p>
              </div>
              <button
                onClick={() => setManagingPermissions(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>

            {/* Permission Matrix */}
            <div className="flex-1 overflow-y-auto p-6">
              <PermissionMatrix
                permissions={allPermissions}
                selectedPermissions={managingPermissions.permissions?.map((p) => p.id) || []}
                onPermissionToggle={handlePermissionToggle}
                readOnly={managingPermissions.is_system}
              />
              {managingPermissions.is_system && (
                <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    System roles are read-only and cannot be modified
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
