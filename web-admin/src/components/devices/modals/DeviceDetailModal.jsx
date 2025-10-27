import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI, tagsAPI, playlistsAPI, contentAPI } from '../../../services/api'
import { Modal, ModalFooter, Button } from '../../shared'
import { Tv, Monitor, X, Edit, FileText, Trash2, Plus, Tag as TagIcon, List, Wifi, WifiOff, Circle, Eye, Film, Activity, Download, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import SpeedHistoryModal from './SpeedHistoryModal'

/**
 * DeviceDetailModal Component
 * Comprehensive modal for viewing and managing device details
 *
 * Features:
 * - Device basic information (type, IP, status, specs)
 * - Online/Offline status indicator
 * - Assigned tags with add/remove functionality
 * - Assigned playlists with add/remove functionality
 * - Quick actions (Edit, View Logs, Delete)
 * - Visual design with gradient header and organized sections
 *
 * @param {Object} device - Device object to display/manage
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onEdit - Callback when edit button is clicked
 * @param {Function} onViewLogs - Callback when view logs button is clicked
 * @param {Function} onDelete - Callback when delete button is clicked
 */
export default function DeviceDetailModal({ device: initialDevice, onClose, onEdit, onViewLogs, onDelete }) {
  const queryClient = useQueryClient()
  const [showTagSelector, setShowTagSelector] = useState(false)
  const [showPlaylistSelector, setShowPlaylistSelector] = useState(false)
  const [showContentSelector, setShowContentSelector] = useState(false)
  const [showSpeedHistory, setShowSpeedHistory] = useState(false)

  // Fetch current device data (will auto-update on invalidation)
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

  // Get current device from devices list (auto-updates when invalidated)
  const device = useMemo(() => {
    return devicesData?.devices?.find(d => d.id === initialDevice.id) || initialDevice
  }, [devicesData, initialDevice.id])

  // Fetch all available tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch all available playlists
  const { data: playlistsData } = useQuery({
    queryKey: ['playlists'],
    queryFn: () => playlistsAPI.list().then(res => res.data),
  })

  // Fetch all available content
  const { data: allContentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Fetch device content assignments
  const { data: deviceContentData } = useQuery({
    queryKey: ['devices', device.id, 'content'],
    queryFn: () => devicesAPI.getContent(device.id).then(res => res.data),
  })

  // Fetch tag content for all device tags (for inheritance display)
  const tagContentQueries = useQuery({
    queryKey: ['devices', device.id, 'tag-content', device.tags?.map(t => t.id).sort().join(',')],
    queryFn: async () => {
      console.log('🔍 Fetching tag content for device', device.id, 'with tags:', device.tags?.map(t => t.tag_name))
      if (!device.tags || device.tags.length === 0) {
        console.log('⚠️ No tags found, returning empty array')
        return []
      }
      const promises = device.tags.map(tag =>
        tagsAPI.getContent(tag.id).then(res => {
          console.log(`✅ Tag "${tag.tag_name}" (${tag.id}) content:`, res.data.length, 'items')
          return {
            tag,
            content: res.data
          }
        })
      )
      const results = await Promise.all(promises)
      console.log('📦 Total tag content results:', results)
      return results
    },
    enabled: device.tags && device.tags.length > 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  })

  // Watch for changes in device tags and refetch tag content
  useEffect(() => {
    console.log('🔄 Device tags changed, triggering tag content refetch')
    console.log('   Current tags:', device.tags?.map(t => t.tag_name))
    if (device.tags && device.tags.length > 0) {
      tagContentQueries.refetch()
    }
  }, [device.tags?.map(t => t.id).sort().join(',')])

  // Fetch speed test history for this device (last 10 tests for chart)
  const { data: speedTestHistoryData, isLoading: isLoadingSpeedTest } = useQuery({
    queryKey: ['devices', device.id, 'speedtest', 'history-chart'],
    queryFn: () => devicesAPI.getSpeedTests(device.id, 10).then(res => res.data),
    retry: false, // Don't retry if no speed test data exists
    refetchInterval: 60000, // Auto-refresh every 60 seconds
  })

  // Assign tag mutation
  const assignTagMutation = useMutation({
    mutationFn: (tagId) => {
      console.log('🏷️ Assigning tag', tagId, 'to device', device.id)
      return tagsAPI.assign({ device_id: device.id, tag_id: tagId })
    },
    onSuccess: () => {
      console.log('✅ Tag assigned successfully, invalidating devices query...')
      // Invalidate devices query - useEffect will handle tag content refetch
      queryClient.invalidateQueries(['devices'])
      toast.success('Tag assigned!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to assign tag', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Unassign tag mutation
  const unassignTagMutation = useMutation({
    mutationFn: (tagId) => {
      console.log('🗑️ Removing tag', tagId, 'from device', device.id)
      return tagsAPI.unassign({ device_id: device.id, tag_id: tagId })
    },
    onSuccess: () => {
      console.log('✅ Tag removed successfully, invalidating devices query...')
      // Invalidate devices query - useEffect will handle tag content refetch
      queryClient.invalidateQueries(['devices'])
      toast.success('Tag removed!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to remove tag', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Assign playlist mutation
  const assignPlaylistMutation = useMutation({
    mutationFn: (playlistId) => playlistsAPI.assignToDevices(playlistId, { device_ids: [device.id] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      toast.success('Playlist assigned!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to assign playlist', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Unassign playlist mutation
  const unassignPlaylistMutation = useMutation({
    mutationFn: (playlistId) => playlistsAPI.unassignFromDevices(playlistId, { device_ids: [device.id] }),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices'])
      toast.success('Playlist removed!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to remove playlist', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Assign content mutation
  const assignContentMutation = useMutation({
    mutationFn: ({ contentId, priority }) => devicesAPI.assignContent(device.id, contentId, priority),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices', device.id, 'content'])
      toast.success('Content assigned!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to assign content', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Unassign content mutation
  const unassignContentMutation = useMutation({
    mutationFn: (contentId) => devicesAPI.unassignContent(device.id, contentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['devices', device.id, 'content'])
      toast.success('Content removed!', {
        duration: 3000,
        position: 'bottom-right',
      })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to remove content', {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  })

  // Run speed test handler
  const handleRunSpeedTest = async () => {
    try {
      await devicesAPI.queueCommand(device.id, {
        command_type: 'run_speed_test',
        reason: 'Manual speed test triggered from web admin'
      })
      toast.success('Speed test command queued successfully. Results will appear in 15-20 seconds.', {
        duration: 4000,
        position: 'bottom-right',
      })

      // Auto-refresh speed test data after speed test completes (estimated 15 seconds)
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['devices', device.id, 'speedtest'] })
        console.log('[DeviceDetail] Invalidated speed test cache after manual test')
      }, 15000)
    } catch (error) {
      console.error('Failed to queue speed test command:', error)
      toast.error(`Failed to run speed test: ${error.response?.data?.detail || error.message}`, {
        duration: 4000,
        position: 'bottom-right',
      })
    }
  }

  // Check if device is online (last_seen within 60 seconds)
  const isOnline = (() => {
    if (!device.last_seen) return false
    // Backend sends UTC timestamps without 'Z', add it to ensure correct parsing
    const utcLastSeen = device.last_seen.endsWith('Z') ? device.last_seen : device.last_seen + 'Z'
    const lastSeenTime = new Date(utcLastSeen).getTime()
    const now = Date.now()
    const timeout = 60000 // 60 seconds (2x heartbeat interval of 30s)
    const diff = now - lastSeenTime
    return diff < timeout
  })()

  // Get available tags (not yet assigned)
  const assignedTagIds = device.tags?.map(t => t.id) || []
  const availableTags = tagsData?.items?.filter(t => !assignedTagIds.includes(t.id)) || []

  // Get available playlists (not yet assigned)
  const assignedPlaylistIds = device.playlists?.map(p => p.id) || []
  const availablePlaylists = playlistsData?.items?.filter(p => !assignedPlaylistIds.includes(p.id)) || []

  // Get available content (not yet assigned to device)
  const assignedContentIds = deviceContentData?.map(c => c.content_id) || []
  const availableContent = allContentData?.items?.filter(c => !assignedContentIds.includes(c.id)) || []

  // Determine if device is TV based on platform
  const isTv = device.platform && ['webOS', 'Tizen', 'Android TV'].includes(device.platform)

  return (
    <>
    <Modal
      isOpen={true}
      onClose={onClose}
      size="2xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom header with gradient and icon - Fixed */}
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          {isTv ? (
            <Tv className="w-6 h-6 text-blue-600" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600" />
          )}
          <div>
            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{device.device_name}</h2>
            <div className="flex items-center gap-2 mt-1">
              {isOnline ? (
                <>
                  <Circle className="w-3 h-3 text-green-500 fill-green-500" />
                  <span className="text-sm text-green-600 font-medium">Online</span>
                </>
              ) : (
                <>
                  <Circle className="w-3 h-3 text-red-500 fill-red-500" />
                  <span className="text-sm text-red-600 font-medium">Offline</span>
                </>
              )}
            </div>
          </div>
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
        {/* Quick Actions Bar */}
        <div className="flex gap-2 mb-6 pb-6 border-b">
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Edit className="w-4 h-4" />}
            onClick={() => {
              onClose()
              onEdit(device)
            }}
          >
            Edit Device
          </Button>
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<FileText className="w-4 h-4" />}
            onClick={() => {
              onClose()
              onViewLogs(device)
            }}
          >
            View Logs
          </Button>
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Activity className="w-4 h-4" />}
            onClick={() => setShowSpeedHistory(true)}
          >
            Speed History
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Eye className="w-4 h-4" />}
            onClick={() => {
              window.open(`/devices/${device.id}/preview`, '_blank')
            }}
          >
            Preview
          </Button>
          <Button
            variant="danger"
            size="sm"
            leftIcon={<Trash2 className="w-4 h-4" />}
            onClick={() => {
              if (confirm(`Delete device "${device.device_name}"?`)) {
                onDelete(device.id)
                onClose()
              }
            }}
          >
            Delete
          </Button>
        </div>

        {/* Tags Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <TagIcon className="w-5 h-5 text-purple-600" />
              Tags
            </h3>
            <button
              onClick={() => setShowTagSelector(!showTagSelector)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              {showTagSelector ? 'Cancel' : '+ Add Tag'}
            </button>
          </div>

          {/* Tag Selector (when adding) */}
          {showTagSelector && availableTags.length > 0 && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2 font-medium">Select a tag to add:</p>
              <div className="flex flex-wrap gap-2">
                {availableTags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => {
                      assignTagMutation.mutate(tag.id)
                      setShowTagSelector(false)
                    }}
                    className="px-3 py-1 rounded-full text-sm font-medium text-white hover:opacity-80 transition-opacity"
                    style={{ backgroundColor: tag.color || '#6B7280' }}
                  >
                    {tag.tag_name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Assigned Tags */}
          {device.tags && device.tags.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {device.tags.map(tag => (
                <div
                  key={tag.id}
                  className="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium text-white"
                  style={{ backgroundColor: tag.color || '#6B7280' }}
                >
                  <span>{tag.tag_name}</span>
                  <button
                    onClick={() => unassignTagMutation.mutate(tag.id)}
                    className="hover:bg-white/20 rounded-full p-0.5 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No tags assigned</p>
          )}
        </div>

        {/* Playlists Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <List className="w-5 h-5 text-indigo-600" />
              Playlists
            </h3>
            <button
              onClick={() => setShowPlaylistSelector(!showPlaylistSelector)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              {showPlaylistSelector ? 'Cancel' : '+ Add Playlist'}
            </button>
          </div>

          {/* Playlist Selector (when adding) */}
          {showPlaylistSelector && availablePlaylists.length > 0 && (
            <div className="mb-3 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2 font-medium">Select a playlist to add:</p>
              <div className="space-y-2">
                {availablePlaylists.map(playlist => (
                  <button
                    key={playlist.id}
                    onClick={() => {
                      assignPlaylistMutation.mutate(playlist.id)
                      setShowPlaylistSelector(false)
                    }}
                    className="w-full text-left px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800 dark:text-gray-100">{playlist.name}</span>
                      {playlist.is_active && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">Active</span>
                      )}
                    </div>
                    {playlist.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{playlist.description}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Assigned Playlists */}
          {device.playlists && device.playlists.length > 0 ? (
            <div className="space-y-2">
              {device.playlists.map(playlist => (
                <div
                  key={playlist.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800 dark:text-gray-100">{playlist.name}</span>
                      {playlist.is_active && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">Active</span>
                      )}
                      <span className="text-xs text-gray-500 dark:text-gray-400">Priority: {playlist.priority}</span>
                    </div>
                    {playlist.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{playlist.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => unassignPlaylistMutation.mutate(playlist.id)}
                    className="text-red-500 hover:bg-red-50 rounded-lg p-2 transition-colors"
                    title="Remove playlist"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No playlists assigned</p>
          )}
        </div>

        {/* Content Section */}
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Film className="w-5 h-5 text-pink-600" />
            Content
          </h3>

          {/* Direct Assignments Subsection */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700 dark:text-gray-300">Direct Assignments</h4>
              <button
                onClick={() => setShowContentSelector(!showContentSelector)}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                {showContentSelector ? 'Cancel' : '+ Add Content'}
              </button>
            </div>

            {/* Content Selector (when adding) */}
            {showContentSelector && availableContent.length > 0 && (
              <div className="mb-3 p-3 bg-pink-50 rounded-lg border border-pink-200">
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2 font-medium">Select content to add:</p>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {availableContent.map(content => (
                    <button
                      key={content.id}
                      onClick={() => {
                        assignContentMutation.mutate({
                          contentId: content.id,
                          priority: 0
                        })
                        setShowContentSelector(false)
                      }}
                      className="w-full text-left px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-pink-500 hover:bg-pink-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <span className="font-medium text-gray-800 dark:text-gray-100">{content.title}</span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                              {content.content_type}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">{content.duration}s</span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Assigned Content */}
            {deviceContentData && deviceContentData.length > 0 ? (
              <div className="space-y-2">
                {deviceContentData
                  .sort((a, b) => a.display_order - b.display_order)
                  .map((assignment) => (
                  <div
                    key={assignment.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-800 dark:text-gray-100">
                          {assignment.content?.title || `Content #${assignment.content_id}`}
                        </span>
                        {!assignment.is_active && (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">Inactive</span>
                        )}
                        <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
                          Priority: {assignment.priority}
                        </span>
                      </div>
                      {assignment.content && (
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                            {assignment.content.content_type}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">{assignment.content.duration}s</span>
                          {assignment.notes && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">• {assignment.notes}</span>
                          )}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => unassignContentMutation.mutate(assignment.content_id)}
                      className="text-red-500 hover:bg-red-50 rounded-lg p-2 transition-colors ml-2"
                      title="Remove content"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">No direct content assigned</p>
            )}
          </div>

          {/* Tag-based Content Subsection (Read-only) */}
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Inherited from Tags</h4>
            {tagContentQueries.data && tagContentQueries.data.length > 0 ? (
              <div className="space-y-3">
                {tagContentQueries.data.map(({ tag, content }) => (
                  <div key={tag.id} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: tag.color || '#6B7280' }}
                      >
                        {tag.tag_name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {content && content.length > 0
                          ? `${content.length} content item${content.length !== 1 ? 's' : ''}`
                          : 'No content'
                        }
                      </span>
                    </div>
                    {content && content.length > 0 ? (
                      <div className="space-y-1">
                        {content.slice(0, 3).map((assignment) => (
                          <div key={assignment.id} className="text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                            <span>{assignment.content?.title || `Content #${assignment.content_id}`}</span>
                            {assignment.content && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                ({assignment.content.content_type}, {assignment.content.duration}s)
                              </span>
                            )}
                          </div>
                        ))}
                        {content.length > 3 && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 ml-4">
                            +{content.length - 3} more...
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic ml-4">
                        No content assigned to this tag
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">No tags assigned to this device</p>
            )}
          </div>
        </div>

        {/* Device Information Section */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4">Device Information</h3>
          <div className="space-y-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 rounded-lg p-4">
            <div className="flex items-center">
              <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Device ID:</span>
              <span className="text-gray-900 dark:text-white font-mono">{device.id}</span>
            </div>
            <div className="flex items-center">
              <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Platform:</span>
              <span className="text-gray-900 dark:text-white">{device.platform || device.device_type.charAt(0).toUpperCase() + device.device_type.slice(1)}</span>
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
            {device.screen_width && device.screen_height && (
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700 dark:text-gray-300">Screen Resolution:</span>
                <span className="text-gray-900 dark:text-white">{device.screen_width}x{device.screen_height}</span>
              </div>
            )}
          </div>

          {/* Network Speed Section */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-md font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                Network Speed History
              </h4>
              <Button
                onClick={handleRunSpeedTest}
                variant="success"
                size="sm"
                disabled={device.status !== 'active'}
                title={device.status !== 'active' ? 'Device must be active to run speed test' : 'Run network speed test'}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                }
              >
                Run Speed Test
              </Button>
            </div>
            {isLoadingSpeedTest ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                Loading speed test data...
              </div>
            ) : speedTestHistoryData && speedTestHistoryData.total > 0 ? (
              <div>
                {/* Latest Speed Stats */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <Download className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Latest Download</span>
                    </div>
                    <div className="text-xl font-bold text-green-700 dark:text-green-400">
                      {speedTestHistoryData.items[0].download_speed.toFixed(2)} Mbps
                    </div>
                  </div>
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <Upload className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Latest Upload</span>
                    </div>
                    <div className="text-xl font-bold text-blue-700 dark:text-blue-400">
                      {speedTestHistoryData.items[0].upload_speed.toFixed(2)} Mbps
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Quality</div>
                    <div className={`inline-block px-2 py-1 rounded text-sm font-medium ${
                      speedTestHistoryData.items[0].quality === 'good' ? 'bg-green-200 dark:bg-green-900/50 text-green-800 dark:text-green-300' :
                      speedTestHistoryData.items[0].quality === 'fair' ? 'bg-yellow-200 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300' :
                      'bg-red-200 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                    }`}>
                      {speedTestHistoryData.items[0].quality}
                    </div>
                  </div>
                </div>

                {/* Speed Chart */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart
                      data={speedTestHistoryData.items.map(test => ({
                        time: new Date(test.tested_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        download: parseFloat(test.download_speed.toFixed(2)),
                        upload: parseFloat(test.upload_speed.toFixed(2)),
                      })).reverse()}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                      <XAxis
                        dataKey="time"
                        className="text-xs fill-gray-600 dark:fill-gray-400"
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis
                        label={{ value: 'Mbps', angle: -90, position: 'insideLeft', className: 'fill-gray-600 dark:fill-gray-400' }}
                        className="text-xs fill-gray-600 dark:fill-gray-400"
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: '1px solid #e5e7eb',
                          borderRadius: '0.5rem',
                          fontSize: '0.875rem'
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '0.875rem' }} />
                      <Line
                        type="monotone"
                        dataKey="download"
                        stroke="#16a34a"
                        strokeWidth={2}
                        name="Download"
                        dot={{ fill: '#16a34a', r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="upload"
                        stroke="#2563eb"
                        strokeWidth={2}
                        name="Upload"
                        dot={{ fill: '#2563eb', r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Quality Info */}
                <div className="mt-3 text-xs text-gray-500 dark:text-gray-400 flex items-center justify-between">
                  <div>Last tested: {new Date(speedTestHistoryData.items[0].tested_at).toLocaleString()}</div>
                  <div className="flex gap-4">
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-green-500 rounded"></span>
                      Good: ≥25/10
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-yellow-500 rounded"></span>
                      Fair: ≥10/5
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 bg-red-500 rounded"></span>
                      Poor: &lt;10/5
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No speed test data available</p>
                <p className="text-sm mt-1">Viewer will perform speed test every 30 minutes</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer - Fixed */}
      <div className="p-6 border-t bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 flex-shrink-0">
        <ModalFooter align="right">
          <Button onClick={onClose} variant="primary" className="min-w-[120px]">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>

    {/* Speed History Modal */}
    {showSpeedHistory && (
      <SpeedHistoryModal
        device={device}
        onClose={() => setShowSpeedHistory(false)}
      />
    )}
  </>
  )
}
