import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { contentAPI, devicesAPI, tagsAPI } from '../../../services/api'
import { showToast } from '../../../utils/toast'
import { Modal, Button } from '../../shared'

/**
 * EditContentModal Component
 * Modal for editing individual content details and managing device/tag assignments
 *
 * Features:
 * - Edit content metadata (title, description, duration)
 * - Assign/unassign content to specific devices
 * - Assign/unassign content to tags (affects all devices with those tags)
 * - Visual feedback for selected devices/tags
 * - Diff-based assignment updates (only changes what's needed)
 * - Pre-populated with existing assignments
 * - Loading state while fetching assignments
 *
 * @param {Object} content - Content object to edit
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onSubmit - Optional callback after successful save
 */
export default function EditContentModal({ content, onClose, onSubmit }) {
  const queryClient = useQueryClient()
  const [saving, setSaving] = useState(false)

  // State for content metadata
  const [title, setTitle] = useState(content.title)
  const [description, setDescription] = useState(content.description || '')

  // Video segment state
  const [videoStartTime, setVideoStartTime] = useState(content.video_start_time || 0)
  const [videoEndTime, setVideoEndTime] = useState(content.video_end_time || null)

  // Auto-calculate duration for videos
  const calculateDuration = (startTime, endTime) => {
    if (content.content_type === 'video') {
      if (endTime && endTime > startTime) {
        return Math.ceil(endTime - startTime)
      } else if (content.video_duration) {
        return Math.ceil(content.video_duration - startTime)
      }
    }
    return content.duration
  }

  const [duration, setDuration] = useState(calculateDuration(videoStartTime, videoEndTime))

  // Fetch existing assignments for this content
  const { data: assignmentsData, isLoading: assignmentsLoading } = useQuery({
    queryKey: ['content-assignments', content.id],
    queryFn: () => contentAPI.getAssignments(content.id).then(res => res.data),
  })

  // Fetch devices and tags
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // State for selected device and tag IDs
  const [selectedDeviceIds, setSelectedDeviceIds] = useState(new Set())
  const [selectedTagIds, setSelectedTagIds] = useState(new Set())

  // State for display order (for new assignments)
  const [displayOrder, setDisplayOrder] = useState(0)

  // State for initial assignments (to track what to add/remove)
  const [initialDeviceIds, setInitialDeviceIds] = useState(new Set())
  const [initialTagIds, setInitialTagIds] = useState(new Set())

  // Pre-populate selections when assignments load
  useEffect(() => {
    if (assignmentsData && !assignmentsLoading) {
      const deviceIds = new Set()
      const tagIds = new Set()

      assignmentsData.forEach(assignment => {
        if (assignment.device_id) {
          deviceIds.add(assignment.device_id)
        }
        if (assignment.tag_id) {
          tagIds.add(assignment.tag_id)
        }
      })

      setSelectedDeviceIds(deviceIds)
      setSelectedTagIds(tagIds)
      setInitialDeviceIds(deviceIds)
      setInitialTagIds(tagIds)
    }
  }, [assignmentsData, assignmentsLoading])

  const toggleDevice = (deviceId) => {
    setSelectedDeviceIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(deviceId)) {
        newSet.delete(deviceId)
      } else {
        newSet.add(deviceId)
      }
      return newSet
    })
  }

  const toggleTag = (tagId) => {
    setSelectedTagIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tagId)) {
        newSet.delete(tagId)
      } else {
        newSet.add(tagId)
      }
      return newSet
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)

    try {
      // First, update content metadata if changed
      const hasMetadataChanges =
        title !== content.title ||
        description !== (content.description || '') ||
        duration !== content.duration ||
        (content.content_type === 'video' && (
          videoStartTime !== (content.video_start_time || 0) ||
          videoEndTime !== content.video_end_time
        ))

      if (hasMetadataChanges) {
        const updateData = {
          title,
          description,
          duration: parseInt(duration)
        }

        // Add video segment timing for videos
        if (content.content_type === 'video') {
          updateData.video_start_time = videoStartTime
          updateData.video_end_time = videoEndTime
        }

        await contentAPI.update(content.id, updateData)
      }

      // Determine what to add and what to remove
      const devicesToAdd = [...selectedDeviceIds].filter(id => !initialDeviceIds.has(id))
      const devicesToRemove = [...initialDeviceIds].filter(id => !selectedDeviceIds.has(id))
      const tagsToAdd = [...selectedTagIds].filter(id => !initialTagIds.has(id))
      const tagsToRemove = [...initialTagIds].filter(id => !selectedTagIds.has(id))

      // Add new device assignments
      for (const deviceId of devicesToAdd) {
        await contentAPI.assign(content.id, {
          device_id: deviceId,
          display_order: parseInt(displayOrder) || 0,
          priority: 0
        })
      }

      // Add new tag assignments
      for (const tagId of tagsToAdd) {
        await contentAPI.assign(content.id, {
          tag_id: tagId,
          display_order: parseInt(displayOrder) || 0,
          priority: 0
        })
      }

      // Remove device assignments
      for (const deviceId of devicesToRemove) {
        await contentAPI.unassign(content.id, {
          device_id: deviceId
        })
      }

      // Remove tag assignments
      for (const tagId of tagsToRemove) {
        await contentAPI.unassign(content.id, {
          tag_id: tagId
        })
      }

      // Refresh assignments and close
      queryClient.invalidateQueries(['content-assignments', content.id])
      queryClient.invalidateQueries(['content'])

      setSaving(false)
      showToast.success('Content updated successfully!')
      onClose()
    } catch (error) {
      setSaving(false)
      showToast.error(error.response?.data?.detail || 'Failed to update content')
    }
  }

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3 justify-end">
      <Button
        type="button"
        onClick={onClose}
        disabled={saving}
        variant="secondary"
        className="flex-1"
      >
        {saving ? 'Please wait...' : 'Cancel'}
      </Button>
      <Button
        type="submit"
        onClick={handleSubmit}
        disabled={saving}
        variant="primary"
        className="flex-1"
      >
        {saving ? 'Saving...' : 'Save Changes'}
      </Button>
    </div>
  )

  if (assignmentsLoading) {
    return (
      <Modal isOpen={true} onClose={onClose} size="2xl">
        <p className="text-center text-gray-600 dark:text-gray-400">Loading assignments...</p>
      </Modal>
    )
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="2xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
      footer={footer}
    >
      {/* Custom Header - Fixed */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Edit Content</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Edit content details and assignments</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          aria-label="Close modal"
          disabled={saving}
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Form Content - Scrollable */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Content Details Section */}
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">✏️</span>
                <h3 className="font-bold text-gray-800 dark:text-gray-100 text-lg">Content Details</h3>
              </div>

              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    disabled={saving}
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    rows={3}
                    disabled={saving}
                  />
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Duration (seconds)
                    {content.content_type === 'video' && (
                      <span className="text-xs text-blue-600 ml-2">
                        ⚡ Auto-calculated from segment
                      </span>
                    )}
                  </label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      content.content_type === 'video'
                        ? 'border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 cursor-not-allowed'
                        : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                    disabled={saving || content.content_type === 'video'}
                    min="1"
                    readOnly={content.content_type === 'video'}
                    required
                  />
                  {content.content_type === 'video' && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      📊 Auto-calculated: {videoEndTime
                        ? `${videoEndTime}s - ${videoStartTime}s = ${duration}s`
                        : `Total video (${content.video_duration?.toFixed(0) || '?'}s) - Start (${videoStartTime}s) = ${duration}s`
                      }
                    </p>
                  )}
                </div>

                {/* Video Segment Timing (only for videos) */}
                {content.content_type === 'video' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        🎬 Start Time (seconds)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={videoStartTime}
                        onChange={(e) => {
                          const newStart = parseFloat(e.target.value) || 0
                          setVideoStartTime(newStart)
                          setDuration(calculateDuration(newStart, videoEndTime))
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        disabled={saving}
                        min={0}
                        placeholder="0 (from beginning)"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Start video playback from this time</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        🏁 End Time (seconds)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={videoEndTime || ''}
                        onChange={(e) => {
                          const newEnd = e.target.value ? parseFloat(e.target.value) : null
                          setVideoEndTime(newEnd)
                          setDuration(calculateDuration(videoStartTime, newEnd))
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        disabled={saving}
                        min={0}
                        placeholder="(play until end)"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Stop video at this time (leave empty to play until end)</p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Assignment Settings Section */}
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">🔢</span>
                <h3 className="font-bold text-gray-800 dark:text-gray-100 text-lg">Assignment Settings</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Display Order
                </label>
                <input
                  type="number"
                  value={displayOrder}
                  onChange={(e) => setDisplayOrder(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={saving}
                  min="0"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Order in playback sequence (lower numbers play first). This will be applied to all new assignments below.
                </p>
              </div>
            </div>

            {/* Devices Section */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">📱</span>
                <h3 className="font-bold text-gray-800 dark:text-gray-100 text-lg">Devices</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Select devices to assign this content to
              </p>
              {devicesData?.devices && devicesData.devices.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {devicesData.devices.map((device) => (
                    <label
                      key={device.id}
                      className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedDeviceIds.has(device.id)
                          ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-500 dark:border-blue-600 shadow-md'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedDeviceIds.has(device.id)}
                        onChange={() => toggleDevice(device.id)}
                        className="w-5 h-5 rounded accent-blue-600"
                        disabled={saving}
                      />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-100 block truncate">
                          {device.device_name}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 block">
                          {device.device_type.toUpperCase()}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg text-center text-gray-500 dark:text-gray-400 text-sm">
                  No active devices available
                </div>
              )}
              {selectedDeviceIds.size > 0 && (
                <div className="mt-3 p-2 bg-blue-100 dark:bg-blue-900/30 rounded border border-blue-300 dark:border-blue-600">
                  <p className="text-sm text-blue-800">
                    ✓ {selectedDeviceIds.size} device(s) selected
                  </p>
                </div>
              )}
            </div>

            {/* Tags Section */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🏷️</span>
                <h3 className="font-bold text-gray-800 dark:text-gray-100 text-lg">Tags</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Select tags to assign this content to (affects all devices with these tags)
              </p>
              {tagsData?.items && tagsData.items.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {tagsData.items.map((tag) => (
                    <label
                      key={tag.id}
                      className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedTagIds.has(tag.id)
                          ? 'bg-green-100 dark:bg-green-900/30 border-green-500 dark:border-green-600 shadow-md'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-green-300 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTagIds.has(tag.id)}
                        onChange={() => toggleTag(tag.id)}
                        className="w-5 h-5 rounded accent-green-600"
                        disabled={saving}
                      />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-100 block truncate">
                          {tag.tag_name}
                        </span>
                        {tag.description && (
                          <span className="text-xs text-gray-500 dark:text-gray-400 block truncate">
                            {tag.description}
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg text-center text-gray-500 dark:text-gray-400 text-sm">
                  No tags available
                </div>
              )}
              {selectedTagIds.size > 0 && (
                <div className="mt-3 p-2 bg-green-100 dark:bg-green-900/30 rounded border border-green-300 dark:border-green-600">
                  <p className="text-sm text-green-800">
                    ✓ {selectedTagIds.size} tag(s) selected
                  </p>
                </div>
              )}
            </div>
          </div>
      </form>
    </Modal>
  )
}
