import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { settingsAPI } from '../../services/api'
import { Download, Upload, Trash2, HardDrive, Server, Clock, Package } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button } from '../shared'
import { formatFileSize } from '../../utils/helpers'

/**
 * SystemTab Component
 * System maintenance and information
 *
 * Features:
 * - Database backup/restore
 * - Clear cache
 * - System information
 * - Storage usage
 * - Version information
 */
export default function SystemTab() {
  const [processing, setProcessing] = useState(false)

  // Fetch system info
  const { data: systemInfo, isLoading } = useQuery({
    queryKey: ['system', 'info'],
    queryFn: () => settingsAPI.getSystemInfo().then(res => res.data),
  })

  // Backup database mutation
  const backupMutation = useMutation({
    mutationFn: settingsAPI.backupDatabase,
    onSuccess: (response) => {
      showToast.success('Database backup created successfully!')
      // Download backup file
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `signage-backup-${new Date().toISOString().split('T')[0]}.sql`
      document.body.appendChild(link)
      link.click()
      link.remove()
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Backup failed')
    }
  })

  // Clear cache mutation
  const clearCacheMutation = useMutation({
    mutationFn: settingsAPI.clearCache,
    onSuccess: () => {
      showToast.success('Cache cleared successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to clear cache')
    }
  })

  const handleBackup = () => {
    if (confirm('Create database backup?\n\nThis may take a few minutes for large databases.')) {
      backupMutation.mutate()
    }
  }

  const handleClearCache = () => {
    if (confirm('Clear system cache?\n\nThis will temporarily slow down the system while cache rebuilds.')) {
      clearCacheMutation.mutate()
    }
  }

  return (
    <div className="space-y-6">
      {/* System Information */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Version */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-2">
              <Package className="w-5 h-5 text-blue-600" />
              <p className="font-medium text-gray-800 dark:text-gray-100">Version</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{systemInfo?.version || 'v1.0.0'}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Digital Signage System</p>
          </div>

          {/* Uptime */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-5 h-5 text-green-600" />
              <p className="font-medium text-gray-800 dark:text-gray-100">Uptime</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemInfo?.uptime_hours ? `${Math.floor(systemInfo.uptime_hours / 24)}d ${systemInfo.uptime_hours % 24}h` : 'N/A'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">System running</p>
          </div>

          {/* Database Size */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-2">
              <HardDrive className="w-5 h-5 text-purple-600" />
              <p className="font-medium text-gray-800 dark:text-gray-100">Database Size</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemInfo?.database_size ? formatFileSize(systemInfo.database_size) : 'N/A'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Total database storage</p>
          </div>

          {/* Storage Used */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-2">
              <Server className="w-5 h-5 text-orange-600" />
              <p className="font-medium text-gray-800 dark:text-gray-100">Media Storage</p>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemInfo?.media_storage_used ? formatFileSize(systemInfo.media_storage_used) : 'N/A'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Content files storage</p>
          </div>
        </div>
      </div>

      {/* Database Management */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Database Management</h3>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
          {/* Backup */}
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800 dark:text-gray-100">Backup Database</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Download complete database backup (SQL dump)</p>
            </div>
            <Button
              variant="primary"
              leftIcon={<Download className="w-4 h-4" />}
              onClick={handleBackup}
              disabled={backupMutation.isLoading}
            >
              {backupMutation.isLoading ? 'Creating...' : 'Create Backup'}
            </Button>
          </div>

          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-800 dark:text-gray-100">Restore Database</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Restore from backup file (SQL dump)</p>
              </div>
              <Button
                variant="secondary"
                leftIcon={<Upload className="w-4 h-4" />}
                disabled
                title="Feature coming soon"
              >
                Restore
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Cache Management */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Cache Management</h3>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800 dark:text-gray-100">Clear System Cache</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Clear cached data to free up memory and resolve issues</p>
              <p className="text-xs text-orange-600 mt-1">⚠️ This will temporarily slow down the system</p>
            </div>
            <Button
              variant="danger"
              leftIcon={<Trash2 className="w-4 h-4" />}
              onClick={handleClearCache}
              disabled={clearCacheMutation.isLoading}
            >
              {clearCacheMutation.isLoading ? 'Clearing...' : 'Clear Cache'}
            </Button>
          </div>
        </div>
      </div>

      {/* System Logs (Future Feature) */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">System Logs</h3>
        <div className="bg-gray-50 dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
          <Server className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 font-medium">System Logs Viewer</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">View and export system logs</p>
          <Button variant="secondary" disabled>
            Coming Soon
          </Button>
        </div>
      </div>
    </div>
  )
}
