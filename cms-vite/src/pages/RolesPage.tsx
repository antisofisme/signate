/**
 * Roles Management Page
 * Main page for managing roles and permissions
 */

import React, { useState } from 'react';
import { Plus, Search, Shield, Key } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  PageHeader,
  PageSkeleton,
  EmptyState,
  ConfirmDialog,
  Button,
  ModalOverlay,
  PageStats,
  PageToolbar,
} from '@/shared/components';
import { RoleCard } from '@/features/rbac/components/RoleCard';
import { RoleForm } from '@/features/rbac/components/RoleForm';
import { useRoles, useCreateRole, useUpdateRole, useDeleteRole } from '@/features/rbac/hooks/useRoles';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
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
  const [deleteItem, setDeleteItem] = useState<Role | null>(null);

  // Permission checks
  const { hasPermission: canView } = useCanPerformAction('roles', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('roles', 'create');
  const { hasPermission: canEdit } = useCanPerformAction('roles', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('roles', 'delete');

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
      return;
    }
    setDeleteItem(role);
  };

  const confirmDelete = () => {
    if (!deleteItem) return;
    deleteRoleMutation.mutate(deleteItem.id, {
      onSuccess: () => setDeleteItem(null),
    });
  };

  const handleViewRole = (role: Role) => {
    setViewingRole(role);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
  };

  // Loading state
  if (rolesLoading) {
    return <PageSkeleton showTable={false} />;
  }

  // Permission check - no view access
  if (!canView) {
    return (
      <EmptyState
        icon={Shield}
        title={t('common.noPermission', 'No Permission')}
        description={t('rbac.noViewPermission', 'You do not have permission to view roles')}
      />
    );
  }

  const totalPermissions = getTotalPossiblePermissions();

  return (
    <>
      <PageHeader
        title={t('rbac.rolesAndPermissions', 'Roles & Permissions')}
        description={t('rbac.manageRolesDescription', 'Manage user roles and their permissions')}
      />

      {/* Toolbar: Search kiri, Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t('rbac.searchRoles', 'Search roles...')}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowCreateForm(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('rbac.createRole', 'Create Role')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas content */}
      <PageStats
        total={rolesData?.total || 0}
        totalLabel="roles"
        stats={[
          { label: 'system', value: systemRoles.length, color: 'text-purple-600 dark:text-purple-400' },
          { label: 'custom', value: customRoles.length, color: 'text-green-600 dark:text-green-400' },
          { label: 'permissions', value: totalPermissions, color: 'text-amber-600 dark:text-amber-400' },
        ]}
      />

      {/* Content */}
      <div className="space-y-6">
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
                  onEdit={canEdit ? handleEditRole : undefined}
                  onDelete={canDelete ? handleDeleteRole : undefined}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Shield}
              title={t('rbac.noCustomRoles', 'No custom roles yet')}
              description={t('rbac.createFirstRole', 'Create your first custom role to get started')}
            />
          )}
        </div>
      </div>

      {/* Create Role Modal */}
      <ModalOverlay
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      >
        <div className="p-4" onClick={(e) => e.stopPropagation()}>
          <RoleForm
            onSubmit={handleCreateRole}
            onCancel={() => setShowCreateForm(false)}
            isLoading={createRoleMutation.isPending}
          />
        </div>
      </ModalOverlay>

      {/* Edit Role Modal */}
      <ModalOverlay
        isOpen={!!editingRole}
        onClose={() => setEditingRole(null)}
      >
        <div className="p-4" onClick={(e) => e.stopPropagation()}>
          {editingRole && (
            <RoleForm
              role={editingRole}
              onSubmit={handleUpdateRole}
              onCancel={() => setEditingRole(null)}
              isLoading={updateRoleMutation.isPending}
            />
          )}
        </div>
      </ModalOverlay>

      {/* View Role Modal (Read-only for system roles) */}
      <ModalOverlay
        isOpen={!!viewingRole}
        onClose={() => setViewingRole(null)}
      >
        <div className="p-4" onClick={(e) => e.stopPropagation()}>
          {viewingRole && (
            <RoleForm
              role={viewingRole}
              onSubmit={() => {}}
              onCancel={() => setViewingRole(null)}
              isLoading={false}
            />
          )}
        </div>
      </ModalOverlay>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={!!deleteItem}
        onOpenChange={(open) => !open && setDeleteItem(null)}
        title={t('rbac.deleteRole', 'Delete Role')}
        description={t(
          'rbac.confirmDeleteRole',
          `Are you sure you want to delete "${deleteItem?.name}"? This action cannot be undone.`
        )}
        variant="danger"
        confirmLabel={t('common.delete', 'Delete')}
        onConfirm={confirmDelete}
        isLoading={deleteRoleMutation.isPending}
      />
    </>
  );
}
