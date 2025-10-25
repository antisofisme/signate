import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersAPI } from '../../services/api'
import { Plus, Edit2, Trash2, Shield, Mail, Calendar } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button } from '../shared'

/**
 * UsersTab Component
 * User management interface for Settings page
 *
 * Features:
 * - List all users with roles and status
 * - Create new users
 * - Edit user details and roles
 * - Delete users
 * - Password reset
 * - Last login tracking
 */
export default function UsersTab() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)

  // Fetch users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersAPI.list().then(res => res.data),
  })

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: usersAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['users'])
      showToast.success('User deleted successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete user')
    }
  })

  const handleDelete = (id, username) => {
    if (confirm(`Delete user "${username}"?\n\nThis action cannot be undone.`)) {
      deleteMutation.mutate(id)
    }
  }

  const getRoleBadge = (role) => {
    const styles = {
      admin: 'bg-purple-100 text-purple-700',
      editor: 'bg-blue-100 text-blue-700',
      viewer: 'bg-gray-100 text-gray-700'
    }
    return styles[role] || styles.viewer
  }

  return (
    <div>
      {/* Header Actions */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">User Management</h3>
          <p className="text-sm text-gray-600">Manage users, roles, and permissions</p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Add User
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Users Table */}
      {!isLoading && usersData?.items && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {usersData.items.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  {/* User Info */}
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <span className="font-semibold text-blue-600">
                          {user.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{user.username}</p>
                        {user.full_name && (
                          <p className="text-sm text-gray-500">{user.full_name}</p>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Role */}
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getRoleBadge(user.role)}`}>
                      <Shield className="w-3 h-3" />
                      {user.role}
                    </span>
                  </td>

                  {/* Email */}
                  <td className="px-6 py-4">
                    {user.email ? (
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Mail className="w-4 h-4" />
                        {user.email}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>

                  {/* Last Login */}
                  <td className="px-6 py-4">
                    {user.last_login ? (
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {new Date(user.last_login).toLocaleDateString()}
                      </div>
                    ) : (
                      <span className="text-gray-400">Never</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setSelectedUser(user)
                          setShowEditModal(true)
                        }}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(user.id, user.username)}
                        disabled={user.role === 'admin' && usersData.items.filter(u => u.role === 'admin').length === 1}
                        title={user.role === 'admin' ? 'Cannot delete last admin' : 'Delete user'}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!usersData?.items || usersData.items.length === 0) && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No users found</p>
          <p className="text-sm text-gray-500 mb-4">Add your first user to get started</p>
          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setShowCreateModal(true)}
          >
            Add First User
          </Button>
        </div>
      )}

      {/* Modals - To be created */}
      {/* {showCreateModal && <UserFormModal onClose={() => setShowCreateModal(false)} />} */}
      {/* {showEditModal && <UserFormModal user={selectedUser} onClose={() => setShowEditModal(false)} />} */}
    </div>
  )
}
