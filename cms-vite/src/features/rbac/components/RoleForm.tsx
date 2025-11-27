/**
 * Role Form Component
 * Form for creating and editing roles with permission matrix
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Loader2, Shield, Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PermissionMatrix } from './PermissionMatrix';
import type { Permissions } from '../constants/permissions';
import { countPermissions, getTotalPossiblePermissions } from '../constants/permissions';

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
// Validation Schema
// ============================================================================

const roleSchema = z.object({
  name: z
    .string()
    .min(3, 'Name must be at least 3 characters')
    .max(50, 'Name must be less than 50 characters'),
  description: z
    .string()
    .max(200, 'Description must be less than 200 characters')
    .optional()
    .or(z.literal('')),
  is_active: z.boolean().default(true),
});

type RoleFormData = z.infer<typeof roleSchema>;

// ============================================================================
// Component Props
// ============================================================================

interface RoleFormProps {
  role?: Role;
  onSubmit: (data: CreateRoleRequest | UpdateRoleRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function RoleForm({ role, onSubmit, onCancel, isLoading }: RoleFormProps) {
  const { t } = useTranslation();
  const isEditMode = !!role;
  const isSystemRole = role?.is_system_role ?? false;

  // Separate state for permissions (not part of react-hook-form)
  const [permissions, setPermissions] = useState<Permissions>(
    role?.permissions || {}
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RoleFormData>({
    resolver: zodResolver(roleSchema),
    defaultValues: {
      name: role?.name || '',
      description: role?.description || '',
      is_active: role?.is_active ?? true,
    },
  });

  const handleFormSubmit = (data: RoleFormData) => {
    // Combine form data with permissions
    const submitData: CreateRoleRequest | UpdateRoleRequest = {
      ...data,
      permissions,
    };
    onSubmit(submitData);
  };

  // Calculate permission stats
  const permissionCount = countPermissions(permissions);
  const totalPermissions = getTotalPossiblePermissions();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {isEditMode ? t('rbac.editRole', 'Edit Role') : t('rbac.createNewRole', 'Create New Role')}
            </h2>
            {isSystemRole && (
              <div className="flex items-center gap-1 text-sm text-amber-600 dark:text-amber-400">
                <Lock className="w-3 h-3" />
                <span>{t('rbac.systemRole', 'System Role')}</span>
              </div>
            )}
          </div>
        </div>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>
      </div>

      {/* Form - Scrollable */}
      <form
        onSubmit={handleSubmit(handleFormSubmit)}
        className="flex-1 overflow-y-auto"
      >
        <div className="p-6 space-y-6">
          {/* Basic Information Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('rbac.basicInformation', 'Basic Information')}
            </h3>

            {/* Role Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('rbac.roleName', 'Role Name')} *
              </label>
              <input
                type="text"
                {...register('name')}
                disabled={isSystemRole}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder={t('rbac.roleNamePlaceholder', 'e.g., content_editor')}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.name.message}
                </p>
              )}
              {isSystemRole && (
                <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
                  {t('rbac.systemRoleCannotBeRenamed', 'System roles cannot be renamed')}
                </p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('rbac.description', 'Description')}
              </label>
              <textarea
                {...register('description')}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
                placeholder={t('rbac.descriptionPlaceholder', 'Brief description of the role')}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.description.message}
                </p>
              )}
            </div>

            {/* Active Status */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_active"
                {...register('is_active')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
              />
              <label
                htmlFor="is_active"
                className="text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t('rbac.active', 'Active')}
              </label>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                ({t('rbac.inactiveRolesHelp', 'Inactive roles cannot be assigned to users')})
              </span>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-200 dark:border-gray-700" />

          {/* Permissions Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('rbac.permissions', 'Permissions')}
              </h3>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {permissionCount} / {totalPermissions} {t('rbac.selected', 'selected')}
              </span>
            </div>

            <PermissionMatrix
              permissions={permissions}
              onPermissionsChange={setPermissions}
              disabled={isLoading}
              isSystemRole={isSystemRole}
            />
          </div>
        </div>

        {/* Actions - Fixed at bottom */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex-shrink-0">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {t('common.cancel', 'Cancel')}
          </button>
          <button
            type="submit"
            disabled={isLoading || isSystemRole}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin h-4 w-4" />
                {t('common.saving', 'Saving...')}
              </span>
            ) : isSystemRole ? (
              <span className="flex items-center gap-2">
                <Lock className="w-4 h-4" />
                {t('rbac.systemRoleCannotEdit', 'Cannot Edit System Role')}
              </span>
            ) : isEditMode ? (
              t('rbac.updateRole', 'Update Role')
            ) : (
              t('rbac.createRole', 'Create Role')
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default RoleForm;
