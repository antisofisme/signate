/**
 * Permission Matrix Component
 * Visual matrix for managing role permissions
 */

import React, { useState, useMemo } from 'react'
import { Check, X } from 'lucide-react'
import type { Permission, PermissionResource, PermissionAction } from '../types/rbac.types'

// ============================================================================
// Types
// ============================================================================

interface PermissionMatrixProps {
  permissions: Permission[]
  selectedPermissions: number[]
  onPermissionToggle: (permissionId: number) => void
  readOnly?: boolean
}

interface PermissionCell {
  permission: Permission
  isSelected: boolean
}

// ============================================================================
// Resource Icons & Labels
// ============================================================================

const RESOURCE_LABELS: Record<PermissionResource, string> = {
  users: 'Users',
  roles: 'Roles',
  organizations: 'Organizations',
  devices: 'Devices',
  content: 'Content',
  playlists: 'Playlists',
  schedules: 'Schedules',
  widgets: 'Widgets',
  templates: 'Templates',
  tags: 'Tags',
  analytics: 'Analytics',
  audit: 'Audit Logs',
  translations: 'Translations',
  pms: 'PMS Integration',
  weather: 'Weather',
  settings: 'Settings',
}

const ACTION_LABELS: Record<PermissionAction, string> = {
  create: 'Create',
  read: 'Read',
  update: 'Update',
  delete: 'Delete',
  manage: 'Manage',
}

const ACTION_COLORS: Record<PermissionAction, string> = {
  create: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
  read: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
  update: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
  delete: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
  manage: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
}

// ============================================================================
// Component
// ============================================================================

export function PermissionMatrix({
  permissions,
  selectedPermissions,
  onPermissionToggle,
  readOnly = false,
}: PermissionMatrixProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedResource, setSelectedResource] = useState<PermissionResource | 'all'>('all')

  // Group permissions by resource
  const permissionsByResource = useMemo(() => {
    const grouped: Record<PermissionResource, PermissionCell[]> = {} as any

    permissions.forEach((permission) => {
      if (!grouped[permission.resource]) {
        grouped[permission.resource] = []
      }

      grouped[permission.resource].push({
        permission,
        isSelected: selectedPermissions.includes(permission.id),
      })
    })

    // Sort by action
    Object.keys(grouped).forEach((resource) => {
      grouped[resource as PermissionResource].sort((a, b) => {
        const actionOrder = ['read', 'create', 'update', 'delete', 'manage']
        return actionOrder.indexOf(a.permission.action) - actionOrder.indexOf(b.permission.action)
      })
    })

    return grouped
  }, [permissions, selectedPermissions])

  // Filter resources
  const filteredResources = useMemo(() => {
    const resources = Object.keys(permissionsByResource) as PermissionResource[]

    return resources.filter((resource) => {
      // Filter by selected resource
      if (selectedResource !== 'all' && resource !== selectedResource) {
        return false
      }

      // Filter by search term
      if (searchTerm) {
        const resourceLabel = RESOURCE_LABELS[resource].toLowerCase()
        return resourceLabel.includes(searchTerm.toLowerCase())
      }

      return true
    })
  }, [permissionsByResource, selectedResource, searchTerm])

  // Calculate stats
  const stats = useMemo(() => {
    const total = permissions.length
    const selected = selectedPermissions.length
    const percentage = total > 0 ? Math.round((selected / total) * 100) : 0

    return { total, selected, percentage }
  }, [permissions, selectedPermissions])

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex items-center justify-between gap-4">
        {/* Search */}
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search resources..."
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        />

        {/* Resource Filter */}
        <select
          value={selectedResource}
          onChange={(e) => setSelectedResource(e.target.value as any)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="all">All Resources</option>
          {Object.entries(RESOURCE_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-semibold text-gray-900 dark:text-white">
            {stats.selected}
          </span>{' '}
          of {stats.total} permissions selected
        </div>
        <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all"
            style={{ width: `${stats.percentage}%` }}
          />
        </div>
        <div className="text-sm font-semibold text-gray-900 dark:text-white">
          {stats.percentage}%
        </div>
      </div>

      {/* Permission Matrix */}
      <div className="space-y-4">
        {filteredResources.map((resource) => (
          <div
            key={resource}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            {/* Resource Header */}
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {RESOURCE_LABELS[resource]}
              </h3>
            </div>

            {/* Permission Cells */}
            <div className="p-4">
              <div className="flex flex-wrap gap-2">
                {permissionsByResource[resource].map(({ permission, isSelected }) => (
                  <button
                    key={permission.id}
                    onClick={() => !readOnly && onPermissionToggle(permission.id)}
                    disabled={readOnly}
                    className={`
                      flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-sm transition-all
                      ${isSelected
                        ? `${ACTION_COLORS[permission.action]} ring-2 ring-offset-2 ring-blue-500 dark:ring-offset-gray-800`
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }
                      ${readOnly ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}
                    `}
                  >
                    {isSelected ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <X className="w-4 h-4 opacity-50" />
                    )}
                    <span>{ACTION_LABELS[permission.action]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}

        {/* Empty State */}
        {filteredResources.length === 0 && (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            No resources found matching your search
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
        <div className="font-semibold text-gray-700 dark:text-gray-300">Legend:</div>
        {Object.entries(ACTION_LABELS).map(([action, label]) => (
          <div key={action} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded ${ACTION_COLORS[action as PermissionAction].split(' ')[0]}`} />
            <span className="text-gray-600 dark:text-gray-400">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
