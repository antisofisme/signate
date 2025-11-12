/**
 * PMS Provider Select Component
 *
 * Dropdown to select PMS provider
 */

import { Building2 } from 'lucide-react'
import { PMS_PROVIDERS, type PMSProvider } from '../types/pms.types'

interface PMSProviderSelectProps {
  value: PMSProvider
  onChange: (provider: PMSProvider) => void
  disabled?: boolean
}

export function PMSProviderSelect({ value, onChange, disabled }: PMSProviderSelectProps) {
  const selectedProvider = PMS_PROVIDERS.find((p) => p.id === value)

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
        PMS Provider
      </label>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value as PMSProvider)}
        disabled={disabled}
        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
      >
        {PMS_PROVIDERS.map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.name}
          </option>
        ))}
      </select>

      {selectedProvider && (
        <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                {selectedProvider.name}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {selectedProvider.description}
              </p>

              <div className="flex flex-wrap gap-2 mb-2">
                {selectedProvider.features.map((feature) => (
                  <span
                    key={feature}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 rounded"
                  >
                    {feature}
                  </span>
                ))}
              </div>

              <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                <div>Connection: {selectedProvider.connection_type.toUpperCase()}</div>
                {selectedProvider.requires_api_key && (
                  <div>• Requires API Key</div>
                )}
                {selectedProvider.requires_credentials && (
                  <div>• Requires Username & Password</div>
                )}
              </div>

              {selectedProvider.documentation_url && (
                <a
                  href={selectedProvider.documentation_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  View Documentation →
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
