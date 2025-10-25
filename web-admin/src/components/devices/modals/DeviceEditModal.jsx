import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Tv, Monitor, Save, RefreshCw, Unlock, X } from 'lucide-react'
import { devicesAPI } from '../../../services/api'
import toast from 'react-hot-toast'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'

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
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    device_name: device.device_name || '',
    status: device.status || 'pending',
    rotation: device.rotation || 0,
    volume_enabled: device.volume_enabled !== undefined ? device.volume_enabled : true,
  })
  const [isSaving, setIsSaving] = useState(false)
  const [isReleasing, setIsReleasing] = useState(false)
  const [pendingDevices, setPendingDevices] = useState([])
  const [selectedPendingId, setSelectedPendingId] = useState(null)
  const [isLoadingPending, setIsLoadingPending] = useState(false)

  // Fetch pending devices (only browser devices without UUID)
  useEffect(() => {
    const fetchPendingDevices = async () => {
      try {
        setIsLoadingPending(true)
        const response = await devicesAPI.list()
        // Filter: hanya pending devices yang browser (tidak punya UUID) dan bukan device ini sendiri
        const pending = response.data.devices.filter(
          d => d.status === 'pending' && (!d.device_uuid || d.device_uuid === '') && d.id !== device.id
        )
        setPendingDevices(pending)
      } catch (error) {
        console.error('Failed to fetch pending devices:', error)
      } finally {
        setIsLoadingPending(false)
      }
    }

    // Only fetch for browser devices (not WebOS TV with UUID)
    if (!device.device_uuid || device.device_uuid === '') {
      fetchPendingDevices()
    }
  }, [device.id, device.device_uuid])

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)

      // If user selected a pending device to replace with
      if (selectedPendingId) {
        await devicesAPI.replaceWithPending(device.id, selectedPendingId)
        const message = device.status === 'inactive'
          ? 'Device reconnected and reactivated successfully!'
          : 'Device replaced with pending device successfully!'
        toast.success(message, {
          duration: 3000,
          position: 'bottom-right',
        })

        // Small delay to ensure backend completes transaction
        await new Promise(resolve => setTimeout(resolve, 300))
      } else {
        // Normal update
        await devicesAPI.update(device.id, formData)
        toast.success('Device updated successfully!', {
          duration: 3000,
          position: 'bottom-right',
        })
      }

      // Force immediate refetch and wait for completion
      await queryClient.refetchQueries(['devices'], { type: 'active' })

      await onSave?.()
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

  const handleRelease = async () => {
    // Confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to RELEASE this device?\n\n` +
      `Device: ${device.device_name}\n` +
      `Code: ${device.unique_code}\n\n` +
      `This will:\n` +
      `1. Queue a reset command to clear device data\n` +
      `2. Change status to "pending"\n` +
      `3. Generate new activation code\n` +
      `4. Keep content assignments and settings\n\n` +
      `The device will need to re-activate with the new code.`
    )

    if (!confirmed) return

    try {
      setIsReleasing(true)

      await devicesAPI.release(device.id)

      toast.success(
        'Device released successfully! Reset command queued.\n' +
        'Device will show new activation code when it connects.',
        {
          duration: 5000,
          position: 'bottom-right',
        }
      )

      // Force immediate refetch and wait for completion
      await queryClient.refetchQueries(['devices'], { type: 'active' })

      await onSave?.()
      onClose()
    } catch (error) {
      console.error('Failed to release device:', error)
      toast.error(error.response?.data?.detail || 'Failed to release device', {
        duration: 4000,
        position: 'bottom-right',
      })
    } finally {
      setIsReleasing(false)
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="4xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom header with gradient and icon - Fixed */}
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-b flex-shrink-0">
        <div className="flex items-center">
          {device.device_uuid ? (
            <Tv className="w-6 h-6 text-blue-600 mr-3" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600 mr-3" />
          )}
          <h2 className="text-2xl font-bold text-gray-800">Edit Device Settings</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {/* Device Information Section (Editable) */}
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Device Information</h3>
            <div className="space-y-4 bg-gray-50 rounded-lg p-4 border-2 border-gray-200 shadow-sm">
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
              <FormInput
                label="Device Name"
                type="text"
                value={formData.device_name}
                onChange={(e) => handleChange('device_name', e.target.value)}
                placeholder="Enter device name"
              />

              {/* Device Type (Read-only) */}
              <FormInput
                label="Device Type"
                type="text"
                value={device.device_type.toUpperCase()}
                disabled
              />

              {/* Status (Editable) */}
              <FormInput
                label="Status"
                type="select"
                value={formData.status}
                onChange={(e) => handleChange('status', e.target.value)}
                options={[
                  { value: 'pending', label: 'Pending' },
                  { value: 'active', label: 'Active' },
                  { value: 'inactive', label: 'Inactive' }
                ]}
              />

              {/* IP Address (Read-only) */}
              <FormInput
                label="IP Address"
                type="text"
                value={device.ip_address || 'N/A'}
                disabled
              />

              {/* Last Seen (Read-only) */}
              <FormInput
                label="Last Seen"
                type="text"
                value={device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                disabled
              />
            </div>
          </div>

          {/* Replace with Pending Device Section (Only for Browser Devices) */}
          {(!device.device_uuid || device.device_uuid === '') && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <RefreshCw className="w-5 h-5 mr-2 text-orange-600" />
                {device.status === 'inactive' ? 'Reconnect with Pending Viewer' : 'Replace with Pending Device'}
              </h3>
              <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-4 border-2 border-orange-200">
                <p className="text-sm text-gray-700 mb-3">
                  {device.status === 'inactive'
                    ? 'This device has been released. Connect it with a new viewer by selecting a pending device below. The device will be reactivated automatically.'
                    : 'If this device lost its connection (e.g., cache cleared), you can replace it with a new pending device to reconnect.'}
                </p>

                {isLoadingPending ? (
                  <div className="text-center py-4 text-gray-500">Loading pending devices...</div>
                ) : pendingDevices.length === 0 ? (
                  <div className="text-center py-4 text-gray-500 bg-white rounded-lg border-2 border-dashed border-gray-300">
                    No pending devices available
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Pending Device to Replace With:
                    </label>
                    <select
                      value={selectedPendingId || ''}
                      onChange={(e) => setSelectedPendingId(e.target.value ? parseInt(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-white"
                    >
                      <option value="">
                        {device.status === 'inactive'
                          ? '-- Select a pending viewer to reconnect --'
                          : `-- Keep current code (${device.unique_code || 'N/A'}) --`}
                      </option>
                      {pendingDevices.map(pending => (
                        <option key={pending.id} value={pending.id}>
                          Code: {pending.unique_code} | IP: {pending.ip_address || 'N/A'} | {pending.device_name}
                        </option>
                      ))}
                    </select>

                    {selectedPendingId && (
                      <div className="mt-3 p-3 bg-orange-100 border border-orange-300 rounded-lg">
                        <p className="text-sm font-medium text-orange-800">
                          {device.status === 'inactive'
                            ? '✅ This will reconnect the inactive device with the selected viewer and reactivate it. The pending device will be merged and deleted.'
                            : '⚠️ Warning: This will replace the current device code with the selected pending device. The pending device will be deleted after replacement.'}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Display Settings Section (Editable) */}
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              🎛️ Display Settings
            </h3>
            <div className="space-y-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4 border-2 border-blue-200">
              {/* Rotation Dropdown */}
              <FormInput
                label="Screen Rotation"
                type="select"
                value={formData.rotation}
                onChange={(e) => handleChange('rotation', parseInt(e.target.value))}
                options={[
                  { value: 0, label: '0° (Normal)' },
                  { value: 90, label: '90° (Clockwise)' },
                  { value: 180, label: '180° (Upside Down)' },
                  { value: 270, label: '270° (Counter-clockwise)' }
                ]}
                description="Rotate the display orientation for the viewer"
              />

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
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              📺 Display Information
            </h3>
            <div className="space-y-3 bg-gray-50 rounded-lg p-4 border-2 border-gray-200 shadow-sm">
              <div className="flex items-center">
                <span className="w-48 font-semibold text-gray-900">Screen Resolution:</span>
                <span className="text-gray-900">
                  {device.screen_width && device.screen_height
                    ? `${device.screen_width}x${device.screen_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-semibold text-gray-900">Viewport Size:</span>
                <span className="text-gray-900">
                  {device.viewport_width && device.viewport_height
                    ? `${device.viewport_width}x${device.viewport_height}`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-semibold text-gray-900">Device Pixel Ratio:</span>
                <span className="text-gray-900">
                  {device.device_pixel_ratio || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-semibold text-gray-900">User Agent:</span>
                <span className="text-gray-900 text-sm break-all">
                  {device.user_agent || 'N/A'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-48 font-semibold text-gray-900">Connection:</span>
                <span className="text-gray-900">
                  {device.connection_type && device.connection_speed
                    ? `${device.connection_type} (${device.connection_speed}Mbps)`
                    : device.connection_type || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Fixed */}
      <div className="p-6 border-t bg-gray-50 flex-shrink-0">
        <ModalFooter align="between">
          {/* Left side - Release button (only for active devices) */}
          <div>
            {device.status === 'active' && (
              <Button
                onClick={handleRelease}
                disabled={isReleasing || isSaving}
                variant="warning"
                title="Release device (reset with new activation code)"
              >
                <Unlock className="w-4 h-4" />
                {isReleasing ? 'Releasing...' : 'Release Device'}
              </Button>
            )}
          </div>

          {/* Right side - Cancel and Save buttons */}
          <div className="flex gap-3">
            <Button
              onClick={onClose}
              variant="secondary"
              disabled={isSaving || isReleasing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={isSaving || isReleasing}
              variant="primary"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </ModalFooter>
      </div>
    </Modal>
  )
}
