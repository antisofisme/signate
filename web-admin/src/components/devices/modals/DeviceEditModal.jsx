import { useState } from 'react'
import { Tv, Monitor, Save } from 'lucide-react'
import { devicesAPI } from '../../../services/api'
import toast from 'react-hot-toast'

/**
 * DeviceEditModal Component
 * Modal for editing device settings including display settings
 *
 * Features:
 * - Edit device name and status
 * - Configure display settings (rotation, volume)
 * - View device information (read-only)
 * - Save changes to backend
 *
 * @param {Object} device - Device object to edit
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSave - Callback after successful save
 */
export default function DeviceEditModal({ device, onClose, onSave }) {
  const [formData, setFormData] = useState({
    device_name: device.device_name || '',
    status: device.status || 'pending',
    rotation: device.rotation || 0,
    volume_enabled: device.volume_enabled !== undefined ? device.volume_enabled : true,
  })
  const [isSaving, setIsSaving] = useState(false)

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      await devicesAPI.update(device.id, formData)
      toast.success('Device updated successfully!', {
        duration: 3000,
        position: 'bottom-right',
      })
      onSave?.()
      onClose()
    } catch (error) {
      console.error('Failed to update device:', error)
      toast.error(error.response?.data?.detail || 'Failed to update device', {
        duration: 4000,
        position: 'bottom-right',
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center">
            {device.device_uuid ? (
              <Tv className="w-6 h-6 text-blue-600 mr-3" />
            ) : (
              <Monitor className="w-6 h-6 text-green-600 mr-3" />
            )}
            <h2 className="text-2xl font-bold text-gray-800">Edit Device Settings</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Device Information Section (Editable) */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-4">Device Information</h3>
            <div className="space-y-4 bg-gray-50 rounded-lg p-4">
              {/* Device ID (Read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device ID</label>
                <input
                  type="text"
                  value={device.id}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 font-mono"
                />
              </div>

              {/* Device Name (Editable) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device Name</label>
                <input
                  type="text"
                  value={formData.device_name}
                  onChange={(e) => handleChange('device_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter device name"
                />
              </div>

              {/* Device Type (Read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device Type</label>
                <input
                  type="text"
                  value={device.device_type.toUpperCase()}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                />
              </div>

              {/* Status (Editable) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="pending">Pending</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* IP Address (Read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IP Address</label>
                <input
                  type="text"
                  value={device.ip_address || 'N/A'}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                />
              </div>

              {/* Last Seen (Read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Seen</label>
                <input
                  type="text"
                  value={device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                />
              </div>
            </div>
          </div>

          {/* Display Settings Section (Editable) */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
              🎛️ Display Settings
            </h3>
            <div className="space-y-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4 border-2 border-blue-200">
              {/* Rotation Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Screen Rotation
                </label>
                <select
                  value={formData.rotation}
                  onChange={(e) => handleChange('rotation', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                >
                  <option value={0}>0° (Normal)</option>
                  <option value={90}>90° (Clockwise)</option>
                  <option value={180}>180° (Upside Down)</option>
                  <option value={270}>270° (Counter-clockwise)</option>
                </select>
                <p className="text-xs text-gray-600 mt-1">
                  Rotate the display orientation for the viewer
                </p>
              </div>

              {/* Volume Toggle */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Video Audio
                </label>
                <div className="flex items-center space-x-4">
                  <button
                    type="button"
                    onClick={() => handleChange('volume_enabled', true)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      formData.volume_enabled
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                  >
                    🔊 On
                  </button>
                  <button
                    type="button"
                    onClick={() => handleChange('volume_enabled', false)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      !formData.volume_enabled
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                  >
                    🔇 Off
                  </button>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Enable or disable audio playback for videos
                </p>
              </div>
            </div>
          </div>

          {/* Display Information Section (Read-only) */}
          <div>
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
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
