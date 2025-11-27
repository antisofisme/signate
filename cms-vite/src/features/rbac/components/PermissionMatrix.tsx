/**
 * Permission Matrix Component
 * Visual matrix for managing role permissions with {resource: [actions]} format
 */

import React, { useMemo, useCallback } from 'react';
import { Check, Minus, Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  PERMISSION_RESOURCES,
  PERMISSION_ACTIONS,
  RESOURCE_LABELS,
  ACTION_LABELS,
  ACTION_COLORS,
  countPermissions,
  getTotalPossiblePermissions,
  type Permissions,
  type PermissionResource,
  type PermissionAction,
} from '../constants/permissions';

// ============================================================================
// Types
// ============================================================================

interface PermissionMatrixProps {
  permissions: Permissions;
  onPermissionsChange: (permissions: Permissions) => void;
  disabled?: boolean;
  isSystemRole?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function PermissionMatrix({
  permissions,
  onPermissionsChange,
  disabled = false,
  isSystemRole = false,
}: PermissionMatrixProps) {
  const { t } = useTranslation();
  const isReadOnly = disabled || isSystemRole;

  // Calculate stats
  const stats = useMemo(() => {
    const selected = countPermissions(permissions);
    const total = getTotalPossiblePermissions();
    const percentage = total > 0 ? Math.round((selected / total) * 100) : 0;
    return { selected, total, percentage };
  }, [permissions]);

  // Toggle a single permission
  const togglePermission = useCallback(
    (resource: string, action: string) => {
      if (isReadOnly) return;

      const currentActions = permissions[resource] || [];
      const hasAction = currentActions.includes(action);

      let newActions: string[];
      if (hasAction) {
        // Remove action
        newActions = currentActions.filter((a) => a !== action);
      } else {
        // Add action
        newActions = [...currentActions, action];
      }

      // Update permissions
      const newPermissions = { ...permissions };
      if (newActions.length === 0) {
        delete newPermissions[resource];
      } else {
        newPermissions[resource] = newActions;
      }

      onPermissionsChange(newPermissions);
    },
    [permissions, onPermissionsChange, isReadOnly]
  );

  // Toggle all actions for a resource (row)
  const toggleResourceAll = useCallback(
    (resource: string) => {
      if (isReadOnly) return;

      const currentActions = permissions[resource] || [];
      const allSelected = PERMISSION_ACTIONS.every((action) =>
        currentActions.includes(action)
      );

      const newPermissions = { ...permissions };
      if (allSelected) {
        // Deselect all
        delete newPermissions[resource];
      } else {
        // Select all
        newPermissions[resource] = [...PERMISSION_ACTIONS];
      }

      onPermissionsChange(newPermissions);
    },
    [permissions, onPermissionsChange, isReadOnly]
  );

  // Toggle action for all resources (column)
  const toggleActionAll = useCallback(
    (action: string) => {
      if (isReadOnly) return;

      const allHaveAction = PERMISSION_RESOURCES.every((resource) => {
        const actions = permissions[resource] || [];
        return actions.includes(action);
      });

      const newPermissions: Permissions = {};

      PERMISSION_RESOURCES.forEach((resource) => {
        const currentActions = permissions[resource] || [];
        let newActions: string[];

        if (allHaveAction) {
          // Remove this action from all
          newActions = currentActions.filter((a) => a !== action);
        } else {
          // Add this action to all
          newActions = currentActions.includes(action)
            ? currentActions
            : [...currentActions, action];
        }

        if (newActions.length > 0) {
          newPermissions[resource] = newActions;
        }
      });

      onPermissionsChange(newPermissions);
    },
    [permissions, onPermissionsChange, isReadOnly]
  );

  // Check if all actions for resource are selected
  const isResourceAllSelected = useCallback(
    (resource: string): boolean => {
      const actions = permissions[resource] || [];
      return PERMISSION_ACTIONS.every((action) => actions.includes(action));
    },
    [permissions]
  );

  // Check if some actions for resource are selected
  const isResourcePartialSelected = useCallback(
    (resource: string): boolean => {
      const actions = permissions[resource] || [];
      return actions.length > 0 && !isResourceAllSelected(resource);
    },
    [permissions, isResourceAllSelected]
  );

  // Check if all resources have this action
  const isActionAllSelected = useCallback(
    (action: string): boolean => {
      return PERMISSION_RESOURCES.every((resource) => {
        const actions = permissions[resource] || [];
        return actions.includes(action);
      });
    },
    [permissions]
  );

  // Check if some resources have this action
  const isActionPartialSelected = useCallback(
    (action: string): boolean => {
      const count = PERMISSION_RESOURCES.filter((resource) => {
        const actions = permissions[resource] || [];
        return actions.includes(action);
      }).length;
      return count > 0 && count < PERMISSION_RESOURCES.length;
    },
    [permissions]
  );

  // Check if permission is selected
  const isPermissionSelected = useCallback(
    (resource: string, action: string): boolean => {
      return (permissions[resource] || []).includes(action);
    },
    [permissions]
  );

  return (
    <div className="space-y-4">
      {/* System Role Warning */}
      {isSystemRole && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-amber-700 dark:text-amber-400">
          <Lock className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">
            {t('rbac.systemRoleCannotEditPermissions', 'System role permissions cannot be modified')}
          </span>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-semibold text-gray-900 dark:text-white">
            {stats.selected}
          </span>{' '}
          / {stats.total} {t('rbac.permissionsSelected', 'permissions selected')}
        </div>
        <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${stats.percentage}%` }}
          />
        </div>
        <div className="text-sm font-semibold text-gray-900 dark:text-white">
          {stats.percentage}%
        </div>
      </div>

      {/* Permission Matrix Table */}
      <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        <table className="w-full">
          {/* Header */}
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700">
                {t('rbac.resource', 'Resource')}
              </th>
              {PERMISSION_ACTIONS.map((action) => {
                const allSelected = isActionAllSelected(action);
                const partialSelected = isActionPartialSelected(action);

                return (
                  <th
                    key={action}
                    className="px-3 py-3 text-center text-sm font-semibold border-b border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex flex-col items-center gap-1">
                      <span className={ACTION_COLORS[action as PermissionAction].split(' ')[0]}>
                        {ACTION_LABELS[action as PermissionAction]}
                      </span>
                      {!isReadOnly && (
                        <button
                          onClick={() => toggleActionAll(action)}
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                            allSelected
                              ? 'bg-blue-600 border-blue-600 text-white'
                              : partialSelected
                              ? 'bg-blue-100 border-blue-400 dark:bg-blue-900/30'
                              : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                          }`}
                          title={t('rbac.toggleAll', 'Toggle all')}
                        >
                          {allSelected ? (
                            <Check className="w-3 h-3" />
                          ) : partialSelected ? (
                            <Minus className="w-3 h-3 text-blue-600" />
                          ) : null}
                        </button>
                      )}
                    </div>
                  </th>
                );
              })}
              <th className="px-3 py-3 text-center text-sm font-semibold border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
                {t('rbac.all', 'All')}
              </th>
            </tr>
          </thead>

          {/* Body */}
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {PERMISSION_RESOURCES.map((resource, idx) => {
              const allSelected = isResourceAllSelected(resource);
              const partialSelected = isResourcePartialSelected(resource);

              return (
                <tr
                  key={resource}
                  className={
                    idx % 2 === 0
                      ? 'bg-white dark:bg-gray-900'
                      : 'bg-gray-50/50 dark:bg-gray-800/50'
                  }
                >
                  {/* Resource Name */}
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {RESOURCE_LABELS[resource as PermissionResource]}
                  </td>

                  {/* Action Checkboxes */}
                  {PERMISSION_ACTIONS.map((action) => {
                    const isSelected = isPermissionSelected(resource, action);

                    return (
                      <td key={action} className="px-3 py-3 text-center">
                        <button
                          onClick={() => togglePermission(resource, action)}
                          disabled={isReadOnly}
                          className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-all ${
                            isSelected
                              ? `${ACTION_COLORS[action as PermissionAction]} border-current`
                              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                          } ${isReadOnly ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                          title={`${ACTION_LABELS[action as PermissionAction]} ${RESOURCE_LABELS[resource as PermissionResource]}`}
                        >
                          {isSelected && <Check className="w-4 h-4" />}
                        </button>
                      </td>
                    );
                  })}

                  {/* Select All for Resource */}
                  <td className="px-3 py-3 text-center">
                    {!isReadOnly && (
                      <button
                        onClick={() => toggleResourceAll(resource)}
                        className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-all ${
                          allSelected
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : partialSelected
                            ? 'bg-blue-100 border-blue-400 dark:bg-blue-900/30'
                            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                        }`}
                        title={t('rbac.toggleAllForResource', 'Toggle all permissions for this resource')}
                      >
                        {allSelected ? (
                          <Check className="w-4 h-4" />
                        ) : partialSelected ? (
                          <Minus className="w-4 h-4 text-blue-600" />
                        ) : null}
                      </button>
                    )}
                    {isReadOnly && (
                      <div
                        className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                          allSelected
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : partialSelected
                            ? 'bg-blue-100 border-blue-400 dark:bg-blue-900/30'
                            : 'border-gray-300 dark:border-gray-600'
                        } opacity-60`}
                      >
                        {allSelected ? (
                          <Check className="w-4 h-4" />
                        ) : partialSelected ? (
                          <Minus className="w-4 h-4 text-blue-600" />
                        ) : null}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
        <div className="font-semibold text-gray-700 dark:text-gray-300">
          {t('rbac.legend', 'Legend')}:
        </div>
        {PERMISSION_ACTIONS.map((action) => (
          <div key={action} className="flex items-center gap-2">
            <div
              className={`w-4 h-4 rounded border-2 flex items-center justify-center ${ACTION_COLORS[action as PermissionAction]} border-current`}
            >
              <Check className="w-3 h-3" />
            </div>
            <span className="text-gray-600 dark:text-gray-400">
              {ACTION_LABELS[action as PermissionAction]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PermissionMatrix;
