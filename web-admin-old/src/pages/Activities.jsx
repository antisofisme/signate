import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { activitiesAPI } from '../services/api'
import toast, { Toaster } from 'react-hot-toast'
import {
  Activity, Tv, Upload, ListVideo, Tag, Link, User, Settings,
  Filter, Calendar, Download, RefreshCw, TrendingUp, Clock
} from 'lucide-react'
import { format } from 'date-fns'

/**
 * FASE 3.2: Full Activity Logs Page
 *
 * Features:
 * - Activity stats cards (today, week, month)
 * - Advanced filtering (action type, entity type, user, date range)
 * - Paginated activity table
 * - Export functionality
 * - Real-time refresh
 */
export default function Activities() {
  // Filter states
  const [filters, setFilters] = useState({
    action_type: '',
    entity_type: '',
    user_id: '',
    start_date: '',
    end_date: '',
  })
  const [page, setPage] = useState(0)
  const [limit] = useState(50)

  // Fetch activities with filters
  const { data: activities, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['activities', 'list', filters, page, limit],
    queryFn: () => activitiesAPI.list({
      ...filters,
      skip: page * limit,
      limit
    }).then(res => res.data),
    refetchInterval: 60000 // Refresh every minute
  })

  // Fetch activity stats
  const { data: stats } = useQuery({
    queryKey: ['activities', 'stats'],
    queryFn: () => activitiesAPI.stats().then(res => res.data),
    refetchInterval: 60000
  })

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(0) // Reset to first page
  }

  const clearFilters = () => {
    setFilters({
      action_type: '',
      entity_type: '',
      user_id: '',
      start_date: '',
      end_date: '',
    })
    setPage(0)
  }

  const exportToCSV = () => {
    if (!activities?.items) return

    const headers = ['Timestamp', 'User', 'Action', 'Entity Type', 'Entity Name', 'Details']
    const rows = activities.items.map(activity => [
      format(new Date(activity.timestamp), 'yyyy-MM-dd HH:mm:ss'),
      activity.user?.username || 'System',
      activity.action_type,
      activity.entity_type,
      activity.entity_name || '',
      JSON.stringify(activity.details || {})
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `activity-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
  }

  const getActivityIcon = (actionType) => {
    if (actionType.includes('DEVICE')) return <Tv className="w-4 h-4" />
    if (actionType.includes('CONTENT')) return <Upload className="w-4 h-4" />
    if (actionType.includes('PLAYLIST')) return <ListVideo className="w-4 h-4" />
    if (actionType.includes('TAG')) return <Tag className="w-4 h-4" />
    if (actionType.includes('ASSIGNED') || actionType.includes('UNASSIGNED')) return <Link className="w-4 h-4" />
    if (actionType.includes('USER')) return <User className="w-4 h-4" />
    if (actionType.includes('SETTINGS') || actionType.includes('SYSTEM')) return <Settings className="w-4 h-4" />
    return <Activity className="w-4 h-4" />
  }

  const getActionBadgeColor = (actionType) => {
    if (actionType.includes('DELETE') || actionType.includes('REJECTED') || actionType.includes('UNASSIGNED')) {
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
    }
    if (actionType.includes('CREATE') || actionType.includes('UPLOAD') || actionType.includes('APPROVED') || actionType.includes('REGISTERED') || actionType.includes('ASSIGNED')) {
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    }
    if (actionType.includes('UPDATE')) {
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    }
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
  }

  const totalPages = Math.ceil((activities?.total || 0) / limit)

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      <Toaster />

      {/* Page Header - Dashboard style */}
      <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-md transition-colors">
        <div className="px-4 sm:px-6 lg:px-8 py-3">
          <div className="pl-12 lg:pl-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Activity Logs</h1>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mt-1">
              System activity and audit trail
            </p>
          </div>
        </div>
      </div>

      {/* Content with padding to account for fixed header */}
      <div className="pt-20 sm:pt-24 lg:pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6 animate-fade-in">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Today</p>
              <p className="text-3xl font-bold text-gray-800 dark:text-white">
                {stats?.today || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
              <TrendingUp className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">This Week</p>
              <p className="text-3xl font-bold text-gray-800 dark:text-white">
                {stats?.this_week || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
              <Calendar className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">This Month</p>
              <p className="text-3xl font-bold text-gray-800 dark:text-white">
                {stats?.this_month || 0}
              </p>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
              <Activity className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Action Type
            </label>
            <select
              value={filters.action_type}
              onChange={(e) => handleFilterChange('action_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Actions</option>
              <optgroup label="Device">
                <option value="DEVICE_REGISTERED">Device Registered</option>
                <option value="DEVICE_APPROVED">Device Approved</option>
                <option value="DEVICE_REJECTED">Device Rejected</option>
                <option value="DEVICE_UPDATED">Device Updated</option>
                <option value="DEVICE_DELETED">Device Deleted</option>
              </optgroup>
              <optgroup label="Content">
                <option value="CONTENT_UPLOADED">Content Uploaded</option>
                <option value="CONTENT_UPDATED">Content Updated</option>
                <option value="CONTENT_DELETED">Content Deleted</option>
                <option value="CONTENT_ASSIGNED">Content Assigned</option>
                <option value="CONTENT_UNASSIGNED">Content Unassigned</option>
              </optgroup>
              <optgroup label="Playlist">
                <option value="PLAYLIST_CREATED">Playlist Created</option>
                <option value="PLAYLIST_UPDATED">Playlist Updated</option>
                <option value="PLAYLIST_DELETED">Playlist Deleted</option>
                <option value="PLAYLIST_ASSIGNED">Playlist Assigned</option>
                <option value="PLAYLIST_UNASSIGNED">Playlist Unassigned</option>
              </optgroup>
              <optgroup label="Tag">
                <option value="TAG_CREATED">Tag Created</option>
                <option value="TAG_UPDATED">Tag Updated</option>
                <option value="TAG_DELETED">Tag Deleted</option>
              </optgroup>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Entity Type
            </label>
            <select
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Entities</option>
              <option value="device">Device</option>
              <option value="content">Content</option>
              <option value="playlist">Playlist</option>
              <option value="tag">Tag</option>
              <option value="user">User</option>
              <option value="system">System</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Date Range
            </label>
            <div className="flex gap-2">
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={clearFilters}
            className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            Clear Filters
          </button>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={exportToCSV}
            className="px-4 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Activity Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Entity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
                      <span className="ml-2 text-gray-600 dark:text-gray-400">Loading activities...</span>
                    </div>
                  </td>
                </tr>
              ) : !activities?.items || activities.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <Activity className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p className="text-gray-600 dark:text-gray-400">No activities found</p>
                  </td>
                </tr>
              ) : (
                activities.items.map((activity) => (
                  <tr key={activity.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {format(new Date(activity.timestamp), 'MMM dd, yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-800 dark:text-gray-200">
                          {activity.user?.username || 'System'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getActionBadgeColor(activity.action_type)}`}>
                        {getActivityIcon(activity.action_type)}
                        {activity.action_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-800 dark:text-gray-200">
                      <div>
                        <p className="font-medium">{activity.entity_name || `${activity.entity_type} #${activity.entity_id}`}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{activity.entity_type}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      {activity.details && Object.keys(activity.details).length > 0 ? (
                        <details className="cursor-pointer">
                          <summary className="text-blue-600 dark:text-blue-400 hover:underline">
                            View details
                          </summary>
                          <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs overflow-x-auto">
                            {JSON.stringify(activity.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing {page * limit + 1} to {Math.min((page + 1) * limit, activities?.total || 0)} of {activities?.total || 0} activities
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
        </div>
      </div>
    </div>
  )
}
