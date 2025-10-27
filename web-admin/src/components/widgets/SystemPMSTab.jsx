import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { firebirdAPI } from '../../services/api'
import { Plus, Edit2, Trash2, Database, Server, TestTube, AlertCircle } from 'lucide-react'
import { showToast } from '../../utils/toast'
import { Button } from '../shared'
import FirebirdConfigModal from './modals/FirebirdConfigModal'
import FirebirdConnectionStatus, { FirebirdConnectionBadge } from './FirebirdConnectionStatus'

/**
 * SystemPMSTab Component
 * Manages Firebird database configurations for PMS integration
 *
 * Features:
 * - List all Firebird configurations
 * - Create new configuration
 * - Edit existing configuration
 * - Delete configuration with confirmation
 * - Test connection
 * - Real-time connection status
 */
export default function SystemPMSTab() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [selectedConfig, setSelectedConfig] = useState(null)
  const [expandedConfigId, setExpandedConfigId] = useState(null)

  // Fetch configurations
  const { data: configsData, isLoading } = useQuery({
    queryKey: ['firebird-configs'],
    queryFn: () => firebirdAPI.listConfigs().then(res => res.data),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: firebirdAPI.deleteConfig,
    onSuccess: () => {
      queryClient.invalidateQueries(['firebird-configs'])
      showToast.success('Configuration deleted successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete configuration')
    },
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: firebirdAPI.testConnection,
    onSuccess: (response, configId) => {
      showToast.success(`Connection test successful for config ID ${configId}!`)
      queryClient.invalidateQueries(['firebird-health', configId])
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Connection test failed')
    },
  })

  const handleCreate = () => {
    setSelectedConfig(null)
    setShowModal(true)
  }

  const handleEdit = (config) => {
    setSelectedConfig(config)
    setShowModal(true)
  }

  const handleDelete = (config) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete this configuration?\n\n` +
      `Name: ${config.config_key}\n` +
      `Database: ${config.database_path}\n\n` +
      `This action cannot be undone.`
    )

    if (confirmed) {
      deleteMutation.mutate(config.id)
    }
  }

  const handleTest = (configId) => {
    testConnectionMutation.mutate(configId)
  }

  const handleModalSuccess = () => {
    queryClient.invalidateQueries(['firebird-configs'])
  }

  const toggleExpand = (configId) => {
    setExpandedConfigId(expandedConfigId === configId ? null : configId)
  }

  const configs = configsData?.configs || []

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">SystemPMS Integration</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Manage Firebird database connections for Property Management System
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={handleCreate}
        >
          Add Configuration
        </Button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && configs.length === 0 && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
          <Database className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 font-medium">No Firebird Configurations</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Create your first Firebird database connection to start integrating PMS data
          </p>
          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={handleCreate}
          >
            Add Configuration
          </Button>
        </div>
      )}

      {/* Configurations List */}
      {!isLoading && configs.length > 0 && (
        <div className="space-y-4">
          {configs.map((config) => (
            <div
              key={config.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Card Header */}
              <div className="p-4">
                <div className="flex items-start justify-between">
                  {/* Left: Config Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                        {config.connection_mode === 'server' ? (
                          <Server className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        ) : (
                          <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        )}
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {config.config_key}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {config.connection_mode === 'server'
                            ? `${config.database_host}:${config.database_port}/${config.database_path}`
                            : config.database_path}
                        </p>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div className="flex items-center gap-2 mt-3">
                      <FirebirdConnectionBadge
                        status={config.is_active ? 'connected' : 'disconnected'}
                      />
                      {!config.is_active && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          (Configuration is inactive)
                        </span>
                      )}
                    </div>

                    {/* Notes (if any) */}
                    {config.notes && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 italic">
                        {config.notes}
                      </p>
                    )}
                  </div>

                  {/* Right: Action Buttons */}
                  <div className="flex gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTest(config.id)}
                      disabled={testConnectionMutation.isLoading}
                      title="Test connection"
                    >
                      <TestTube className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(config)}
                      title="Edit configuration"
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(config)}
                      disabled={deleteMutation.isLoading}
                      title="Delete configuration"
                    >
                      <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Expandable Connection Status */}
              {config.is_active && (
                <>
                  <div className="px-4 pb-4">
                    <button
                      onClick={() => toggleExpand(config.id)}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline focus:outline-none"
                    >
                      {expandedConfigId === config.id
                        ? '▲ Hide connection details'
                        : '▼ Show connection details'}
                    </button>
                  </div>

                  {/* Expanded Details */}
                  {expandedConfigId === config.id && (
                    <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
                      <FirebirdConnectionStatus
                        configId={config.id}
                        config={config}
                        autoRefresh={true}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Info Alert */}
      {!isLoading && configs.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">About Firebird Integration</p>
            <p>
              Active configurations will automatically fetch data from your Firebird database
              at the specified refresh interval. You can test connections manually or expand
              any configuration to see real-time connection status.
            </p>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showModal && (
        <FirebirdConfigModal
          config={selectedConfig}
          onClose={() => setShowModal(false)}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  )
}
