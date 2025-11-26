/**
 * Users Page
 *
 * Main page for user management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Shield, Loader2, Key } from 'lucide-react';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useChangePassword } from '../hooks/useUsers';
import { useOrganizations } from '@/shared/hooks/useSharedOrganizations';
import { UserList } from '../components/UserList';
import { UserForm } from '../components/UserForm';
import { DeleteConfirmModal } from '@/shared/components/DeleteConfirmModal';
import type { User, CreateUserRequest, UpdateUserRequest, ChangePasswordRequest } from '../types/user';

export default function UsersPage() {
  const { t } = useTranslation();
  const { data: usersData, isLoading } = useUsers();
  const { data: organizationsData } = useOrganizations();
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();
  const changePasswordMutation = useChangePassword();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [changingPasswordUser, setChangingPasswordUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');

  const users = usersData?.users || [];
  const organizations = organizationsData?.organizations || [];
  const totalUsers = usersData?.total || 0;
  const activeUsers = users.filter(u => u.is_active).length;

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

  const handleChangePassword = () => {
    if (!changingPasswordUser || !newPassword) return;
    changePasswordMutation.mutate(
      { id: changingPasswordUser.id, data: { new_password: newPassword } as ChangePasswordRequest },
      { onSuccess: () => { setChangingPasswordUser(null); setNewPassword(''); }}
    );
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  return (
    <>
      {/* Stats */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div><p className="text-sm text-gray-600 dark:text-gray-400">{t('users.stats.totalUsers')}</p><p className="text-2xl font-bold text-gray-900 dark:text-white">{totalUsers}</p></div>
            <Shield className="w-10 h-10 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div><p className="text-sm text-gray-600 dark:text-gray-400">{t('users.stats.active')}</p><p className="text-2xl font-bold text-green-600 dark:text-green-400">{activeUsers}</p></div>
            <Shield className="w-10 h-10 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mb-6 flex justify-end">
        <button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus className="w-5 h-5" />{t('users.actions.createUser')}
        </button>
      </div>

      {/* User List */}
      <UserList users={users} onEdit={setEditingUser} onDelete={setDeletingUser} onChangePassword={setChangingPasswordUser} />

      {/* Modals */}
      {showCreateModal && <UserForm organizations={organizations} onClose={() => setShowCreateModal(false)} onSubmit={handleCreate} isLoading={createMutation.isPending} />}
      {editingUser && <UserForm user={editingUser} organizations={organizations} onClose={() => setEditingUser(null)} onSubmit={handleUpdate} isLoading={updateMutation.isPending} />}
      {deletingUser && <DeleteConfirmModal isOpen={!!deletingUser} title={t('users.delete.title')} message={t('users.delete.message')} itemName={deletingUser.username} onClose={() => setDeletingUser(null)} onConfirm={handleDelete} isLoading={deleteMutation.isPending} />}
      {changingPasswordUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('users.changePassword.title')}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t('users.changePassword.user')}: {changingPasswordUser.username}</p>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder={t('users.changePassword.newPasswordPlaceholder')} className="w-full px-3 py-2 border dark:bg-gray-700 dark:text-white rounded-lg mb-4" />
            <div className="flex justify-end gap-3">
              <button onClick={() => { setChangingPasswordUser(null); setNewPassword(''); }} className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">{t('users.actions.cancel')}</button>
              <button onClick={handleChangePassword} disabled={!newPassword || changePasswordMutation.isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                {changePasswordMutation.isPending ? <><Loader2 className="w-4 h-4 animate-spin" />{t('users.changePassword.changing')}</> : <><Key className="w-4 h-4" />{t('users.actions.change')}</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
