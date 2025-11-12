/**
 * PMS Sync Status Component
 *
 * Display sync status with progress indicators
 */

import { RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { usePMSSyncStatus, useTriggerPMSSync } from '../hooks/usePMS'
import { formatDistanceToNow } from 'date-fns'

export function PMSSyncStatus() {
  const { data: syncStatus, isLoading } = usePMSSyncStatus()
  const triggerSync = useTriggerPMSSync()

  if (isLoading || !syncStatus) {
    return <div className="text-sm text-gray-500">Loading sync status...</div>
  }

  const getStatusIcon = () => {
    if (syncStatus.is_syncing) {
      return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
    }
    if (syncStatus.last_sync_status === 'success') {
      return <CheckCircle className="w-5 h-5 text-green-500" />
    }
    if (syncStatus.last_sync_status === 'error') {
      return <XCircle className="w-5 h-5 text-red-500" />
    }
    if (syncStatus.last_sync_status === 'partial') {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />
    }
    return <Clock className="w-5 h-5 text-gray-400" />
  }

  const getStatusText = () => {
    if (syncStatus.is_syncing) return 'Syncing...'
    if (syncStatus.last_sync_status === 'success') return 'Last sync successful'
    if (syncStatus.last_sync_status === 'error') return 'Last sync failed'
    if (syncStatus.last_sync_status === 'partial') return 'Last sync partially successful'
    return 'Not synced yet'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Sync Status</h3>
        <button
          onClick={() => triggerSync.mutate(undefined)}
          disabled={syncStatus.is_syncing || triggerSync.isPending}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${syncStatus.is_syncing ? 'animate-spin' : ''}`} />
          Sync Now
        </button>
      </div>

      <div className="space-y-4">
        {/* Current Status */}
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <div className="font-medium text-gray-900 dark:text-white">{getStatusText()}</div>
            {syncStatus.last_sync_message && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {syncStatus.last_sync_message}
              </div>
            )}
          </div>
        </div>

        {/* Sync Stats */}
        {(syncStatus.guests_synced !== undefined || syncStatus.rooms_synced !== undefined) && (
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            {syncStatus.guests_synced !== undefined && (
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {syncStatus.guests_synced}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Guests Synced</div>
              </div>
            )}
            {syncStatus.rooms_synced !== undefined && (
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {syncStatus.rooms_synced}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Rooms Synced</div>
              </div>
            )}
          </div>
        )}

        {/* Timestamps */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2 text-sm">
          {syncStatus.last_sync_at && (
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Last Sync:</span>
              <span>{formatDistanceToNow(new Date(syncStatus.last_sync_at), { addSuffix: true })}</span>
            </div>
          )}
          {syncStatus.next_sync_at && !syncStatus.is_syncing && (
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Next Sync:</span>
              <span>{formatDistanceToNow(new Date(syncStatus.next_sync_at), { addSuffix: true })}</span>
            </div>
          )}
        </div>

        {/* Errors */}
        {syncStatus.errors && syncStatus.errors.length > 0 && (
          <details className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <summary className="cursor-pointer text-sm font-medium text-red-600 dark:text-red-400">
              {syncStatus.errors.length} Error(s)
            </summary>
            <ul className="mt-2 space-y-1 text-sm text-red-600 dark:text-red-400 list-disc list-inside">
              {syncStatus.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  )
}
