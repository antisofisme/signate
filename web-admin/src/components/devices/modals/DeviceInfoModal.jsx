import { Tv, Monitor } from 'lucide-react'

/**
 * DeviceInfoModal Component
 * Modal for displaying detailed device information
 *
 * Features:
 * - Display information (screen resolution, viewport, pixel ratio)
 * - Platform information (UUID, platform, model, firmware)
 * - Device basic information (ID, type, IP, status, last seen)
 * - Organized in collapsible sections with proper formatting
 * - Status badges with color coding
 * - Platform badges (webOS, etc.)
 * - Monospace formatting for technical identifiers
 *
 * @param {Object} device - Device object to display information for
 * @param {Function} onClose - Callback when modal should close
 */
export default function DeviceInfoModal({ device, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center">
            {device.device_uuid ? (
              <Tv className="w-6 h-6 text-blue-600 mr-3" />
            ) : (
              <Monitor className="w-6 h-6 text-green-600 mr-3" />
            )}
            <h2 className="text-2xl font-bold text-gray-800">{device.device_name}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Display Information Section */}
          <div className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              📺 Display Information
            </h3>
            <div className="space-y-3 bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Screen Resolution:</span>
                <span className="text-gray-900">
                  {device.screen_width && device.screen_height
                    ? `${device.screen_width}x${device.screen_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Viewport Size:</span>
                <span className="text-gray-900">
                  {device.viewport_width && device.viewport_height
                    ? `${device.viewport_width}x${device.viewport_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Device Pixel Ratio:</span>
                <span className="text-gray-900">
                  {device.device_pixel_ratio || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">User Agent:</span>
                <span className="text-gray-900 text-sm break-all">
                  {device.user_agent || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Connection:</span>
                <span className="text-gray-900">
                  {device.connection_type && device.connection_speed
                    ? `${device.connection_type} (${device.connection_speed}Mbps)`
                    : device.connection_type || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Device Basic Information */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-4">Device Information</h3>
            <div className="space-y-3 bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Device ID:</span>
                <span className="text-gray-900 font-mono">{device.id}</span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Device Type:</span>
                <span className="text-gray-900">{device.device_type.toUpperCase()}</span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">IP Address:</span>
                <span className="text-gray-900">{device.ip_address || 'N/A'}</span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  device.status === 'active' ? 'bg-green-100 text-green-700' :
                  device.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {device.status}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Last Seen:</span>
                <span className="text-gray-900">
                  {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
