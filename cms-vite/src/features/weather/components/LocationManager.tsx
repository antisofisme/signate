/**
 * Location Manager Component
 *
 * Manage weather locations with search and CRUD operations
 */

import { MapPin, Plus, Trash2, Star } from 'lucide-react';

interface Location {
  id: number;
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  is_default: boolean;
}

interface LocationManagerProps {
  locations?: Location[];
  searchQuery: string;
  searchResults?: any[];
  onSearchChange: (query: string) => void;
  onAddLocation: (result: any) => void;
  onDeleteLocation: (id: number) => void;
  isSearching: boolean;
}

export function LocationManager({
  locations,
  searchQuery,
  searchResults,
  onSearchChange,
  onAddLocation,
  onDeleteLocation,
  isSearching,
}: LocationManagerProps) {
  return (
    <div className="max-w-3xl space-y-6">
      {/* Search Locations */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Add Location</h3>

        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search for a city..."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
        />

        {isSearching && (
          <p className="text-sm text-gray-500 dark:text-gray-400">Searching...</p>
        )}

        {searchResults && searchResults.length > 0 && (
          <div className="space-y-2">
            {searchResults.map((result, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{result.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {result.country} • Lat: {result.latitude}, Lon: {result.longitude}
                  </p>
                </div>
                <button
                  onClick={() => onAddLocation(result)}
                  className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  Add
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Current Locations */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Saved Locations</h3>

        {!locations || locations.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No locations added yet. Search and add locations above.
          </p>
        ) : (
          <div className="space-y-2">
            {locations.map((location) => (
              <div
                key={location.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900 dark:text-white">{location.name}</p>
                      {location.is_default && (
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {location.city}, {location.country}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => onDeleteLocation(location.id)}
                  className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LocationManager;
