/**
 * Role Form Component
 * Form for creating and editing roles
 */

import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Role, CreateRoleRequest, UpdateRoleRequest } from '../types/rbac.types'

// ============================================================================
// Validation Schema
// ============================================================================

// Note: Validation messages are in English for consistency with zod validation
const roleSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters').max(50, 'Name must be less than 50 characters'),
  description: z.string().max(200, 'Description must be less than 200 characters').optional(),
  is_active: z.boolean().default(true),
})

type RoleFormData = z.infer<typeof roleSchema>

// ============================================================================
// Component Props
// ============================================================================

interface RoleFormProps {
  role?: Role
  onSubmit: (data: CreateRoleRequest | UpdateRoleRequest) => void
  onCancel: () => void
  isLoading?: boolean
}

// ============================================================================
// Component
// ============================================================================

export function RoleForm({ role, onSubmit, onCancel, isLoading }: RoleFormProps) {
  const { t } = useTranslation()
  const isEditMode = !!role

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
  })

  const handleFormSubmit = (data: RoleFormData) => {
    onSubmit(data)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {isEditMode ? t('rbac.editRole') : t('rbac.createNewRole')}
        </h2>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
        {/* Role Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('rbac.roleName')} *
          </label>
          <input
            type="text"
            {...register('name')}
            disabled={role?.is_system}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder={t('rbac.roleNamePlaceholder')}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.name.message}
            </p>
          )}
          {role?.is_system && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {t('rbac.systemRoleCannotBeRenamed')}
            </p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('rbac.description')}
          </label>
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
            placeholder={t('rbac.descriptionPlaceholder')}
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.description.message}
            </p>
          )}
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {t('rbac.descriptionHelp')}
          </p>
        </div>

        {/* Active Status */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="is_active"
            {...register('is_active')}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {t('rbac.active')}
          </label>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('rbac.inactiveRolesHelp')}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin h-4 w-4" />
                {t('common.saving')}
              </span>
            ) : (
              isEditMode ? t('rbac.updateRole') : t('rbac.createRole')
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
