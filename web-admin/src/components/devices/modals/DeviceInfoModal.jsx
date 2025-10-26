import { Tv, Monitor, X } from 'lucide-react'
import { Modal, ModalFooter, Button } from '../../shared'

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
  // Determine if device is TV based on platform
  const isTv = device.platform && ['webOS', 'Tizen', 'Android TV'].includes(device.platform)

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="2xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom header with gradient and icon - Fixed */}
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-b flex-shrink-0">
        <div className="flex items-center">
          {isTv ? (
            <Tv className="w-6 h-6 text-blue-600 mr-3" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600 mr-3" />
          )}
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{device.device_name}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto p-6">
          {/* Display Information Section */}
          <div className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center">
              📺 Display Information
            </h3>
            <div className="space-y-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Screen Resolution:</span>
                <span className="text-gray-900 dark:text-white">
                  {device.screen_width && device.screen_height
                    ? `${device.screen_width}x${device.screen_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Viewport Size:</span>
                <span className="text-gray-900 dark:text-white">
                  {device.viewport_width && device.viewport_height
                    ? `${device.viewport_width}x${device.viewport_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Device Pixel Ratio:</span>
                <span className="text-gray-900 dark:text-white">
                  {device.device_pixel_ratio || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">User Agent:</span>
                <span className="text-gray-900 dark:text-white text-sm break-all">
                  {device.user_agent || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Connection:</span>
                <span className="text-gray-900 dark:text-white">
                  {device.connection_type && device.connection_speed
                    ? `${device.connection_type} (${device.connection_speed}Mbps)`
                    : device.connection_type || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Device Basic Information */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4">Device Information</h3>
            <div className="space-y-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Device ID:</span>
                <span className="text-gray-900 dark:text-white font-mono">{device.id}</span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Device Type:</span>
                <span className="text-gray-900 dark:text-white">{device.device_type.toUpperCase()}</span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">IP Address:</span>
                <span className="text-gray-900 dark:text-white font-mono">{device.ip_address || '-'}</span>
              </div>
              {device.unique_code && (
                <div className="flex items-center">
                  <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Activation Code:</span>
                  <span className="text-gray-900 dark:text-white font-mono font-bold text-lg text-green-600">
                    {device.unique_code}
                  </span>
                </div>
              )}
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  device.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                  device.status === 'pending' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                  'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}>
                  {device.status}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Last Seen:</span>
                <span className="text-gray-900 dark:text-white">
                  {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </div>
      </div>

      {/* Footer - Fixed */}
      <div className="p-6 border-t bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 flex-shrink-0">
        <ModalFooter align="right">
          <Button onClick={onClose} variant="primary">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
