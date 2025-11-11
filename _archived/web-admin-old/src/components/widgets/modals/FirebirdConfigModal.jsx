import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Database, Server, Eye, EyeOff, Save, Loader, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { firebirdAPI } from '../../../services/api'
import { showToast } from '../../../utils/toast'
import { Modal, Button, FormInput } from '../../shared'

/**
 * FirebirdConfigModal Component
 * Modal for creating/editing Firebird database configuration
 *
 * Features:
 * - Create new or edit existing Firebird configuration
 * - Conditional fields based on connection mode (Server/Embedded)
 * - Password visibility toggle
 * - Test connection before saving
 * - Real-time validation
 * - Connection status indicator
 *
 * @param {Object} config - Existing configuration object (null for create mode)
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSuccess - Callback after successful save
 */
export default function FirebirdConfigModal({ config, onClose, onSuccess }) {
  const isEditMode = !!config

  const [formData, setFormData] = useState({
    config_key: config?.config_key || '',
    connection_mode: config?.connection_mode || 'server',
    database_host: config?.database_host || 'localhost',
    database_port: config?.database_port || 3050,
    database_path: config?.database_path || '',
    database_user: config?.database_user || 'SYSDBA',
    database_password: config?.database_password || '',
    refresh_interval: config?.refresh_interval || 300,
    is_active: config?.is_active !== undefined ? config.is_active : true,
    notes: config?.notes || '',
  })

  const [showPassword, setShowPassword] = useState(false)
  const [testStatus, setTestStatus] = useState(null) // 'testing', 'success', 'error', null
  const [testMessage, setTestMessage] = useState('')
  const [errors, setErrors] = useState({})

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (data) => {
      if (isEditMode) {
        return firebirdAPI.updateConfig(config.id, data)
      } else {
        return firebirdAPI.createConfig(data)
      }
    },
    onSuccess: () => {
      showToast.success(
        isEditMode
          ? 'Firebird configuration updated successfully!'
          : 'Firebird configuration created successfully!'
      )
      onSuccess?.()
      onClose()
    },
    onError: (error) => {
      showToast.error(
        error.response?.data?.detail || 'Failed to save configuration'
      )
    },
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: (data) => {
      // If editing, test with ID. If creating, send data to test endpoint
      if (isEditMode) {
        return firebirdAPI.testConnection(config.id)
      } else {
        // For new configs, we need a different endpoint or pass data directly
        return firebirdAPI.createConfig({ ...data, test_only: true })
      }
    },
    onSuccess: (response) => {
      setTestStatus('success')
      setTestMessage(response.data?.message || 'Connection successful!')
      showToast.success('Connection test successful!')
    },
    onError: (error) => {
      setTestStatus('error')
      setTestMessage(
        error.response?.data?.detail || 'Connection failed. Please check your settings.'
      )
      showToast.error('Connection test failed')
    },
  })

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
    // Reset test status when critical fields change
    if (['database_host', 'database_port', 'database_path', 'database_user', 'database_password', 'connection_mode'].includes(field)) {
      setTestStatus(null)
      setTestMessage('')
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.config_key.trim()) {
      newErrors.config_key = 'Configuration name is required'
    }

    if (!formData.database_path.trim()) {
      newErrors.database_path = 'Database path is required'
    }

    if (formData.connection_mode === 'server') {
      if (!formData.database_host.trim()) {
        newErrors.database_host = 'Database host is required for server mode'
      }
      if (!formData.database_port || formData.database_port < 1 || formData.database_port > 65535) {
        newErrors.database_port = 'Valid port number is required (1-65535)'
      }
    }

    if (!formData.database_user.trim()) {
      newErrors.database_user = 'Database user is required'
    }

    if (!formData.database_password.trim()) {
      newErrors.database_password = 'Database password is required'
    }

    if (!formData.refresh_interval || formData.refresh_interval < 10) {
      newErrors.refresh_interval = 'Refresh interval must be at least 10 seconds'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleTestConnection = () => {
    if (!validateForm()) {
      showToast.warning('Please fix validation errors before testing connection')
      return
    }

    setTestStatus('testing')
    setTestMessage('Testing connection...')
    testConnectionMutation.mutate(formData)
  }

  const handleSave = () => {
    if (!validateForm()) {
      showToast.warning('Please fix validation errors')
      return
    }

    saveMutation.mutate(formData)
  }

  const isServerMode = formData.connection_mode === 'server'

  // Footer with split layout (Test Connection on left, Cancel/Save on right)
  const footer = (
    <div className="flex justify-between gap-3">
      {/* Left side - Test Connection */}
      <Button
        onClick={handleTestConnection}
        disabled={testConnectionMutation.isLoading || saveMutation.isLoading}
        variant="outline"
        leftIcon={testStatus === 'testing' ? <Loader className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
      >
        {testStatus === 'testing' ? 'Testing...' : 'Test Connection'}
      </Button>

      {/* Right side - Cancel and Save */}
      <div className="flex gap-3">
        <Button
          onClick={onClose}
          variant="secondary"
          disabled={saveMutation.isLoading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={saveMutation.isLoading}
          variant="primary"
          leftIcon={saveMutation.isLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        >
          {saveMutation.isLoading ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="3xl"
      bodyClassName="flex-1 overflow-y-auto p-6"
      footer={footer}
    >
      {/* Header */}
      <div className="flex items-center mb-6">
        <Database className="w-6 h-6 text-blue-600 dark:text-blue-400 mr-3" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isEditMode ? 'Edit Firebird Configuration' : 'New Firebird Configuration'}
        </h2>
      </div>

      {/* Form */}
      <div className="space-y-6">
        {/* Basic Information Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Server className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
            Basic Information
          </h3>
          <div className="space-y-4 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            {/* Config Key/Name */}
            <FormInput
              label="Configuration Name"
              type="text"
              value={formData.config_key}
              onChange={(e) => handleChange('config_key', e.target.value)}
              placeholder="e.g., hotel_pms_main"
              required
              error={errors.config_key}
              description="Unique identifier for this configuration"
              disabled={isEditMode} // Don't allow changing key in edit mode
            />

            {/* Connection Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Connection Mode <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => handleChange('connection_mode', 'server')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                    formData.connection_mode === 'server'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-400'
                  }`}
                >
                  <Server className="w-5 h-5 mx-auto mb-1" />
                  Server Mode
                </button>
                <button
                  type="button"
                  onClick={() => handleChange('connection_mode', 'embedded')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                    formData.connection_mode === 'embedded'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-400'
                  }`}
                >
                  <Database className="w-5 h-5 mx-auto mb-1" />
                  Embedded Mode
                </button>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Server mode connects to remote Firebird server. Embedded mode for local database files.
              </p>
            </div>

            {/* Is Active Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <div className="flex items-center space-x-4">
                <button
                  type="button"
                  onClick={() => handleChange('is_active', true)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    formData.is_active
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  <CheckCircle className="w-4 h-4 inline mr-2" />
                  Active
                </button>
                <button
                  type="button"
                  onClick={() => handleChange('is_active', false)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    !formData.is_active
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  <XCircle className="w-4 h-4 inline mr-2" />
                  Inactive
                </button>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Only active configurations will be used for data fetching
              </p>
            </div>
          </div>
        </div>

        {/* Connection Settings Section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
            Connection Settings
          </h3>
          <div className="space-y-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
            {/* Database Host - Only for Server Mode */}
            {isServerMode && (
              <FormInput
                label="Database Host"
                type="text"
                value={formData.database_host}
                onChange={(e) => handleChange('database_host', e.target.value)}
                placeholder="localhost or IP address"
                required
                error={errors.database_host}
                description="Hostname or IP address of Firebird server"
              />
            )}

            {/* Database Port - Only for Server Mode */}
            {isServerMode && (
              <FormInput
                label="Database Port"
                type="number"
                value={formData.database_port}
                onChange={(e) => handleChange('database_port', parseInt(e.target.value) || 3050)}
                placeholder="3050"
                required
                error={errors.database_port}
                description="Port number (default: 3050)"
              />
            )}

            {/* Database Path */}
            <FormInput
              label="Database Path"
              type="text"
              value={formData.database_path}
              onChange={(e) => handleChange('database_path', e.target.value)}
              placeholder={isServerMode ? '/path/to/database.fdb' : 'C:\\data\\database.fdb'}
              required
              error={errors.database_path}
              description={isServerMode
                ? 'Path to database file on the server'
                : 'Full path to local database file'}
            />

            {/* Database User */}
            <FormInput
              label="Database User"
              type="text"
              value={formData.database_user}
              onChange={(e) => handleChange('database_user', e.target.value)}
              placeholder="SYSDBA"
              required
              error={errors.database_user}
              description="Database username (default: SYSDBA)"
            />

            {/* Database Password with Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Database Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.database_password}
                  onChange={(e) => handleChange('database_password', e.target.value)}
                  placeholder="Enter password"
                  className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 ${
                    errors.database_password
                      ? 'border-red-500 dark:border-red-500'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.database_password && (
                <p className="text-xs text-red-500 dark:text-red-400 mt-1">{errors.database_password}</p>
              )}
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Password will be encrypted and stored securely
              </p>
            </div>

            {/* Refresh Interval */}
            <FormInput
              label="Refresh Interval (seconds)"
              type="number"
              value={formData.refresh_interval}
              onChange={(e) => handleChange('refresh_interval', parseInt(e.target.value) || 300)}
              placeholder="300"
              required
              error={errors.refresh_interval}
              description="How often to fetch data from database (minimum: 10 seconds)"
            />
          </div>
        </div>

        {/* Notes Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Notes (Optional)
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
            placeholder="Add any notes or description about this configuration..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none"
          />
        </div>

        {/* Test Connection Status */}
        {testStatus && (
          <div
            className={`p-4 rounded-lg border-2 flex items-start gap-3 ${
              testStatus === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 border-green-500'
                : testStatus === 'error'
                ? 'bg-red-50 dark:bg-red-900/20 border-red-500'
                : 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
            }`}
          >
            {testStatus === 'testing' && <Loader className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0 mt-0.5" />}
            {testStatus === 'success' && <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />}
            {testStatus === 'error' && <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
            <div>
              <p
                className={`font-medium ${
                  testStatus === 'success'
                    ? 'text-green-800 dark:text-green-300'
                    : testStatus === 'error'
                    ? 'text-red-800 dark:text-red-300'
                    : 'text-blue-800 dark:text-blue-300'
                }`}
              >
                {testStatus === 'testing' && 'Testing Connection...'}
                {testStatus === 'success' && 'Connection Successful!'}
                {testStatus === 'error' && 'Connection Failed'}
              </p>
              <p
                className={`text-sm mt-1 ${
                  testStatus === 'success'
                    ? 'text-green-700 dark:text-green-400'
                    : testStatus === 'error'
                    ? 'text-red-700 dark:text-red-400'
                    : 'text-blue-700 dark:text-blue-400'
                }`}
              >
                {testMessage}
              </p>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
