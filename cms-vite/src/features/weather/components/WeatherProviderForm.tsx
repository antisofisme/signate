/**
 * Weather Provider Configuration Form
 *
 * Form for configuring weather API provider, API key, units, and cache settings
 */

import { Eye, EyeOff, TestTube, Save } from 'lucide-react';
import {
  WEATHER_PROVIDERS,
  TEMPERATURE_UNITS,
  SPEED_UNITS,
  PRESSURE_UNITS,
  type WeatherProvider,
  type WeatherUnits,
} from '../types/weather.types';

interface WeatherProviderFormProps {
  provider: WeatherProvider;
  apiKey: string;
  units: WeatherUnits;
  cacheDuration: number;
  showApiKey: boolean;
  onProviderChange: (provider: WeatherProvider) => void;
  onApiKeyChange: (apiKey: string) => void;
  onUnitsChange: (units: WeatherUnits) => void;
  onCacheDurationChange: (duration: number) => void;
  onShowApiKeyToggle: () => void;
  onSave: () => void;
  onTest: () => void;
  isSaving: boolean;
  isTesting: boolean;
}

export function WeatherProviderForm({
  provider,
  apiKey,
  units,
  cacheDuration,
  showApiKey,
  onProviderChange,
  onApiKeyChange,
  onUnitsChange,
  onCacheDurationChange,
  onShowApiKeyToggle,
  onSave,
  onTest,
  isSaving,
  isTesting,
}: WeatherProviderFormProps) {
  const selectedProvider = WEATHER_PROVIDERS.find((p) => p.id === provider);

  return (
    <div className="max-w-3xl space-y-6">
      {/* Provider Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Weather API Provider</h3>

        <select
          value={provider}
          onChange={(e) => onProviderChange(e.target.value as WeatherProvider)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
        >
          {WEATHER_PROVIDERS.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        {selectedProvider && (
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">{selectedProvider.name}</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {selectedProvider.description}
            </p>
            <div className="flex flex-wrap gap-2 mb-2">
              {selectedProvider.features.map((f) => (
                <span key={f} className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded">
                  {f}
                </span>
              ))}
            </div>
            {selectedProvider.free_tier && (
              <p className="text-sm text-green-600 dark:text-green-400">
                ✓ Free tier: {selectedProvider.free_tier_limit}
              </p>
            )}
            {selectedProvider.signup_url && (
              <a
                href={selectedProvider.signup_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline inline-block mt-2"
              >
                Get API Key →
              </a>
            )}
          </div>
        )}
      </div>

      {/* API Key */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">API Key</h3>
        <div className="relative">
          <input
            type={showApiKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="Enter your API key"
            className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <button
            type="button"
            onClick={onShowApiKeyToggle}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400"
          >
            {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Units */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Units</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Temperature</label>
            <select
              value={units.temperature}
              onChange={(e) => onUnitsChange({ ...units, temperature: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {TEMPERATURE_UNITS.map((u) => (
                <option key={u.value} value={u.value}>
                  {u.label} ({u.symbol})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Wind Speed</label>
            <select
              value={units.speed}
              onChange={(e) => onUnitsChange({ ...units, speed: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {SPEED_UNITS.map((u) => (
                <option key={u.value} value={u.value}>
                  {u.label} ({u.symbol})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Pressure</label>
            <select
              value={units.pressure}
              onChange={(e) => onUnitsChange({ ...units, pressure: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {PRESSURE_UNITS.map((u) => (
                <option key={u.value} value={u.value}>
                  {u.label} ({u.symbol})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Cache Duration */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cache Settings</h3>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Cache Duration (minutes)
        </label>
        <input
          type="number"
          value={cacheDuration}
          onChange={(e) => onCacheDurationChange(parseInt(e.target.value))}
          min={1}
          max={1440}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          How long to cache weather data before fetching new data
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onTest}
          disabled={!apiKey || isTesting}
          className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <TestTube className="w-5 h-5" />
          {isTesting ? 'Testing...' : 'Test API'}
        </button>
        <button
          onClick={onSave}
          disabled={!apiKey || isSaving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-5 h-5" />
          {isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
}

export default WeatherProviderForm;
