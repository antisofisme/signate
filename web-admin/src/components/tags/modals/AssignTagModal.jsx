import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { tagsAPI, devicesAPI } from '../../../services/api'
import { showToast } from '../../../utils/toast'
import { Modal } from '../../shared'

/**
 * AssignTagModal Component
 * Modal for assigning/unassigning tags to/from devices
 *
 * Features:
 * - Display all active devices with assignment status
 * - One-click assign/unassign toggle buttons
 * - Real-time query updates after mutations
 * - Device information display (name, type, IP)
 * - Color-coded tag indicator
 * - Visual feedback for assigned vs unassigned devices
 * - Optimistic UI with query invalidation
 *
 * @param {Object} tag - Tag object to assign to devices
 * @param {Function} onClose - Callback when modal should close
 */
export default function AssignTagModal({ tag, onClose }) {
  const queryClient = useQueryClient()

  // Fetch all active devices
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  // Fetch devices already assigned to this tag
  const { data: tagDevices } = useQuery({
    queryKey: ['tag-devices', tag.id],
    queryFn: () => tagsAPI.getDevices(tag.id).then(res => res.data),
  })

  // Assign tag mutation
  const assignMutation = useMutation({
    mutationFn: tagsAPI.assign,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      queryClient.invalidateQueries(['tag-devices', tag.id])
      showToast.success('Tag assigned successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign tag mutation
  const unassignMutation = useMutation({
    mutationFn: tagsAPI.unassign,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      queryClient.invalidateQueries(['tag-devices', tag.id])
      showToast.success('Tag removed successfully!')
    },
  })

  const handleAssign = (deviceId) => {
    assignMutation.mutate({
      tag_id: tag.id,
      device_id: deviceId,
    })
  }

  const handleUnassign = (deviceId) => {
    unassignMutation.mutate({
      tag_id: tag.id,
      device_id: deviceId,
    })
  }

  const assignedDeviceIds = tagDevices?.devices?.map(d => d.id) || []

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="2xl"
      showCloseButton={false}
    >
      {/* Custom header with tag color indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div
            className="w-4 h-4 rounded-full mr-3"
            style={{ backgroundColor: tag.color }}
          />
          <h2 className="text-xl font-bold">Assign Devices: {tag.tag_name}</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Device list */}
      <div className="space-y-2">
        {devicesData?.devices?.map((device) => {
          const isAssigned = assignedDeviceIds.includes(device.id)
          return (
            <div
              key={device.id}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            >
              <div>
                <p className="font-medium text-gray-800 dark:text-gray-100">{device.device_name}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {device.device_type.toUpperCase()} • {device.ip_address || 'N/A'}
                </p>
              </div>
              <button
                onClick={() => isAssigned ? handleUnassign(device.id) : handleAssign(device.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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
      </div>

      {/* Empty state */}
      {devicesData?.devices?.length === 0 && (
        <p className="text-center py-8 text-gray-500 dark:text-gray-400">No devices available</p>
      )}
    </Modal>
  )
}
