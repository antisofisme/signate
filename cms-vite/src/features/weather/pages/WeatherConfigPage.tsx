/**
 * Weather Configuration Page
 *
 * Configure weather service integration - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from '@/shared/utils/toast';
import { PageHeader, AccessDenied, PageSkeleton } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import {
  useWeatherConfig,
  useCreateWeatherConfig,
  useUpdateWeatherConfig,
  useTestWeatherAPI,
  useWeatherLocations,
  useCreateLocation,
  useDeleteLocation,
  useWeatherData,
  useSearchLocations,
} from '../hooks/useWeather';
import { WeatherProviderForm } from '../components/WeatherProviderForm';
import { LocationManager } from '../components/LocationManager';
import { WeatherPreview } from '../components/WeatherPreview';
import type {
  WeatherProvider,
  WeatherUnits,
} from '../types/weather.types';

export default function WeatherConfigPage() {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canView, isLoading: isCheckingPermission } = useCanPerformAction('settings', 'read');
  const { hasPermission: canUpdate } = useCanPerformAction('settings', 'edit');

  // Show loading state while checking permissions
  if (isCheckingPermission) {
    return <PageSkeleton />;
  }

  // Show access denied if no read permission
  if (!canView) {
    return <AccessDenied />;
  }

  const { data: config, isLoading } = useWeatherConfig();
  const { data: locations } = useWeatherLocations();
  const createConfig = useCreateWeatherConfig();
  const updateConfig = useUpdateWeatherConfig();
  const testAPI = useTestWeatherAPI();
  const createLocation = useCreateLocation();
  const deleteLocation = useDeleteLocation();

  const [activeTab, setActiveTab] = useState<'config' | 'locations' | 'preview'>('config');
  const [provider, setProvider] = useState<WeatherProvider>(config?.provider || 'openweathermap');
  const [apiKey, setApiKey] = useState(config?.api_key || '');
  const [showApiKey, setShowApiKey] = useState(false);
  const [units, setUnits] = useState<WeatherUnits>(
    config?.units || { temperature: 'celsius', speed: 'kmh', pressure: 'hpa' }
  );
  const [cacheDuration, setCacheDuration] = useState(config?.cache_duration_minutes || 10);

  // Location search
  const [locationSearch, setLocationSearch] = useState('');
  const { data: searchResults } = useSearchLocations(locationSearch);

  // Preview location
  const [previewLocationId, setPreviewLocationId] = useState<number | null>(null);
  const { data: weatherData } = useWeatherData(previewLocationId || 0);

  const handleSave = () => {
    const data = {
      provider,
      api_key: apiKey,
      units,
      cache_duration_minutes: cacheDuration,
    };

    if (config) {
      updateConfig.mutate(data);
    } else {
      createConfig.mutate(data);
    }
  };

  const handleTest = () => {
    const defaultLocation = locations?.find((loc) => loc.is_default);
    if (!defaultLocation) {
      toast.warning('Please add a default location first');
      return;
    }

    testAPI.mutate({
      provider,
      api_key: apiKey,
      latitude: defaultLocation.latitude,
      longitude: defaultLocation.longitude,
    });
  };

  const handleAddLocation = (result: any) => {
    createLocation.mutate({
      name: result.name,
      latitude: result.latitude,
      longitude: result.longitude,
      city: result.name,
      country: result.country,
      is_default: !locations || locations.length === 0,
    });
    setLocationSearch('');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 dark:text-gray-400">{t('weather.loading', 'Loading weather configuration...')}</div>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title={t('weather.title', 'Weather Service')}
        description={t('weather.subtitle', 'Configure weather API integration for digital signage')}
      />

      <div className="space-y-6">
        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'config'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            {t('weather.tabs.config', 'Configuration')}
          </button>
          <button
            onClick={() => setActiveTab('locations')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'locations'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            {t('weather.tabs.locations', 'Locations')}
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
            {t('weather.tabs.preview', 'Preview')}
          </button>
        </div>

        {/* Config Tab */}
        {activeTab === 'config' && (
        <WeatherProviderForm
          provider={provider}
          apiKey={apiKey}
          units={units}
          cacheDuration={cacheDuration}
          showApiKey={showApiKey}
          onProviderChange={setProvider}
          onApiKeyChange={setApiKey}
          onUnitsChange={setUnits}
          onCacheDurationChange={setCacheDuration}
          onShowApiKeyToggle={() => setShowApiKey(!showApiKey)}
          onSave={handleSave}
          onTest={handleTest}
          isSaving={createConfig.isPending || updateConfig.isPending}
          isTesting={testAPI.isPending}
        />
      )}

        {/* Locations Tab */}
        {activeTab === 'locations' && (
          <LocationManager
            locations={locations.filter(loc => loc.id !== undefined) as any}
            searchQuery={locationSearch}
            searchResults={searchResults}
            onSearchChange={setLocationSearch}
            onAddLocation={handleAddLocation}
            onDeleteLocation={(id) => deleteLocation.mutate(id)}
            isSearching={false}
          />
        )}

        {/* Preview Tab */}
        {activeTab === 'preview' && (
          <WeatherPreview
            locations={locations.filter(loc => loc.id !== undefined) as any}
            selectedLocationId={previewLocationId}
            weatherData={weatherData}
            onLocationSelect={setPreviewLocationId}
            isLoading={false}
          />
        )}
      </div>
    </>
  );
}
