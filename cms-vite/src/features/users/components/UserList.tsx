/**
 * User List Component
 *
 * Table display of users with actions
 * Following CMS UI Development skill standards
 */

import { useTranslation } from 'react-i18next';
import { Shield, Pencil, Trash2, Key, Building, UserCog } from 'lucide-react';
import { TABLE_STYLES, ACTION_BUTTON, SortableTableHeader, DateCell } from '@/shared/components';
import type { SortConfig } from '@/shared/components';
import type { User } from '../types/user';

interface UserListProps {
  users: User[];
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
  onChangePassword?: (user: User) => void;
  onAssignRole?: (user: User) => void;
  // Sorting props (optional - controlled by parent)
  sortConfig?: SortConfig | null;
  onSortChange?: (config: SortConfig | null) => void;
}

export function UserList({
  users,
  onEdit,
  onDelete,
  onChangePassword,
  onAssignRole,
  sortConfig,
  onSortChange,
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
            <th className="w-72 px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="username"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('users.table.user')}
                </SortableTableHeader>
              ) : (
                t('users.table.user')
              )}
            </th>
            <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="is_active"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('users.table.status')}
                </SortableTableHeader>
              ) : (
                t('users.table.status')
              )}
            </th>
            <th className="w-28 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="role"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('users.table.role')}
                </SortableTableHeader>
              ) : (
                t('users.table.role')
              )}
            </th>
            <th className="w-32 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="organization_name"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('users.table.organization')}
                </SortableTableHeader>
              ) : (
                t('users.table.organization')
              )}
            </th>
            <th className="w-24 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {sortConfig && onSortChange ? (
                <SortableTableHeader
                  columnKey="created_at"
                  sortConfig={sortConfig}
                  onSortChange={onSortChange}
                >
                  {t('users.table.joined', 'Joined')}
                </SortableTableHeader>
              ) : (
                t('users.table.joined', 'Joined')
              )}
            </th>
            <th className="w-36 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              {t('users.table.actions')}
            </th>
          </tr>
        </thead>
        <tbody className={TABLE_STYLES.tbody}>
          {users?.map((user) => (
            <tr key={user.id} className={TABLE_STYLES.tr}>
              <td className="px-3 py-4 overflow-hidden">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-gray-900 dark:text-white truncate" title={user.full_name || user.username}>
                    {user.full_name || user.username}
                    {user.full_name && (
                      <span className="ml-1 text-gray-500 dark:text-gray-400 font-normal">
                        ({user.username})
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={user.email}>
                    {user.email}
                  </div>
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
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
              <td className="px-4 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                  {t(`users.roles.${user.role}`)}
                </span>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center">
                  <Building className="w-4 h-4 mr-1" />
                  {user.organization_name || t('users.table.noOrganization')}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <DateCell date={user.created_at} />
              </td>
              <td className={TABLE_STYLES.td}>
                <div className="flex items-center gap-2">
                  {onAssignRole && (
                    <button
                      onClick={() => onAssignRole(user)}
                      className={ACTION_BUTTON.ASSIGN}
                      title={t('users.actions.assignRole') || 'Assign Role'}
                    >
                      <UserCog className="w-4 h-4" />
                    </button>
                  )}
                  {onChangePassword && (
                    <button
                      onClick={() => onChangePassword(user)}
                      className={ACTION_BUTTON.SETTINGS}
                      title={t('users.actions.changePassword')}
                    >
                      <Key className="w-4 h-4" />
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={() => onEdit(user)}
                      className={ACTION_BUTTON.EDIT}
                      title={t('users.actions.editUser')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(user)}
                      className={ACTION_BUTTON.DELETE}
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
