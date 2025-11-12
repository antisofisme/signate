/**
 * Weather Configuration Page
 *
 * Configure weather service integration
 */

import { useState } from 'react'
import { Cloud, Save, Trash2, Plus, MapPin, Eye, EyeOff, TestTube, Thermometer } from 'lucide-react'
import { PageHeader } from '@/shared/components'
import {
  useWeatherConfig,
  useCreateWeatherConfig,
  useUpdateWeatherConfig,
  useDeleteWeatherConfig,
  useTestWeatherAPI,
  useWeatherLocations,
  useCreateLocation,
  useDeleteLocation,
  useWeatherData,
  useSearchLocations,
} from '../hooks/useWeather'
import {
  WEATHER_PROVIDERS,
  TEMPERATURE_UNITS,
  SPEED_UNITS,
  PRESSURE_UNITS,
  type WeatherProvider,
  type WeatherUnits,
} from '../types/weather.types'

export default function WeatherConfigPage() {
  const { data: config, isLoading } = useWeatherConfig()
  const { data: locations } = useWeatherLocations()
  const createConfig = useCreateWeatherConfig()
  const updateConfig = useUpdateWeatherConfig()
  const deleteConfig = useDeleteWeatherConfig()
  const testAPI = useTestWeatherAPI()
  const createLocation = useCreateLocation()
  const deleteLocation = useDeleteLocation()

  const [activeTab, setActiveTab] = useState<'config' | 'locations' | 'preview'>('config')
  const [provider, setProvider] = useState<WeatherProvider>(config?.provider || 'openweathermap')
  const [apiKey, setApiKey] = useState(config?.api_key || '')
  const [showApiKey, setShowApiKey] = useState(false)
  const [units, setUnits] = useState<WeatherUnits>(
    config?.units || { temperature: 'celsius', speed: 'kmh', pressure: 'hpa' }
  )
  const [cacheDuration, setCacheDuration] = useState(config?.cache_duration_minutes || 10)

  // Location search
  const [locationSearch, setLocationSearch] = useState('')
  const { data: searchResults } = useSearchLocations(locationSearch)

  // Preview location
  const [previewLocationId, setPreviewLocationId] = useState<number | null>(null)
  const { data: weatherData } = useWeatherData(previewLocationId || 0)

  const selectedProvider = WEATHER_PROVIDERS.find((p) => p.id === provider)

  const handleSave = () => {
    const data = {
      provider,
      api_key: apiKey,
      units,
      cache_duration_minutes: cacheDuration,
    }

    if (config) {
      updateConfig.mutate(data)
    } else {
      createConfig.mutate(data)
    }
  }

  const handleTest = () => {
    const defaultLocation = locations?.find((loc) => loc.is_default)
    if (!defaultLocation) {
      alert('Please add a default location first')
      return
    }

    testAPI.mutate({
      provider,
      api_key: apiKey,
      latitude: defaultLocation.latitude,
      longitude: defaultLocation.longitude,
    })
  }

  const handleAddLocation = (result: any) => {
    createLocation.mutate({
      name: result.name,
      latitude: result.latitude,
      longitude: result.longitude,
      city: result.name,
      country: result.country,
      is_default: !locations || locations.length === 0,
    })
    setLocationSearch('')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading weather configuration...</div>
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Weather Service"
        description="Configure weather API integration for digital signage"
      />

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('config')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'config'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
              : 'text-gray-600 dark:text-gray-400'
          }`}
        >
          Configuration
        </button>
        <button
          onClick={() => setActiveTab('locations')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'locations'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
              : 'text-gray-600 dark:text-gray-400'
          }`}
        >
          Locations
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'preview'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
              : 'text-gray-600 dark:text-gray-400'
          }`}
          disabled={!locations || locations.length === 0}
        >
          Preview
        </button>
      </div>

      {/* Config Tab */}
      {activeTab === 'config' && (
        <div className="max-w-3xl space-y-6">
          {/* Provider Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Weather API Provider</h3>

            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as WeatherProvider)}
              className="w-full px-4 py-2 border rounded-lg mb-4"
            >
              {WEATHER_PROVIDERS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            {selectedProvider && (
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                <h4 className="font-medium mb-2">{selectedProvider.name}</h4>
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
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">API Key</h3>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-4 py-2 pr-10 border rounded-lg"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Units */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Units</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Temperature</label>
                <select
                  value={units.temperature}
                  onChange={(e) => setUnits({ ...units, temperature: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {TEMPERATURE_UNITS.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.label} ({u.symbol})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Wind Speed</label>
                <select
                  value={units.speed}
                  onChange={(e) => setUnits({ ...units, speed: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {SPEED_UNITS.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.symbol}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Pressure</label>
                <select
                  value={units.pressure}
                  onChange={(e) => setUnits({ ...units, pressure: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {PRESSURE_UNITS.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.symbol}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Cache Duration */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Cache Duration</h3>
            <input
              type="number"
              value={cacheDuration}
              onChange={(e) => setCacheDuration(Number(e.target.value))}
              min="5"
              max="60"
              className="w-full px-4 py-2 border rounded-lg"
            />
            <p className="text-sm text-gray-500 mt-2">
              Weather data will be cached for {cacheDuration} minutes
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleTest}
              disabled={!apiKey || testAPI.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
            >
              <TestTube className="w-5 h-5" />
              Test API
            </button>
            <button
              onClick={handleSave}
              disabled={!apiKey || createConfig.isPending || updateConfig.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
            >
              <Save className="w-5 h-5" />
              {config ? 'Update' : 'Save'}
            </button>
            {config && (
              <button
                onClick={() => {
                  if (confirm('Delete weather configuration?')) deleteConfig.mutate()
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
              >
                <Trash2 className="w-5 h-5" />
                Delete
              </button>
            )}
          </div>
        </div>
      )}

      {/* Locations Tab */}
      {activeTab === 'locations' && (
        <div className="max-w-4xl space-y-6">
          {/* Add Location */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Add Location</h3>
            <input
              type="text"
              value={locationSearch}
              onChange={(e) => setLocationSearch(e.target.value)}
              placeholder="Search for city..."
              className="w-full px-4 py-2 border rounded-lg mb-4"
            />
            {searchResults && searchResults.length > 0 && (
              <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
                {searchResults.map((result, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAddLocation(result)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <div className="font-medium">{result.display_name}</div>
                    <div className="text-sm text-gray-500">
                      {result.latitude.toFixed(4)}, {result.longitude.toFixed(4)}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Locations List */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Saved Locations</h3>
            </div>
            <div className="divide-y">
              {locations && locations.length > 0 ? (
                locations.map((location) => (
                  <div key={location.id} className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <MapPin className="w-5 h-5 text-blue-500" />
                      <div>
                        <div className="font-medium">{location.name}</div>
                        <div className="text-sm text-gray-500">
                          {location.city}, {location.country}
                        </div>
                        <div className="text-xs text-gray-400">
                          {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                        </div>
                      </div>
                      {location.is_default && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                          Default
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        if (confirm('Delete this location?')) deleteLocation.mutate(location.id!)
                      }}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center text-gray-500">
                  No locations added yet
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Preview Tab */}
      {activeTab === 'preview' && locations && locations.length > 0 && (
        <div className="max-w-4xl space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4">Select Location</h3>
            <select
              value={previewLocationId || ''}
              onChange={(e) => setPreviewLocationId(Number(e.target.value))}
              className="w-full px-4 py-2 border rounded-lg"
            >
              <option value="">Choose a location...</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          {weatherData && (
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-8 text-white">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-3xl font-bold">{weatherData.location.name}</h2>
                  <p className="text-blue-100">{weatherData.location.country}</p>
                </div>
                <Thermometer className="w-12 h-12" />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="text-4xl font-bold">{weatherData.current.temperature}°</div>
                  <div className="text-blue-100">Temperature</div>
                </div>
                <div>
                  <div className="text-4xl font-bold">{weatherData.current.humidity}%</div>
                  <div className="text-blue-100">Humidity</div>
                </div>
                <div>
                  <div className="text-4xl font-bold">{weatherData.current.wind_speed}</div>
                  <div className="text-blue-100">Wind Speed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{weatherData.current.condition}</div>
                  <div className="text-blue-100">Condition</div>
                </div>
              </div>

              {weatherData.forecast && weatherData.forecast.length > 0 && (
                <div className="mt-8 pt-8 border-t border-blue-400">
                  <h3 className="text-xl font-semibold mb-4">7-Day Forecast</h3>
                  <div className="grid grid-cols-7 gap-2">
                    {weatherData.forecast.map((day, idx) => (
                      <div key={idx} className="text-center">
                        <div className="text-sm">{day.day_of_week}</div>
                        <div className="text-lg font-bold">{day.temperature_max}°</div>
                        <div className="text-sm text-blue-200">{day.temperature_min}°</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}
