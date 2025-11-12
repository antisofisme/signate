/**
 * Audit Log Filters Component
 * Filter controls for audit logs
 */

import { X } from 'lucide-react';
import type { AuditLogFilters as Filters } from '../types/auditLog';
import { RESOURCE_TYPES } from '../types/auditLog';

interface AuditLogFiltersProps {
  filters: Filters;
  users: any[];
  organizations: any[];
  onFilterChange: (filters: Filters) => void;
  onClearFilters: () => void;
}

export function AuditLogFilters({
  filters,
  users,
  organizations,
  onFilterChange,
  onClearFilters,
}: AuditLogFiltersProps) {
  const hasActiveFilters = filters.user_id || filters.organization_id || filters.resource_type || filters.start_date;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* User Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            User
          </label>
          <select
            value={filters.user_id || ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                user_id: e.target.value ? parseInt(e.target.value) : undefined,
                page: 1,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Users</option>
            {users?.map((user) => (
              <option key={user.id} value={user.id}>
                {user.username} ({user.full_name})
              </option>
            ))}
          </select>
        </div>

        {/* Organization Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Organization
          </label>
          <select
            value={filters.organization_id || ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                organization_id: e.target.value ? parseInt(e.target.value) : undefined,
                page: 1,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Organizations</option>
            {organizations?.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
        </div>

        {/* Resource Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Resource Type
          </label>
          <select
            value={filters.resource_type || ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                resource_type: e.target.value || undefined,
                page: 1,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Types</option>
            {RESOURCE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Date Range
          </label>
          <input
            type="date"
            value={filters.start_date || ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                start_date: e.target.value || undefined,
                page: 1,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={onClearFilters}
            className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            <X className="w-4 h-4" />
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}

export default AuditLogFilters;
