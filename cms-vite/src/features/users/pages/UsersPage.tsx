/**
 * Users Page
 *
 * Main page for user management - orchestration only
 * Following CMS UI Development skill standards
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Users } from 'lucide-react';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useChangePassword } from '../hooks/useUsers';
import { useOrganizations } from '@/shared/hooks/useSharedOrganizations';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { UserList } from '../components/UserList';
import { UserForm } from '../components/UserForm';
import { ChangePasswordDialog } from '../components/ChangePasswordDialog';
import { RoleAssignmentModal } from '../components/RoleAssignmentModal';
import {
  Button,
  ConfirmDialog,
  EmptyState,
  PageSkeleton,
  AccessDenied,
  PageHeader,
  PageStats,
  PageToolbar,
} from '@/shared/components';
import type { User, CreateUserRequest, UpdateUserRequest, ChangePasswordRequest } from '../types/user';

export default function UsersPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingView } = useCanPerformAction('users', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('users', 'create');
  const { hasPermission: canEdit } = useCanPerformAction('users', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('users', 'delete');
  const { hasPermission: canManageRoles } = useCanPerformAction('roles', 'edit');

  // Data fetching
  const { data: usersData, isLoading: isLoadingUsers } = useUsers();
  const { data: organizationsData } = useOrganizations();
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();
  const changePasswordMutation = useChangePassword();

  // State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [changingPasswordUser, setChangingPasswordUser] = useState<User | null>(null);
  const [assigningRoleUser, setAssigningRoleUser] = useState<User | null>(null);

  const users = usersData?.users || [];
  const organizations = organizationsData?.organizations || [];
  const totalUsers = usersData?.total || 0;
  const activeUsers = users.filter(u => u.is_active).length;

  // Handlers
  const handleCreate = (data: CreateUserRequest) => {
    createMutation.mutate(data, { onSuccess: () => setShowCreateModal(false) });
  };

  const handleUpdate = (data: UpdateUserRequest) => {
    if (!editingUser) return;
    updateMutation.mutate({ id: editingUser.id, data }, { onSuccess: () => setEditingUser(null) });
  };

  const handleDelete = () => {
    if (!deletingUser) return;
    deleteMutation.mutate(deletingUser.id, { onSuccess: () => setDeletingUser(null) });
  };

  const handleChangePassword = (data: ChangePasswordRequest) => {
    if (!changingPasswordUser) return;
    changePasswordMutation.mutate(
      { id: changingPasswordUser.id, data },
      { onSuccess: () => setChangingPasswordUser(null) }
    );
  };

  // Permission loading state
  if (isCheckingView) {
    return <PageSkeleton />;
  }

  // Access denied
  if (!canView) {
    return <AccessDenied />;
  }

  // Loading state
  if (isLoadingUsers) {
    return <PageSkeleton />;
  }

  // Empty state
  if (users.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title={t('users.empty.title') || 'No users found'}
        description={t('users.empty.description') || 'Get started by adding your first user'}
      />
    );
  }

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('users.title', 'Users')}
        description={t('users.subtitle', 'Manage users and their permissions')}
      />

      {/* Toolbar: Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('users.actions.createUser') || 'Add User'}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas list */}
      <PageStats
        total={totalUsers}
        totalLabel="users"
        stats={[
          { label: 'active', value: activeUsers, color: 'text-green-600 dark:text-green-400' },
          { label: 'inactive', value: totalUsers - activeUsers, color: 'text-gray-500' },
        ]}
      />

      {/* User List */}
      <UserList
        users={users}
        onEdit={canEdit ? setEditingUser : undefined}
        onDelete={canDelete ? setDeletingUser : undefined}
        onChangePassword={canEdit ? setChangingPasswordUser : undefined}
        onAssignRole={canManageRoles ? setAssigningRoleUser : undefined}
      />

      {/* Modals */}
      <UserForm
        isOpen={showCreateModal}
        organizations={organizations}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
      />

      <UserForm
        isOpen={!!editingUser}
        user={editingUser ?? undefined}
        organizations={organizations}
        onClose={() => setEditingUser(null)}
        onSubmit={handleUpdate}
        isLoading={updateMutation.isPending}
      />

      <ConfirmDialog
        open={!!deletingUser}
        onOpenChange={(open) => !open && setDeletingUser(null)}
        title={t('users.delete.title') || 'Delete User'}
        description={
          deletingUser
            ? `${t('users.delete.message') || 'Are you sure you want to delete'} "${deletingUser.username}"? ${t('users.delete.warning') || 'This action cannot be undone.'}`
            : ''
        }
        variant="danger"
        confirmLabel={t('users.actions.delete') || 'Delete'}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />

      <ChangePasswordDialog
        isOpen={!!changingPasswordUser}
        user={changingPasswordUser}
        onClose={() => setChangingPasswordUser(null)}
        onSubmit={handleChangePassword}
        isLoading={changePasswordMutation.isPending}
      />

      <RoleAssignmentModal
        isOpen={!!assigningRoleUser}
        user={assigningRoleUser}
        onClose={() => setAssigningRoleUser(null)}
      />
    </>
  );
}
