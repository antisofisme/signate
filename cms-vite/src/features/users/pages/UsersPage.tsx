/**
 * Users Page
 *
 * Main page for user management - orchestration only
 * Following CMS UI Development skill standards
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Shield, Users } from 'lucide-react';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useChangePassword } from '../hooks/useUsers';
import { useOrganizations } from '@/shared/hooks/useSharedOrganizations';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { UserList } from '../components/UserList';
import { UserForm } from '../components/UserForm';
import { ChangePasswordDialog } from '../components/ChangePasswordDialog';
import {
  Button,
  StatsCard,
  ConfirmDialog,
  EmptyState,
  PageSkeleton,
  AccessDenied,
} from '@/shared/components';
import type { User, CreateUserRequest, UpdateUserRequest, ChangePasswordRequest } from '../types/user';

export default function UsersPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingView } = useCanPerformAction('users', 'view');
  const { hasPermission: canCreate } = useCanPerformAction('users', 'create');
  const { hasPermission: canEdit } = useCanPerformAction('users', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('users', 'delete');

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
        action={
          canCreate && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              {t('users.actions.createUser') || 'Add User'}
            </Button>
          )
        }
      />
    );
  }

  return (
    <>
      {/* Stats */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <StatsCard
          label={t('users.stats.totalUsers') || 'Total Users'}
          value={totalUsers}
          icon={Users}
          iconColor="blue"
        />
        <StatsCard
          label={t('users.stats.active') || 'Active Users'}
          value={activeUsers}
          icon={Shield}
          iconColor="green"
        />
      </div>

      {/* Actions */}
      {canCreate && (
        <div className="mb-6 flex justify-end">
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-5 h-5 mr-2" />
            {t('users.actions.createUser') || 'Add User'}
          </Button>
        </div>
      )}

      {/* User List */}
      <UserList
        users={users}
        onEdit={canEdit ? setEditingUser : undefined}
        onDelete={canDelete ? setDeletingUser : undefined}
        onChangePassword={canEdit ? setChangingPasswordUser : undefined}
      />

      {/* Modals */}
      {showCreateModal && (
        <UserForm
          organizations={organizations}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      )}

      {editingUser && (
        <UserForm
          user={editingUser}
          organizations={organizations}
          onClose={() => setEditingUser(null)}
          onSubmit={handleUpdate}
          isLoading={updateMutation.isPending}
        />
      )}

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

      {changingPasswordUser && (
        <ChangePasswordDialog
          user={changingPasswordUser}
          open={!!changingPasswordUser}
          onOpenChange={(open) => !open && setChangingPasswordUser(null)}
          onSubmit={handleChangePassword}
          isLoading={changePasswordMutation.isPending}
        />
      )}
    </>
  );
}
