import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, devicesAPI } from '../../../services/api'
import { Modal, ModalFooter, Button } from '../../shared'
import { Monitor } from 'lucide-react'
import { showToast } from '../../../utils/toast'

/**
 * TagDeviceManagementModal Component
 * Modal for managing device assignments to a tag
 * Pattern: Same as PlaylistAssignmentModal for consistency
 *
 * Features:
 * - Shows ALL devices (active)
 * - Visual feedback for assigned vs unassigned
 * - One-click assign/remove buttons
 * - Real-time query updates after mutations
 * - Device information display (name, type, status, IP)
 *
 * @param {Object} tag - Tag object to manage devices for
 * @param {Function} onClose - Callback when modal should close
 */
export default function TagDeviceManagementModal({ tag, onClose }) {
  const queryClient = useQueryClient()

  // Fetch all active devices
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  // Fetch devices currently assigned to this tag
  const { data: assignedDevicesData } = useQuery({
    queryKey: ['tags', tag.id, 'devices'],
    queryFn: () => tagsAPI.getDevices(tag.id).then(res => res.data),
  })

  // Assign tag to device mutation
  const assignMutation = useMutation({
    mutationFn: (deviceId) => tagsAPI.assign({
      tag_id: tag.id,
      device_id: deviceId
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags', tag.id, 'devices'])
      queryClient.invalidateQueries(['tags'])
      showToast.success('Device assigned to tag!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign tag from device mutation
  const unassignMutation = useMutation({
    mutationFn: (deviceId) => tagsAPI.unassign({
      tag_id: tag.id,
      device_id: deviceId
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags', tag.id, 'devices'])
      queryClient.invalidateQueries(['tags'])
      showToast.success('Device removed from tag!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Unassignment failed')
    }
  })

  const handleToggle = (deviceId, isAssigned) => {
    if (isAssigned) {
      unassignMutation.mutate(deviceId)
    } else {
      assignMutation.mutate(deviceId)
    }
  }

  // Get list of assigned device IDs for quick lookup
  const assignedDeviceIds = assignedDevicesData?.devices?.map(d => d.id) || []

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Devices: ${tag.tag_name}`}
      size="2xl"
    >
      <div className="space-y-4">
        {/* Tag Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
          <p>
            Assign or remove devices from this tag. Devices assigned to this tag will automatically receive content and playlists assigned to the tag.
          </p>
        </div>

        {/* Devices List */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
          {devicesData?.devices?.map((device) => {
            const isAssigned = assignedDeviceIds.includes(device.id)
            return (
              <div
                key={device.id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    device.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-100">{device.device_name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {device.device_type.toUpperCase()} • {device.ip_address || 'N/A'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle(device.id, isAssigned)}
                  disabled={assignMutation.isPending || unassignMutation.isPending}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                    isAssigned
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isAssigned ? 'Remove' : 'Assign'}
                </button>
              </div>
            )
          })}

          {/* Empty state */}
          {devicesData?.devices?.length === 0 && (
            <div className="text-center py-8">
              <Monitor className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
              <p className="text-gray-500 dark:text-gray-400">No active devices available</p>
            </div>
          )}
        </div>

        {/* Stats Summary */}
        <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Total Devices:</span>
            <span className="font-semibold text-gray-800 dark:text-gray-100">{devicesData?.devices?.length || 0}</span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-gray-600 dark:text-gray-400">Assigned to this tag:</span>
            <span className="font-semibold text-green-700">{assignedDeviceIds.length}</span>
          </div>
        </div>

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
