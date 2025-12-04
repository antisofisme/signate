/**
 * Role Assignment Modal Component
 *
 * Modal dialog for assigning roles to users
 * Following CMS UI Development skill standards
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, Check, Loader2 } from 'lucide-react';
import { Button, Modal } from '@/shared/components';
import { useRoles } from '@/features/rbac/hooks/useRoles';
import { useAssignRoleToUser } from '@/features/rbac/hooks/usePermissions';
import type { User } from '../types/user';
import type { Role } from '@/features/rbac/types/rbac.types';

interface RoleAssignmentModalProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
}

export function RoleAssignmentModal({
  isOpen,
  user,
  onClose,
}: RoleAssignmentModalProps) {
  const { t } = useTranslation();
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);

  // Fetch available roles
  const { data: rolesData, isLoading: isLoadingRoles } = useRoles();
  const assignRoleMutation = useAssignRoleToUser();

  const roles = rolesData?.roles || [];

  // Reset selection when modal opens with a new user
  useEffect(() => {
    if (user && roles.length > 0) {
      // Find current role and select it
      const currentRole = roles.find(
        (r) => r.name.toLowerCase() === user.role.toLowerCase()
      );
      setSelectedRoleId(currentRole?.id || null);
    }
  }, [user, roles]);

  const handleAssign = () => {
    if (!user || !selectedRoleId) return;

    assignRoleMutation.mutate(
      { userId: user.id, roleId: selectedRoleId },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  const handleClose = () => {
    setSelectedRoleId(null);
    onClose();
  };

  if (!user) return null;

  const getRoleBadgeColor = (role: Role) => {
    const roleName = role.name.toLowerCase();
    switch (roleName) {
      case 'super_admin':
        return 'border-purple-500 bg-purple-50 dark:bg-purple-900/20';
      case 'admin':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      case 'content_manager':
        return 'border-green-500 bg-green-50 dark:bg-green-900/20';
      case 'viewer':
        return 'border-gray-400 bg-gray-50 dark:bg-gray-800/50';
      default:
        return 'border-gray-300 bg-gray-50 dark:bg-gray-800/50';
    }
  };

  const getRoleIcon = (role: Role) => {
    const roleName = role.name.toLowerCase();
    switch (roleName) {
      case 'super_admin':
        return 'text-purple-600 dark:text-purple-400';
      case 'admin':
        return 'text-blue-600 dark:text-blue-400';
      case 'content_manager':
        return 'text-green-600 dark:text-green-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const isCurrentRole = (role: Role) => {
    return role.name.toLowerCase() === user.role.toLowerCase();
  };

  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={assignRoleMutation.isPending}
      >
        {t('common.cancel', 'Cancel')}
      </Button>
      <Button
        type="button"
        variant="primary"
        onClick={handleAssign}
        disabled={
          assignRoleMutation.isPending ||
          !selectedRoleId ||
          isCurrentRole(roles.find((r) => r.id === selectedRoleId) || {} as Role)
        }
        loading={assignRoleMutation.isPending}
        leftIcon={<Shield className="w-4 h-4" />}
      >
        {t('users.roles.assign', 'Assign Role')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('users.roles.assignTitle', 'Assign Role')}
      maxWidth="md"
      footer={footer}
    >
      <div className="p-6 space-y-4">
        {/* User info */}
        <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('users.table.user', 'User')}:{' '}
            <span className="font-medium text-gray-900 dark:text-white">
              {user.full_name || user.username}
            </span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('users.changePassword.email', 'Email')}:{' '}
            <span className="font-medium text-gray-900 dark:text-white">
              {user.email}
            </span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {t('users.roles.current', 'Current Role')}:{' '}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
              {t(`users.roles.${user.role}`, user.role)}
            </span>
          </p>
        </div>

        {/* Role list */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            {t('users.roles.selectRole', 'Select Role')}
          </label>

          {isLoadingRoles ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : roles.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {t('users.roles.noRoles', 'No roles available')}
            </div>
          ) : (
            <div className="space-y-2">
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => setSelectedRoleId(role.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all ${
                    selectedRoleId === role.id
                      ? `${getRoleBadgeColor(role)} border-opacity-100`
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Shield
                      className={`w-5 h-5 ${
                        selectedRoleId === role.id
                          ? getRoleIcon(role)
                          : 'text-gray-400'
                      }`}
                    />
                    <div className="text-left">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {t(`users.roles.${role.name.toLowerCase()}`, role.name)}
                      </p>
                      {role.description && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {role.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isCurrentRole(role) && (
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300">
                        {t('users.roles.currentBadge', 'Current')}
                      </span>
                    )}
                    {selectedRoleId === role.id && (
                      <Check className="w-5 h-5 text-green-500" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Info note */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mt-4">
          <p className="text-xs text-blue-800 dark:text-blue-200">
            <strong>{t('common.note', 'Note')}:</strong>{' '}
            {t('users.roles.assignNote', 'Changing a user\'s role will update their permissions immediately. The user may need to log out and log back in for changes to take full effect.')}
          </p>
        </div>
      </div>
    </Modal>
  );
}

export default RoleAssignmentModal;
