/**
 * Users Page
 *
 * LAYER 1: PRESENTATION
 * Manage users with CRUD operations
 * Uses shared components and RHF-based forms
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Pencil, Trash2, Key, Shield } from 'lucide-react';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useChangePassword,
} from '@/features/users/hooks/useUsers';
import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { PageHeader, AccessDenied, PageSkeleton, ConfirmDialog, Button } from '@/shared/components';
import { UserForm } from '@/features/users/components/UserForm';
import { ChangePasswordModal } from '@/features/users/components/ChangePasswordModal';
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  UserListFilters,
} from '@/features/users/types/user';
import type { UserRole } from '@/lib/auth/permissions';

export default function UsersPage() {
  const { t } = useTranslation();

  // Check permissions
  const { hasPermission, isLoading: isCheckingPermission } = useCanPerformAction(
    'users',
    'read'
  );

  // Show loading state while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Show access denied if no permission
  if (!hasPermission) {
    return <AccessDenied />;
  }

  return <UsersPageContent />;
}

function UsersPageContent() {
  const { t } = useTranslation();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [changingPassword, setChangingPassword] = useState<User | null>(null);
  const [filters, setFilters] = useState<UserListFilters>({});

  // Queries
  const { data, isLoading } = useUsers(filters);
  const { data: orgsData } = useOrganizations(true); // Active only

  // Mutations
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();
  const changePasswordMutation = useChangePassword();

  const handleCreate = (data: CreateUserRequest) => {
    createMutation.mutate(data, {
      onSuccess: () => setShowCreateModal(false),
    });
  };

  const handleUpdate = (data: UpdateUserRequest) => {
    if (!editingUser) return;
    updateMutation.mutate(
      { id: editingUser.id, data },
      {
        onSuccess: () => setEditingUser(null),
      }
    );
  };

  const handleDelete = () => {
    if (!deletingUser) return;
    deleteMutation.mutate(deletingUser.id, {
      onSuccess: () => setDeletingUser(null),
    });
  };

  const handleChangePassword = (newPassword: string) => {
    if (!changingPassword) return;
    changePasswordMutation.mutate(
      { id: changingPassword.id, data: { new_password: newPassword } },
      {
        onSuccess: () => setChangingPassword(null),
      }
    );
  };

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case 'super_admin':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'admin':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'manager':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'viewer':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatRoleLabel = (role: UserRole) => {
    switch (role) {
      case 'super_admin':
        return 'Super Admin';
      case 'admin':
        return 'Admin';
      case 'manager':
        return 'Manager';
      case 'viewer':
        return 'Viewer';
      default:
        return role;
    }
  };

  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title="Users"
        description="Manage user accounts and permissions"
      />

      {/* Content */}
      <div className="space-y-6">
        {/* Action Bar */}
        <div className="flex items-center justify-end">
          <Button
            onClick={() => setShowCreateModal(true)}
            leftIcon={<Plus className="w-5 h-5" />}
          >
            Create User
          </Button>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Organization
              </label>
              <select
                value={filters.organization_id || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    organization_id: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">All Organizations</option>
                {orgsData?.organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Role
              </label>
              <select
                value={filters.role || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    role: (e.target.value as UserRole) || undefined,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">All Roles</option>
                <option value="super_admin">Super Admin</option>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.active_only || false}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      active_only: e.target.checked,
                    })
                  }
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Active users only
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Stats */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Total Users
              </h3>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {data.total}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Active
              </h3>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">
                {data.active}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Inactive
              </h3>
              <p className="text-3xl font-bold text-gray-600 dark:text-gray-400 mt-2">
                {data.total - data.active}
              </p>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
            </div>
          ) : data && data.users.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Organization
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data.users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {user.full_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            @{user.username}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 dark:text-gray-300">
                          {user.email}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 dark:text-gray-300">
                          {user.organization_name || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full flex items-center gap-1 w-fit ${getRoleBadgeColor(
                            user.role
                          )}`}
                        >
                          <Shield className="w-3 h-3" />
                          {formatRoleLabel(user.role)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {user.is_active ? (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setChangingPassword(user)}
                            className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900 rounded-lg transition-colors"
                            title="Change Password"
                          >
                            <Key className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingUser(user)}
                            className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeletingUser(user)}
                            className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                No users found. Create your first user!
              </p>
            </div>
          )}
        </div>

        {/* Create User Modal */}
        <UserForm
          isOpen={showCreateModal}
          organizations={orgsData?.organizations || []}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />

        {/* Edit User Modal */}
        {editingUser && (
          <UserForm
            isOpen={!!editingUser}
            user={editingUser}
            organizations={orgsData?.organizations || []}
            onClose={() => setEditingUser(null)}
            onSubmit={handleUpdate}
            isLoading={updateMutation.isPending}
          />
        )}

        {/* Change Password Modal */}
        {changingPassword && (
          <ChangePasswordModal
            isOpen={!!changingPassword}
            user={changingPassword}
            onClose={() => setChangingPassword(null)}
            onSubmit={handleChangePassword}
            isLoading={changePasswordMutation.isPending}
          />
        )}

        {/* Delete Confirmation */}
        <ConfirmDialog
          open={!!deletingUser}
          onOpenChange={(open) => !open && setDeletingUser(null)}
          title="Delete User"
          description={
            deletingUser
              ? `Are you sure you want to delete "${deletingUser.full_name}" (@${deletingUser.username})? This action cannot be undone.`
              : ''
          }
          confirmLabel="Delete"
          variant="danger"
          onConfirm={handleDelete}
          isLoading={deleteMutation.isPending}
        />
      </div>
    </>
  );
}
