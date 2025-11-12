/**
 * Weather Preview Component
 *
 * Display weather data preview for selected location
 */

import { Thermometer, Cloud, MapPin } from 'lucide-react';

interface Location {
  id: number;
  name: string;
  city: string;
  country: string;
}

interface WeatherPreviewProps {
  locations?: Location[];
  selectedLocationId: number | null;
  weatherData?: any;
  onLocationSelect: (id: number) => void;
  isLoading: boolean;
}

export function WeatherPreview({
  locations,
  selectedLocationId,
  weatherData,
  onLocationSelect,
  isLoading,
}: WeatherPreviewProps) {
  const selectedLocation = locations?.find(loc => loc.id === selectedLocationId);

  return (
    <div className="max-w-3xl space-y-6">
      {/* Location Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Select Location</h3>
        <select
          value={selectedLocationId || ''}
          onChange={(e) => onLocationSelect(parseInt(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="">Choose a location...</option>
          {locations?.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name} - {loc.city}, {loc.country}
            </option>
          ))}
        </select>
      </div>

      {/* Weather Display */}
      {selectedLocationId && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          {isLoading ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Loading weather data...</p>
          ) : weatherData ? (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <MapPin className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  <div>
                    <h4 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {selectedLocation?.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {selectedLocation?.city}, {selectedLocation?.country}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-4xl font-bold text-gray-900 dark:text-white">
                    {weatherData.temperature}°
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {weatherData.condition}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Feels Like</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {weatherData.feels_like}°
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Humidity</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {weatherData.humidity}%
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Wind Speed</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {weatherData.wind_speed}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Pressure</p>
                  <p className="text-xl font-semibold text-gray-900 dark:text-white">
                    {weatherData.pressure}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              No weather data available
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default WeatherPreview;
