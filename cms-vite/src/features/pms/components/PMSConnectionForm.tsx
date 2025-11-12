/**
 * PMS Connection Form Component
 *
 * Form to configure PMS connection settings
 */

import { useState } from 'react'
import { Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { useTestPMSConnection } from '../hooks/usePMS'
import type { PMSConnectionConfig, PMSProvider } from '../types/pms.types'

interface PMSConnectionFormProps {
  provider: PMSProvider
  config: PMSConnectionConfig
  onChange: (config: PMSConnectionConfig) => void
  disabled?: boolean
}

export function PMSConnectionForm({
  provider,
  config,
  onChange,
  disabled,
}: PMSConnectionFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const testConnection = useTestPMSConnection()

  const handleChange = (field: keyof PMSConnectionConfig, value: any) => {
    onChange({ ...config, [field]: value })
  }

  const handleTest = () => {
    testConnection.mutate({ provider, connection_config: config })
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Connection Settings
      </h3>

      {/* Host */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Host / URL
        </label>
        <input
          type="text"
          value={config.host}
          onChange={(e) => handleChange('host', e.target.value)}
          placeholder="api.pms-provider.com"
          disabled={disabled}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        />
      </div>

      {/* Protocol & Port */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Protocol
          </label>
          <select
            value={config.protocol}
            onChange={(e) => handleChange('protocol', e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          >
            <option value="https">HTTPS</option>
            <option value="http">HTTP</option>
            <option value="tcp">TCP</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Port
          </label>
          <input
            type="number"
            value={config.port}
            onChange={(e) => handleChange('port', parseInt(e.target.value) || 0)}
            placeholder="443"
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
        </div>
      </div>

      {/* Username */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Username (Optional)
        </label>
        <input
          type="text"
          value={config.username || ''}
          onChange={(e) => handleChange('username', e.target.value)}
          placeholder="pms_user"
          disabled={disabled}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        />
      </div>

      {/* Password */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Password (Optional)
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            value={config.password || ''}
            onChange={(e) => handleChange('password', e.target.value)}
            placeholder="••••••••"
            disabled={disabled}
            className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* API Key */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          API Key (Optional)
        </label>
        <div className="relative">
          <input
            type={showApiKey ? 'text' : 'password'}
            value={config.api_key || ''}
            onChange={(e) => handleChange('api_key', e.target.value)}
            placeholder="••••••••••••••••"
            disabled={disabled}
            className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Advanced Settings */}
      <details className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <summary className="cursor-pointer font-medium text-gray-900 dark:text-white">
          Advanced Settings
        </summary>
        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Timeout (seconds)
            </label>
            <input
              type="number"
              value={config.timeout || 30}
              onChange={(e) => handleChange('timeout', parseInt(e.target.value) || 30)}
              disabled={disabled}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Retry Attempts
            </label>
            <input
              type="number"
              value={config.retry_attempts || 3}
              onChange={(e) => handleChange('retry_attempts', parseInt(e.target.value) || 3)}
              disabled={disabled}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="ssl_verify"
              checked={config.ssl_verify !== false}
              onChange={(e) => handleChange('ssl_verify', e.target.checked)}
              disabled={disabled}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label
              htmlFor="ssl_verify"
              className="text-sm text-gray-700 dark:text-gray-300"
            >
              Verify SSL Certificate
            </label>
          </div>
        </div>
      </details>

      {/* Test Connection Button */}
      <div className="flex items-center gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={handleTest}
          disabled={disabled || testConnection.isPending || !config.host}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testConnection.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Testing...
            </>
          ) : (
            <>Test Connection</>
          )}
        </button>

        {testConnection.data && (
          <div className="flex items-center gap-2">
            {testConnection.data.success ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm text-green-600 dark:text-green-400">
                  Connection successful ({testConnection.data.response_time_ms}ms)
                </span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-sm text-red-600 dark:text-red-400">
                  {testConnection.data.message}
                </span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
