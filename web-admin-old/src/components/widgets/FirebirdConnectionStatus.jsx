import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Clock } from 'lucide-react'
import { firebirdAPI } from '../../services/api'
import { Button } from '../shared'

/**
 * FirebirdConnectionStatus Component
 * Displays real-time connection status for a Firebird configuration
 *
 * Features:
 * - Visual status indicators (connected/error/checking)
 * - Auto-refresh health status every 30 seconds
 * - Manual refresh button
 * - Last sync timestamp
 * - Error message display
 *
 * @param {number} configId - Firebird configuration ID
 * @param {Object} config - Full configuration object (optional, for displaying info)
 * @param {boolean} autoRefresh - Enable auto-refresh (default: true)
 */
export default function FirebirdConnectionStatus({ configId, config, autoRefresh = true }) {
  const [lastSyncTime, setLastSyncTime] = useState(null)

  // Fetch health status with auto-refresh
  const { data: healthData, isLoading, error, refetch } = useQuery({
    queryKey: ['firebird-health', configId],
    queryFn: () => firebirdAPI.getHealth(configId).then(res => res.data),
    refetchInterval: autoRefresh ? 30000 : false, // Auto-refresh every 30s
    onSuccess: (data) => {
      if (data?.last_sync) {
        setLastSyncTime(new Date(data.last_sync))
      }
    },
  })

  // Determine status
  const getStatus = () => {
    if (isLoading) return 'checking'
    if (error || healthData?.status === 'error') return 'error'
    if (healthData?.status === 'connected') return 'connected'
    return 'disconnected'
  }

  const status = getStatus()

  // Status display config
  const statusConfig = {
    connected: {
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-200 dark:border-green-700',
      label: 'Connected',
    },
    error: {
      icon: XCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      borderColor: 'border-red-200 dark:border-red-700',
      label: 'Error',
    },
    disconnected: {
      icon: AlertCircle,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
      borderColor: 'border-yellow-200 dark:border-yellow-700',
      label: 'Disconnected',
    },
    checking: {
      icon: RefreshCw,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      borderColor: 'border-blue-200 dark:border-blue-700',
      label: 'Checking...',
    },
  }

  const currentConfig = statusConfig[status]
  const StatusIcon = currentConfig.icon

  // Format time ago
  const formatTimeAgo = (date) => {
    if (!date) return 'Never'

    const seconds = Math.floor((new Date() - date) / 1000)

    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  return (
    <div
      className={`p-4 rounded-lg border ${currentConfig.bgColor} ${currentConfig.borderColor}`}
    >
      <div className="flex items-center justify-between">
        {/* Status Info */}
        <div className="flex items-center gap-3">
          <StatusIcon
            className={`w-6 h-6 ${currentConfig.color} ${status === 'checking' ? 'animate-spin' : ''}`}
          />
          <div>
            <div className="flex items-center gap-2">
              <span className={`font-semibold ${currentConfig.color}`}>
                {currentConfig.label}
              </span>
              {config && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  ({config.config_key})
                </span>
              )}
            </div>

            {/* Last Sync Time */}
            {lastSyncTime && (
              <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 mt-1">
                <Clock className="w-3 h-3" />
                <span>Last sync: {formatTimeAgo(lastSyncTime)}</span>
              </div>
            )}

            {/* Error Message */}
            {status === 'error' && (
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                {error?.response?.data?.detail || healthData?.message || 'Connection failed'}
              </p>
            )}

            {/* Connection Info */}
            {status === 'connected' && healthData?.message && (
              <p className="text-sm text-green-700 dark:text-green-400 mt-1">
                {healthData.message}
              </p>
            )}
          </div>
        </div>

        {/* Manual Refresh Button */}
        <Button
          onClick={() => refetch()}
          disabled={isLoading}
          variant="ghost"
          size="sm"
          leftIcon={<RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
          title="Refresh connection status"
        >
          Refresh
        </Button>
      </div>

      {/* Additional Info */}
      {config && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
            <div>
              <span className="font-medium">Mode:</span>{' '}
              <span className="capitalize">{config.connection_mode}</span>
            </div>
            {config.connection_mode === 'server' && (
              <div>
                <span className="font-medium">Host:</span>{' '}
                <span>{config.database_host}:{config.database_port}</span>
              </div>
            )}
            <div className="col-span-2">
              <span className="font-medium">Database:</span>{' '}
              <span className="break-all">{config.database_path}</span>
            </div>
            <div>
              <span className="font-medium">Refresh:</span>{' '}
              <span>{config.refresh_interval}s</span>
            </div>
            <div>
              <span className="font-medium">Status:</span>{' '}
              <span className={config.is_active ? 'text-green-600' : 'text-gray-500'}>
                {config.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * FirebirdConnectionBadge Component
 * Compact badge version for displaying in lists/cards
 *
 * @param {string} status - Connection status ('connected', 'error', 'checking')
 * @param {boolean} showLabel - Show text label (default: true)
 */
export function FirebirdConnectionBadge({ status, showLabel = true }) {
  const statusConfig = {
    connected: {
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      label: 'Connected',
    },
    error: {
      icon: XCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      label: 'Error',
    },
    checking: {
      icon: RefreshCw,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      label: 'Checking',
    },
    disconnected: {
      icon: AlertCircle,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      label: 'Disconnected',
    },
  }

  const config = statusConfig[status] || statusConfig.disconnected
  const Icon = config.icon

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${config.bgColor}`}
    >
      <Icon
        className={`w-3.5 h-3.5 ${config.color} ${status === 'checking' ? 'animate-spin' : ''}`}
      />
      {showLabel && (
        <span className={`text-xs font-medium ${config.color}`}>
          {config.label}
        </span>
      )}
    </div>
  )
}
