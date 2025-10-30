import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI, devicesAPI, tagsAPI } from '../../../services/api'
import { Modal, Button } from '../../shared'
import { Monitor, Tag } from 'lucide-react'
import { showToast } from '../../../utils/toast'

/**
 * PlaylistAssignmentModal Component
 * Modal for assigning playlists to devices and tags
 *
 * Features:
 * - Tab-based interface (Devices | Tags)
 * - Assign/unassign playlist to individual devices
 * - Assign/unassign playlist to tags (bulk assignment)
 * - Visual feedback for assigned vs unassigned
 * - Real-time query updates after mutations
 * - Device information display (name, type, status)
 * - Tag information display (name, color, device count)
 *
 * @param {Object} playlist - Playlist object to assign
 * @param {Function} onClose - Callback when modal should close
 */
export default function PlaylistAssignmentModal({ playlist, onClose }) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('devices') // 'devices' | 'tags'

  // Fetch all active devices
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  // Fetch all tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch current playlist assignments
  const { data: assignmentsData } = useQuery({
    queryKey: ['playlists', playlist.id, 'assignments'],
    queryFn: () => playlistsAPI.getAssignments(playlist.id).then(res => res.data),
  })

  // Assign to device mutation
  const assignToDeviceMutation = useMutation({
    mutationFn: (deviceId) => playlistsAPI.assignToDevices(playlist.id, { device_ids: [deviceId] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'assignments'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Playlist assigned to device!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign from device mutation
  const unassignFromDeviceMutation = useMutation({
    mutationFn: (deviceId) => playlistsAPI.unassignFromDevices(playlist.id, { device_ids: [deviceId] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'assignments'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Playlist removed from device!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Unassignment failed')
    }
  })

  // Assign to tag mutation
  const assignToTagMutation = useMutation({
    mutationFn: (tagId) => playlistsAPI.assignToTags(playlist.id, { tag_ids: [tagId] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'assignments'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Playlist assigned to tag!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign from tag mutation
  const unassignFromTagMutation = useMutation({
    mutationFn: (tagId) => playlistsAPI.unassignFromTags(playlist.id, { tag_ids: [tagId] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'assignments'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Playlist removed from tag!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Unassignment failed')
    }
  })

  const handleDeviceToggle = (deviceId, isAssigned) => {
    if (isAssigned) {
      unassignFromDeviceMutation.mutate(deviceId)
    } else {
      assignToDeviceMutation.mutate(deviceId)
    }
  }

  const handleTagToggle = (tagId, isAssigned) => {
    if (isAssigned) {
      unassignFromTagMutation.mutate(tagId)
    } else {
      assignToTagMutation.mutate(tagId)
    }
  }

  const assignedDeviceIds = assignmentsData?.devices?.map(d => d.id) || []
  const assignedTagIds = assignmentsData?.tags?.map(t => t.id) || []

  // Footer with close button
  const footer = (
    <div className="flex justify-end">
      <Button variant="secondary" onClick={onClose} className="flex-1">
        Close
      </Button>
    </div>
  )

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Assign Playlist: ${playlist.name}`}
      size="2xl"
      footer={footer}
    >
      <div className="space-y-4">
        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('devices')}
            className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${
              activeTab === 'devices'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-800 dark:text-gray-100'
            }`}
          >
            <Monitor className="w-4 h-4" />
            Devices ({devicesData?.devices?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('tags')}
            className={`px-4 py-2 font-medium text-sm transition-colors flex items-center gap-2 ${
              activeTab === 'tags'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-800 dark:text-gray-100'
            }`}
          >
            <Tag className="w-4 h-4" />
            Tags ({tagsData?.items?.length || 0})
          </button>
        </div>

        {/* Devices Tab Content */}
        {activeTab === 'devices' && (
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
                    onClick={() => handleDeviceToggle(device.id, isAssigned)}
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

            {/* Empty state */}
            {devicesData?.devices?.length === 0 && (
              <p className="text-center py-8 text-gray-500 dark:text-gray-400">No devices available</p>
            )}
          </div>
        )}

        {/* Tags Tab Content */}
        {activeTab === 'tags' && (
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
            {tagsData?.items?.map((tag) => {
              const isAssigned = assignedTagIds.includes(tag.id)
              return (
                <div
                  key={tag.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: tag.color }}
                    />
                    <div>
                      <p className="font-medium text-gray-800 dark:text-gray-100">{tag.tag_name}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {tag.description || 'No description'} • {tag.device_count || 0} devices
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleTagToggle(tag.id, isAssigned)}
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

            {/* Empty state */}
            {tagsData?.items?.length === 0 && (
              <p className="text-center py-8 text-gray-500 dark:text-gray-400">No tags available</p>
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
          {activeTab === 'devices' ? (
            <p>
              Assign this playlist to individual devices. Devices will play this playlist according to its schedule.
            </p>
          ) : (
            <p>
              Assign this playlist to tags to bulk-assign it to all devices in those tags. This is the recommended approach for managing many devices.
            </p>
          )}
        </div>
      </div>
    </Modal>
  )
}
