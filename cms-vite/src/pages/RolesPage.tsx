/**
 * Roles Management Page
 * Main page for managing roles and permissions
 */

import React, { useState } from 'react';
import { Plus, Search, Shield, Key } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '@/shared/components';
import { RoleCard } from '@/features/rbac/components/RoleCard';
import { RoleForm } from '@/features/rbac/components/RoleForm';
import { useRoles, useCreateRole, useUpdateRole, useDeleteRole } from '@/features/rbac/hooks/useRoles';
import { getTotalPossiblePermissions, type Permissions } from '@/features/rbac/constants/permissions';

// ============================================================================
// Types
// ============================================================================

interface Role {
  id: number;
  name: string;
  description?: string;
  is_system_role?: boolean;
  is_active?: boolean;
  organization_id?: number;
  permissions?: Permissions;
  users_count?: number;
  created_at?: string;
  updated_at?: string;
}

interface CreateRoleRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  organization_id?: number;
  permissions: Permissions;
}

interface UpdateRoleRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  permissions?: Permissions;
}

// ============================================================================
// Component
// ============================================================================

export default function RolesPage() {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [viewingRole, setViewingRole] = useState<Role | null>(null);

  // Queries
  const { data: rolesData, isLoading: rolesLoading } = useRoles();

  // Mutations
  const createRoleMutation = useCreateRole();
  const updateRoleMutation = useUpdateRole();
  const deleteRoleMutation = useDeleteRole();

  // Filter roles
  const filteredRoles =
    rolesData?.roles?.filter(
      (role: Role) =>
        role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        role.description?.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

  // Separate system and custom roles
  const systemRoles = filteredRoles.filter((r: Role) => r.is_system_role);
  const customRoles = filteredRoles.filter((r: Role) => !r.is_system_role);

  // Handlers
  const handleCreateRole = (data: CreateRoleRequest | UpdateRoleRequest) => {
    createRoleMutation.mutate(data as CreateRoleRequest, {
      onSuccess: () => {
        setShowCreateForm(false);
      },
    });
  };

  const handleUpdateRole = (data: CreateRoleRequest | UpdateRoleRequest) => {
    if (!editingRole) return;

    updateRoleMutation.mutate(
      { id: editingRole.id, data: data as UpdateRoleRequest },
      {
        onSuccess: () => {
          setEditingRole(null);
        },
      }
    );
  };

  const handleDeleteRole = (role: Role) => {
    if (role.is_system_role) {
      alert(t('rbac.cannotDeleteSystemRole', 'Cannot delete system roles'));
      return;
    }

    if (
      confirm(
        t('rbac.confirmDeleteRole', `Are you sure you want to delete the role "${role.name}"?`)
      )
    ) {
      deleteRoleMutation.mutate(role.id);
    }
  };

  const handleViewRole = (role: Role) => {
    setViewingRole(role);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
  };

  // Loading state
  if (rolesLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 dark:text-gray-400">
          {t('common.loading', 'Loading...')}
        </div>
      </div>
    );
  }

  const totalPermissions = getTotalPossiblePermissions();

  return (
    <>
      <PageHeader
        title={t('rbac.rolesAndPermissions', 'Roles & Permissions')}
        description={t('rbac.manageRolesDescription', 'Manage user roles and their permissions')}
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
              placeholder={t('rbac.searchRoles', 'Search roles...')}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Create Button */}
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            {t('rbac.createRole', 'Create Role')}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {rolesData?.total || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {t('rbac.totalRoles', 'Total Roles')}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Shield className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {systemRoles.length}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {t('rbac.systemRoles', 'System Roles')}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {customRoles.length}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {t('rbac.customRoles', 'Custom Roles')}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <Key className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totalPermissions}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {t('rbac.possiblePermissions', 'Possible Permissions')}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Roles Section */}
        {systemRoles.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              {t('rbac.systemRoles', 'System Roles')}
              <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                ({t('rbac.protected', 'Protected')})
              </span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {systemRoles.map((role: Role) => (
                <RoleCard
                  key={role.id}
                  role={role}
                  onView={handleViewRole}
                />
              ))}
            </div>
          </div>
        )}

        {/* Custom Roles Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            {t('rbac.customRoles', 'Custom Roles')}
          </h3>

          {customRoles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {customRoles.map((role: Role) => (
                <RoleCard
                  key={role.id}
                  role={role}
                  onView={handleViewRole}
                  onEdit={handleEditRole}
                  onDelete={handleDeleteRole}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {t('rbac.noCustomRoles', 'No custom roles yet')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {t('rbac.createFirstRole', 'Create your first custom role to get started')}
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
                {t('rbac.createRole', 'Create Role')}
              </button>
            </div>
          )}
        </div>
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

      {/* View Role Modal (Read-only for system roles) */}
      {viewingRole && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <RoleForm
            role={viewingRole}
            onSubmit={() => {}}
            onCancel={() => setViewingRole(null)}
            isLoading={false}
          />
        </div>
      )}
    </>
  );
}
