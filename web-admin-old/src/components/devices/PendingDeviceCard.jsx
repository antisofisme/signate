import { memo } from 'react'
import { Monitor, Tv, CheckCircle } from 'lucide-react'

/**
 * PendingDeviceCard Component
 * Displays a device pending approval with device information and approve button
 * Memoized to prevent unnecessary re-renders in pending devices list
 *
 * Features:
 * - Device icon based on platform (TV platforms or Monitor/Browser)
 * - Device name and identifier (unique code)
 * - Platform badge (webOS, Chrome, etc.)
 * - Last seen timestamp
 * - Approve button with mutation callback
 * - Visual styling with yellow theme for pending status
 *
 * @param {Object} device - Device object with pending status
 * @param {Function} onApprove - Callback when approve button is clicked
 */
function PendingDeviceCard({ device, onApprove }) {
  // Determine if device is TV based on platform
  const isTv = device.platform && ['webOS', 'Tizen', 'Android TV'].includes(device.platform)

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border-2 border-yellow-300 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Device Icon */}
        <div className={`flex items-center justify-center w-12 h-12 rounded-full ${
          isTv ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-green-100 dark:bg-green-900/30'
        }`}>
          {isTv ? (
            <Tv className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600 dark:text-green-400" />
          )}
        </div>

        {/* Device Info */}
        <div>
          <p className="font-bold text-gray-800 dark:text-gray-100">{device.device_name}</p>

          {/* IP Address */}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">IP:</span>
            <span className="font-mono text-sm text-gray-700 dark:text-gray-300">
              {device.ip_address || '-'}
            </span>
            {device.platform && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                device.platform === 'webOS' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}>
                {device.platform}
              </span>
            )}
          </div>

          {/* Code Display */}
          <div className="flex items-center gap-2 mt-1">
            {device.unique_code ? (
              <>
                <span className="text-xs text-gray-500 dark:text-gray-400">Code:</span>
                <span className="font-mono text-lg font-bold text-yellow-600">
                  {device.unique_code}
                </span>
              </>
            ) : (
              <>
                <span className="text-xs text-gray-500 dark:text-gray-400">Code:</span>
                <span className="text-gray-400 dark:text-gray-500">-</span>
              </>
            )}
          </div>

          {/* Last Seen */}
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {device.last_seen
              ? `Last seen: ${new Date(device.last_seen).toLocaleString()}`
              : 'Waiting for connection...'}
          </p>
        </div>
      </div>

      {/* Approve Button */}
      <button
        onClick={() => onApprove(device.id)}
        className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
      >
        <CheckCircle className="w-5 h-5" />
        Approve
      </button>
    </div>
  )
}

export default memo(PendingDeviceCard)
