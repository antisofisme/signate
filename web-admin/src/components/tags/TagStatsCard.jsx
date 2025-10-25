import { useQuery } from '@tanstack/react-query'
import { tagsAPI } from '../../services/api'
import { Users, Wifi, WifiOff, FileText, ListVideo } from 'lucide-react'

/**
 * TagStatsCard Component
 * Displays statistics for a specific tag
 *
 * Features:
 * - Total device count
 * - Online/Offline device breakdown
 * - Content count through tag (placeholder - requires backend)
 * - Playlist count using tag (placeholder - requires backend)
 *
 * @param {Object} tag - Tag object to show statistics for
 */
export default function TagStatsCard({ tag }) {
  // Fetch devices in this tag to calculate online/offline
  const { data: tagDevicesData, isLoading } = useQuery({
    queryKey: ['tag-devices', tag.id],
    queryFn: () => tagsAPI.getDevices(tag.id).then(res => res.data),
    enabled: !!tag.id, // Only fetch if tag.id exists
  })

  const devices = tagDevicesData?.devices || []
  const onlineDevices = devices.filter(d => d.status === 'online').length
  const offlineDevices = devices.filter(d => d.status === 'offline').length
  const totalDevices = devices.length

  // Calculate percentage
  const onlinePercentage = totalDevices > 0 ? Math.round((onlineDevices / totalDevices) * 100) : 0

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-md p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
        <div
          className="w-4 h-4 rounded-full flex-shrink-0"
          style={{ backgroundColor: tag.color }}
        />
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-800 text-lg truncate">{tag.tag_name}</h3>
          <p className="text-sm text-gray-600 truncate">Statistics Overview</p>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Statistics Grid */}
      {!isLoading && (
        <div className="space-y-4">
          {/* Device Statistics */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                <span className="font-semibold text-gray-800">Devices</span>
              </div>
              <span className="text-2xl font-bold text-gray-800">{totalDevices}</span>
            </div>

            {/* Online/Offline Breakdown */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Wifi className="w-4 h-4 text-green-600" />
                  <span className="text-gray-600">Online</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-green-700">{onlineDevices}</span>
                  <span className="text-xs text-gray-500">({onlinePercentage}%)</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <WifiOff className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Offline</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">{offlineDevices}</span>
                  <span className="text-xs text-gray-500">({100 - onlinePercentage}%)</span>
                </div>
              </div>

              {/* Progress Bar */}
              {totalDevices > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${onlinePercentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1 text-center">
                    {onlinePercentage}% devices online
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Content Statistics (Placeholder) */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 opacity-60">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span className="font-semibold text-gray-800">Content</span>
              </div>
              <span className="text-2xl font-bold text-gray-400">-</span>
            </div>
            <p className="text-xs text-gray-500">
              Content assigned through this tag
            </p>
            <div className="mt-2 px-2 py-1 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
              Requires backend support
            </div>
          </div>

          {/* Playlist Statistics (Placeholder) */}
          <div className="bg-white rounded-lg p-4 border border-gray-200 opacity-60">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ListVideo className="w-5 h-5 text-indigo-600" />
                <span className="font-semibold text-gray-800">Playlists</span>
              </div>
              <span className="text-2xl font-bold text-gray-400">-</span>
            </div>
            <p className="text-xs text-gray-500">
              Playlists using this tag
            </p>
            <div className="mt-2 px-2 py-1 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
              Requires backend support
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && totalDevices === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No devices in this tag</p>
        </div>
      )}
    </div>
  )
}
