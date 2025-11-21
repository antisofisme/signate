/**
 * Command History Component
 * Display command execution history with filters and search
 */

import { useState } from 'react'
import { History, Filter, Search, Download, RefreshCw, X, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'
import { deviceCommandApi } from '../api/commands'
import { useQuery } from '@tanstack/react-query'
import type { DeviceCommand, CommandStatus } from '../types/commands'
import { COMMAND_TYPE_INFO } from '../types/commandTemplates'
import { renderIcon } from '@/shared/utils/iconHelper'
import { usePagination } from '@/shared/hooks'
import { PaginationCompact } from '@/shared/components'

interface CommandHistoryProps {
  deviceId?: number
  maxHeight?: string
}

export function CommandHistory({ deviceId, maxHeight = '600px' }: CommandHistoryProps) {
  const [statusFilter, setStatusFilter] = useState<CommandStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Standardized pagination hook
  const pagination = usePagination({ pageSize: 20 })

  // Query command history
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['command-history', deviceId, statusFilter, pagination.currentPage],
    queryFn: () => {
      if (!deviceId) return { total: 0, items: [] }
      return deviceCommandApi.getCommands(deviceId, {
        status: statusFilter === 'all' ? undefined : statusFilter,
        skip: pagination.skip,
        limit: pagination.limit,
      })
    },
    enabled: !!deviceId,
    staleTime: 30 * 1000, // 30 seconds
  })

  // Filter commands by search query
  const filteredCommands = data?.items.filter((cmd) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      cmd.command_type.toLowerCase().includes(query) ||
      cmd.reason?.toLowerCase().includes(query) ||
      cmd.status.toLowerCase().includes(query) ||
      cmd.error_message?.toLowerCase().includes(query)
    )
  }) || []

  const total = data?.total || 0
  const totalPages = pagination.getTotalPages(total)

  const handleExport = () => {
    if (!filteredCommands.length) return

    const csv = [
      ['ID', 'Command Type', 'Status', 'Created At', 'Executed At', 'Reason', 'Error Message'].join(','),
      ...filteredCommands.map((cmd) =>
        [
          cmd.id,
          cmd.command_type,
          cmd.status,
          cmd.created_at,
          cmd.executed_at || '',
          cmd.reason || '',
          cmd.error_message || '',
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `command-history-${deviceId}-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Command History
            </h3>
            {data && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                ({data.total} total)
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleExport}
              disabled={!filteredCommands.length}
              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="Export CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Status Filter */}
          <div className="flex-1">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as CommandStatus | 'all')
                  pagination.resetPage()
                }}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="sent">Sent</option>
                <option value="executed">Executed</option>
                <option value="failed">Failed</option>
                <option value="expired">Expired</option>
              </select>
            </div>
          </div>

          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search commands..."
                className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Command List */}
      <div className="overflow-auto" style={{ maxHeight }}>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
            <span className="ml-2 text-gray-500 dark:text-gray-400">Loading history...</span>
          </div>
        ) : filteredCommands.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <History className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400 text-center">
              {searchQuery ? 'No commands match your search' : 'No command history'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredCommands.map((command) => (
              <CommandHistoryItem key={command.id} command={command} />
            ))}
          </div>
        )}
      </div>

      {/* Pagination - Using standardized component */}
      {totalPages > 1 && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          <PaginationCompact
            currentPage={pagination.currentPage}
            totalPages={totalPages}
            totalItems={total}
            pageSize={pagination.pageSize}
            onPageChange={pagination.goToPage}
            className="px-4"
          />
        </div>
      )}
    </div>
  )
}

// Command History Item Component
function CommandHistoryItem({ command }: { command: DeviceCommand }) {
  const [expanded, setExpanded] = useState(false)
  const commandInfo = COMMAND_TYPE_INFO[command.command_type]

  const statusConfig = {
    pending: { icon: Clock, color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30', label: 'Pending' },
    sent: { icon: AlertCircle, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30', label: 'Sent' },
    executed: { icon: CheckCircle, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30', label: 'Executed' },
    failed: { icon: XCircle, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30', label: 'Failed' },
    expired: { icon: XCircle, color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-900/30', label: 'Expired' },
  }

  const status = statusConfig[command.status]
  const StatusIcon = status.icon

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getExecutionTime = () => {
    if (!command.executed_at || !command.sent_at) return null
    const diff = new Date(command.executed_at).getTime() - new Date(command.sent_at).getTime()
    return `${(diff / 1000).toFixed(2)}s`
  }

  return (
    <div className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex-shrink-0">
              {renderIcon(commandInfo?.icon || 'FileText', { className: 'w-5 h-5 text-gray-600 dark:text-gray-400' })}
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {commandInfo?.label || command.command_type}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {formatDate(command.created_at)}
                {getExecutionTime() && ` • Executed in ${getExecutionTime()}`}
              </p>
            </div>
          </div>

          {command.reason && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Reason: {command.reason}
            </p>
          )}

          {command.error_message && (
            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-400">
              <strong>Error:</strong> {command.error_message}
            </div>
          )}

          {expanded && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">ID:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">{command.id}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Priority:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">{command.priority || 'Normal'}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Sent At:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">{formatDate(command.sent_at)}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Executed At:</span>
                  <span className="ml-2 text-gray-900 dark:text-white">{formatDate(command.executed_at)}</span>
                </div>
              </div>
              {command.command_data && Object.keys(command.command_data).length > 0 && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400 block mb-1">Command Data:</span>
                  <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto">
                    {JSON.stringify(command.command_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded ${status.bg} ${status.color}`}>
            <StatusIcon className="w-3 h-3" />
            {status.label}
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {expanded ? 'Less' : 'More'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CommandHistory
