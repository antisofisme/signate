/**
 * Role Card Component
 * Displays role information in a card format
 */

import React from 'react'
import { Shield, Users, Lock, Edit, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Role } from '../types/rbac.types'

interface RoleCardProps {
  role: Role
  onEdit?: (role: Role) => void
  onDelete?: (role: Role) => void
  onViewDetails?: (role: Role) => void
}

export function RoleCard({ role, onEdit, onDelete, onViewDetails }: RoleCardProps) {
  const { t } = useTranslation()
  const isSystemRole = role.is_system

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => onViewDetails?.(role)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            isSystemRole
              ? 'bg-purple-100 dark:bg-purple-900/30'
              : 'bg-blue-100 dark:bg-blue-900/30'
          }`}>
            <Shield className={`w-5 h-5 ${
              isSystemRole
                ? 'text-purple-600 dark:text-purple-400'
                : 'text-blue-600 dark:text-blue-400'
            }`} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {role.name}
            </h3>
            {isSystemRole && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300 rounded">
                <Lock className="w-3 h-3" />
                {t('rbac.systemRole')}
              </span>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <span
          className={`px-2 py-1 text-xs font-medium rounded ${
            role.is_active
              ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          {role.is_active ? t('rbac.active') : t('rbac.inactive')}
        </span>
      </div>

      {/* Description */}
      {role.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {role.description}
        </p>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
          <Users className="w-4 h-4" />
          <span>{role.users_count || 0} {t('rbac.users')}</span>
        </div>
        {role.permissions && (
          <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
            <Shield className="w-4 h-4" />
            <span>{role.permissions.length} {t('rbac.permissions')}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      {!isSystemRole && (
        <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          {onEdit && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEdit(role)
              }}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
            >
              <Edit className="w-4 h-4" />
              {t('common.edit')}
            </button>
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete(role)
              }}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              {t('common.delete')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
