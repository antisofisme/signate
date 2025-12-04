/**
 * User List Component
 *
 * Table display of users with actions
 * Following CMS UI Development skill standards
 */

import { useTranslation } from 'react-i18next';
import { Shield, Edit, Trash2, Key, Building, UserCog } from 'lucide-react';
import { TABLE_STYLES } from '@/shared/components';
import type { User } from '../types/user';

interface UserListProps {
  users: User[];
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
  onChangePassword?: (user: User) => void;
  onAssignRole?: (user: User) => void;
}

export function UserList({
  users,
  onEdit,
  onDelete,
  onChangePassword,
  onAssignRole,
}: UserListProps) {
  const { t } = useTranslation();

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'admin':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'editor':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className={TABLE_STYLES.container}>
      <div className="overflow-x-auto">
        <table className={`${TABLE_STYLES.table} table-fixed`}>
          <thead className={TABLE_STYLES.thead}>
          <tr>
            <th className={`${TABLE_STYLES.th} w-[25%]`}>
              {t('users.table.user')}
            </th>
            <th className={`${TABLE_STYLES.th} w-20`}>
              {t('users.table.status')}
            </th>
            <th className={`${TABLE_STYLES.th} w-24`}>
              {t('users.table.role')}
            </th>
            <th className={`${TABLE_STYLES.th} w-[20%]`}>
              {t('users.table.organization')}
            </th>
            <th className={`${TABLE_STYLES.th} w-32`}>
              {t('users.table.actions')}
            </th>
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {users?.map((user) => (
            <tr key={user.id} className={TABLE_STYLES.tr}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {user.full_name || user.username}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {user.email}
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    user.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}
                >
                  {user.is_active ? t('users.status.active') : t('users.status.inactive')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                  {t(`users.roles.${user.role}`)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center">
                  <Building className="w-4 h-4 mr-1" />
                  {user.organization_name || t('users.table.noOrganization')}
                </div>
              </td>
              <td className={TABLE_STYLES.td}>
                <div className="flex items-center gap-2">
                  {onAssignRole && (
                    <button
                      onClick={() => onAssignRole(user)}
                      className={TABLE_STYLES.actionBtnPurple || 'p-2 rounded-lg text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors'}
                      title={t('users.actions.assignRole') || 'Assign Role'}
                    >
                      <UserCog className="w-4 h-4" />
                    </button>
                  )}
                  {onChangePassword && (
                    <button
                      onClick={() => onChangePassword(user)}
                      className={TABLE_STYLES.actionBtnGreen}
                      title={t('users.actions.changePassword')}
                    >
                      <Key className="w-4 h-4" />
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={() => onEdit(user)}
                      className={TABLE_STYLES.actionBtnBlue}
                      title={t('users.actions.editUser')}
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(user)}
                      className={TABLE_STYLES.actionBtnRed}
                      title={t('users.actions.deleteUser')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  {!onEdit && !onChangePassword && !onDelete && !onAssignRole && (
                    <span className="text-gray-400 dark:text-gray-600 text-xs">
                      {t('common.noActions') || 'No actions'}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default UserList;
