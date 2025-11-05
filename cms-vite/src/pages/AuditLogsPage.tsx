/**
 * Audit Logs Page
 *
 * LAYER 1: PRESENTATION
 * View audit trail with filters and pagination
 */

import { useState } from 'react';
import { FileText, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuditLogs } from '@/features/audit/hooks/useAuditLogs';
import { useUsers } from '@/features/users/hooks/useUsers';
import { useOrganizations } from '@/features/organizations/hooks/useOrganizations';
import type { AuditLogFilters } from '@/features/audit/types/auditLog';
import { RESOURCE_TYPES } from '@/features/audit/types/auditLog';
import { PageHeader } from '@/shared/components';
import { format } from 'date-fns';

export default function AuditLogsPage() {
  const [filters, setFilters] = useState<AuditLogFilters>({
    page: 1,
    per_page: 20,
  });
  const [showFilters, setShowFilters] = useState(true);

  // Queries
  const { data, isLoading } = useAuditLogs(filters);
  const { data: usersData } = useUsers({});
  const { data: orgsData } = useOrganizations(true);

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const getActionBadgeColor = (action: string) => {
    if (action.includes('create')) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (action.includes('update')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (action.includes('delete')) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (action.includes('login')) return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getResourceBadgeColor = (resourceType: string) => {
    const colors: Record<string, string> = {
      user: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      organization: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      device: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      content: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      auth: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
    };
    return colors[resourceType] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  return (
    <>
      {/* Sticky Page Header */}
      <PageHeader
        title="Audit Logs"
        description="View system activity and user actions"
        actions={
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Filter className="w-5 h-5" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        }
      />

      {/* Content */}
      <div className="space-y-6">

        {/* Filters */}
        {showFilters && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  User
                </label>
                <select
                  value={filters.user_id || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      user_id: e.target.value ? parseInt(e.target.value) : undefined,
                      page: 1,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">All Users</option>
                  {usersData?.users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.username} ({user.full_name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Organization
                </label>
                <select
                  value={filters.organization_id || ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      organization_id: e.target.value ? parseInt(e.target.value) : undefined,
                      page: 1,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">All Organizations</option>
                  {orgsData?.organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Resource Type
                </label>
                <select
                  value={filters.resource_type || ''}
                  onChange={(e) =>
                    setFilters({
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

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Date Range
                </label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={filters.start_date || ''}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        start_date: e.target.value || undefined,
                        page: 1,
                      })
                    }
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>

            {/* Clear Filters */}
            {(filters.user_id || filters.organization_id || filters.resource_type || filters.start_date) && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => setFilters({ page: 1, per_page: 20 })}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Stats */}
        {data && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Audit Logs
                </h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {data.total.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading audit logs...</p>
            </div>
          ) : data && data.logs.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Resource
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Details
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        IP Address
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {data.logs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {format(new Date(log.created_at), 'MMM dd, yyyy')}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {format(new Date(log.created_at), 'HH:mm:ss')}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {log.username || 'System'}
                          </div>
                          {log.organization_name && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {log.organization_name}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionBadgeColor(log.action)}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getResourceBadgeColor(log.resource_type)}`}>
                            {log.resource_type}
                          </span>
                          {log.resource_id && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              ID: {log.resource_id}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-600 dark:text-gray-300 max-w-xs truncate">
                            {log.details ? JSON.stringify(log.details) : '-'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                          {log.ip_address || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    Showing {((data.page - 1) * data.per_page) + 1} to {Math.min(data.page * data.per_page, data.total)} of {data.total} results
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handlePageChange(data.page - 1)}
                      disabled={data.page === 1}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                      Page {data.page} of {data.total_pages}
                    </div>
                    <button
                      onClick={() => handlePageChange(data.page + 1)}
                      disabled={data.page === data.total_pages}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-12 text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No audit logs found. Try adjusting your filters.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
