/**
 * Role Card Component
 * Displays role information in a card format with permission count
 */

import React from 'react';
import { Shield, Users, Lock, Edit, Trash2, Eye, Key } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { countPermissions, getTotalPossiblePermissions, type Permissions } from '../constants/permissions';

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

interface RoleCardProps {
  role: Role;
  onEdit?: (role: Role) => void;
  onDelete?: (role: Role) => void;
  onView?: (role: Role) => void;
}

// ============================================================================
// Component
// ============================================================================

export function RoleCard({ role, onEdit, onDelete, onView }: RoleCardProps) {
  const { t } = useTranslation();
  const isSystemRole = role.is_system_role ?? false;

  // Calculate permission stats
  const permissionCount = countPermissions(role.permissions || {});
  const totalPermissions = getTotalPossiblePermissions();
  const permissionPercentage = totalPermissions > 0
    ? Math.round((permissionCount / totalPermissions) * 100)
    : 0;

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              isSystemRole
                ? 'bg-purple-100 dark:bg-purple-900/30'
                : 'bg-blue-100 dark:bg-blue-900/30'
            }`}
          >
            <Shield
              className={`w-5 h-5 ${
                isSystemRole
                  ? 'text-purple-600 dark:text-purple-400'
                  : 'text-blue-600 dark:text-blue-400'
              }`}
            />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white capitalize">
              {role.name.replace(/_/g, ' ')}
            </h3>
            {isSystemRole && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300 rounded">
                <Lock className="w-3 h-3" />
                {t('rbac.systemRole', 'System Role')}
              </span>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <span
          className={`px-2 py-1 text-xs font-medium rounded ${
            role.is_active !== false
              ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          {role.is_active !== false
            ? t('rbac.active', 'Active')
            : t('rbac.inactive', 'Inactive')}
        </span>
      </div>

      {/* Description */}
      {role.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {role.description}
        </p>
      )}

      {/* Stats */}
      <div className="space-y-3 mb-4">
        {/* User count */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Users className="w-4 h-4" />
          <span>
            {role.users_count || 0} {t('rbac.users', 'users')}
          </span>
        </div>

        {/* Permission count with progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <Key className="w-4 h-4" />
              <span>
                {permissionCount} / {totalPermissions} {t('rbac.permissions', 'permissions')}
              </span>
            </div>
            <span className="text-gray-500 dark:text-gray-400">{permissionPercentage}%</span>
          </div>
          <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                permissionPercentage === 100
                  ? 'bg-green-500'
                  : permissionPercentage > 50
                  ? 'bg-blue-500'
                  : permissionPercentage > 0
                  ? 'bg-yellow-500'
                  : 'bg-gray-300'
              }`}
              style={{ width: `${permissionPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        {/* View button - always visible */}
        {onView && (
          <button
            onClick={() => onView(role)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          >
            <Eye className="w-4 h-4" />
            {t('common.view', 'View')}
          </button>
        )}

        {/* Edit button - only for non-system roles */}
        {onEdit && !isSystemRole && (
          <button
            onClick={() => onEdit(role)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
          >
            <Edit className="w-4 h-4" />
            {t('common.edit', 'Edit')}
          </button>
        )}

        {/* Delete button - only for non-system roles */}
        {onDelete && !isSystemRole && (
          <button
            onClick={() => onDelete(role)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            {t('common.delete', 'Delete')}
          </button>
        )}

        {/* System role indicator */}
        {isSystemRole && (
          <span className="ml-auto text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
            <Lock className="w-3 h-3" />
            {t('rbac.protected', 'Protected')}
          </span>
        )}
      </div>
    </div>
  );
}

export default RoleCard;
