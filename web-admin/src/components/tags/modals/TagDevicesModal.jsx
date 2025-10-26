import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI } from '../../../services/api'
import { Modal, ModalFooter, Button } from '../../shared'
import { Monitor, Trash2, Plus, Wifi, WifiOff } from 'lucide-react'
import { showToast } from '../../../utils/toast'

/**
 * TagDevicesModal Component
 * Modal for viewing and managing devices assigned to a tag
 *
 * Features:
 * - List all devices in the tag
 * - Show device status (online/offline)
 * - Remove devices from tag
 * - Quick action to add more devices (opens AssignTagModal)
 * - Device information display (name, type, IP, status)
 *
 * @param {Object} tag - Tag object to view devices for
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onOpenAssign - Callback to open assign modal
 */
export default function TagDevicesModal({ tag, onClose, onOpenAssign }) {
  const queryClient = useQueryClient()

  // Fetch devices in this tag
  const { data: tagDevicesData, isLoading } = useQuery({
    queryKey: ['tag-devices', tag.id],
    queryFn: () => tagsAPI.getDevices(tag.id).then(res => res.data),
  })

  // Unassign device from tag mutation
  const unassignMutation = useMutation({
    mutationFn: (deviceId) => tagsAPI.unassign({
      tag_id: tag.id,
      device_id: deviceId,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      queryClient.invalidateQueries(['tag-devices', tag.id])
      showToast.success('Device removed from tag!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to remove device')
    }
  })

  const handleRemoveDevice = (device) => {
    if (confirm(`Remove "${device.device_name}" from tag "${tag.tag_name}"?`)) {
      unassignMutation.mutate(device.id)
    }
  }

  const handleAddDevices = () => {
    onClose()
    onOpenAssign()
  }

  const devices = tagDevicesData?.devices || []

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Devices in Tag: ${tag.tag_name}`}
      size="2xl"
    >
      <div className="space-y-4">
        {/* Header with tag color and add button */}
        <div className="flex items-center justify-between pb-3 border-b">
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: tag.color }}
            />
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {devices.length} device{devices.length !== 1 ? 's' : ''} in this tag
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={handleAddDevices}
          >
            Add More Devices
          </Button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && devices.length === 0 && (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
            <Monitor className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400 font-medium mb-2">No devices in this tag</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Assign devices to this tag to get started</p>
            <Button
              variant="primary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={handleAddDevices}
            >
              Assign Devices
            </Button>
          </div>
        )}

        {/* Devices List */}
        {!isLoading && devices.length > 0 && (
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
            {devices.map((device) => (
              <div
                key={device.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                {/* Device Info */}
                <div className="flex items-center gap-3 flex-1">
                  {/* Status Indicator */}
                  <div className="flex-shrink-0">
                    {device.status === 'online' ? (
                      <div className="relative">
                        <Wifi className="w-5 h-5 text-green-500" />
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      </div>
                    ) : (
                      <WifiOff className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                    )}
                  </div>

                  {/* Device Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-800 dark:text-gray-100 truncate">
                        {device.device_name}
                      </p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        device.status === 'online'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {device.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {device.device_type?.toUpperCase() || 'Unknown'} • {device.ip_address || 'No IP'}
                    </p>
                  </div>
                </div>

                {/* Remove Button */}
                <Button
                  variant="danger"
                  size="sm"
                  leftIcon={<Trash2 className="w-4 h-4" />}
                  onClick={() => handleRemoveDevice(device)}
                  disabled={unassignMutation.isLoading}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Info Box */}
        {devices.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
            💡 Removing a device from this tag will not delete the device itself, only the tag assignment.
          </div>
        )}

        {/* Footer */}
        <ModalFooter>
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
