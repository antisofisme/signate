import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesAPI, tagsAPI, playlistsAPI, contentAPI } from '../../../services/api'
import { Modal, ModalFooter, Button } from '../../shared'
import { Tv, Monitor, X, Edit, FileText, Trash2, Plus, Tag as TagIcon, List, Wifi, WifiOff, Circle, Eye, Film } from 'lucide-react'
import toast from 'react-hot-toast'

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
    mutationFn: (data) => devicesAPI.assignContent(device.id, data),
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
        <div className="flex items-center gap-3">
          {device.device_uuid ? (
            <Tv className="w-6 h-6 text-blue-600" />
          ) : (
            <Monitor className="w-6 h-6 text-green-600" />
          )}
          <div>
            <h2 className="text-2xl font-bold text-gray-800">{device.device_name}</h2>
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
          className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
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
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
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
              <p className="text-sm text-gray-700 mb-2 font-medium">Select a tag to add:</p>
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
            <p className="text-sm text-gray-500 italic">No tags assigned</p>
          )}
        </div>

        {/* Playlists Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
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
              <p className="text-sm text-gray-700 mb-2 font-medium">Select a playlist to add:</p>
              <div className="space-y-2">
                {availablePlaylists.map(playlist => (
                  <button
                    key={playlist.id}
                    onClick={() => {
                      assignPlaylistMutation.mutate(playlist.id)
                      setShowPlaylistSelector(false)
                    }}
                    className="w-full text-left px-3 py-2 bg-white rounded-lg border border-gray-200 hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800">{playlist.name}</span>
                      {playlist.is_active && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">Active</span>
                      )}
                    </div>
                    {playlist.description && (
                      <p className="text-xs text-gray-500 mt-1">{playlist.description}</p>
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
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800">{playlist.name}</span>
                      {playlist.is_active && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">Active</span>
                      )}
                      <span className="text-xs text-gray-500">Priority: {playlist.priority}</span>
                    </div>
                    {playlist.description && (
                      <p className="text-xs text-gray-500 mt-1">{playlist.description}</p>
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
            <p className="text-sm text-gray-500 italic">No playlists assigned</p>
          )}
        </div>

        {/* Content Section */}
        <div className="mb-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Film className="w-5 h-5 text-pink-600" />
            Content
          </h3>

          {/* Direct Assignments Subsection */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">Direct Assignments</h4>
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
                <p className="text-sm text-gray-700 mb-2 font-medium">Select content to add:</p>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {availableContent.map(content => (
                    <button
                      key={content.id}
                      onClick={() => {
                        assignContentMutation.mutate({
                          content_id: content.id,
                          display_order: (deviceContentData?.length || 0),
                          is_active: true
                        })
                        setShowContentSelector(false)
                      }}
                      className="w-full text-left px-3 py-2 bg-white rounded-lg border border-gray-200 hover:border-pink-500 hover:bg-pink-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <span className="font-medium text-gray-800">{content.title}</span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                              {content.content_type}
                            </span>
                            <span className="text-xs text-gray-500">{content.duration}s</span>
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
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-800">
                          {assignment.content?.title || `Content #${assignment.content_id}`}
                        </span>
                        {!assignment.is_active && (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">Inactive</span>
                        )}
                        <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                          Priority: {assignment.priority}
                        </span>
                      </div>
                      {assignment.content && (
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                            {assignment.content.content_type}
                          </span>
                          <span className="text-xs text-gray-500">{assignment.content.duration}s</span>
                          {assignment.notes && (
                            <span className="text-xs text-gray-500">• {assignment.notes}</span>
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
              <p className="text-sm text-gray-500 italic">No direct content assigned</p>
            )}
          </div>

          {/* Tag-based Content Subsection (Read-only) */}
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-700 mb-3">Inherited from Tags</h4>
            {tagContentQueries.data && tagContentQueries.data.length > 0 ? (
              <div className="space-y-3">
                {tagContentQueries.data.map(({ tag, content }) => (
                  <div key={tag.id} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: tag.color || '#6B7280' }}
                      >
                        {tag.tag_name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {content && content.length > 0
                          ? `${content.length} content item${content.length !== 1 ? 's' : ''}`
                          : 'No content'
                        }
                      </span>
                    </div>
                    {content && content.length > 0 ? (
                      <div className="space-y-1">
                        {content.slice(0, 3).map((assignment) => (
                          <div key={assignment.id} className="text-sm text-gray-700 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                            <span>{assignment.content?.title || `Content #${assignment.content_id}`}</span>
                            {assignment.content && (
                              <span className="text-xs text-gray-500">
                                ({assignment.content.content_type}, {assignment.content.duration}s)
                              </span>
                            )}
                          </div>
                        ))}
                        {content.length > 3 && (
                          <p className="text-xs text-gray-500 ml-4">
                            +{content.length - 3} more...
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500 italic ml-4">
                        No content assigned to this tag
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">No tags assigned to this device</p>
            )}
          </div>
        </div>

        {/* Device Information Section */}
        <div className="border-t pt-6">
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
              <span className="text-gray-900 font-mono">{device.ip_address || '-'}</span>
            </div>
            {device.device_uuid && (
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Device UUID:</span>
                <span className="text-gray-900 font-mono text-sm bg-blue-50 px-2 py-1 rounded">
                  {device.device_uuid}
                </span>
              </div>
            )}
            {device.unique_code && (
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Activation Code:</span>
                <span className="text-gray-900 font-mono font-bold text-lg text-green-600">
                  {device.unique_code}
                </span>
              </div>
            )}
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
            {device.screen_width && device.screen_height && (
              <div className="flex items-center">
                <span className="w-48 font-medium text-gray-700">Screen Resolution:</span>
                <span className="text-gray-900">{device.screen_width}x{device.screen_height}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer - Fixed */}
      <div className="p-6 border-t bg-gray-50 flex-shrink-0">
        <ModalFooter align="right">
          <Button onClick={onClose} variant="primary" className="min-w-[120px]">
            Close
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
