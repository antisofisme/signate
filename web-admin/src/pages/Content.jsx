import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI, tagsAPI } from '../services/api'
import { Upload, FileImage, Trash2, Link as LinkIcon, Edit, CheckSquare, Square, ArrowRight, ArrowLeft, Tag } from 'lucide-react'
import VideoThumbnail from '../components/content/VideoThumbnail'
import AssignmentBadge from '../components/content/AssignmentBadge'
import UploadModal from '../components/content/modals/UploadModal'
import AssignModal from '../components/content/modals/AssignModal'
import PreviewModal from '../components/content/modals/PreviewModal'
import BulkEditModal from '../components/content/modals/BulkEditModal'
import BulkTagModal from '../components/content/modals/BulkTagModal'

// Helper function to get proxy image URL
const getImageUrl = (content) => {
  // Use backend proxy endpoint which serves images with correct Content-Type
  const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
  return `${baseUrl}/api/content/${content.id}/image`
}

export default function Content() {
  const queryClient = useQueryClient()
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [showBulkEditForm, setShowBulkEditForm] = useState(false)
  const [showBulkTagForm, setShowBulkTagForm] = useState(false)
  const [selectedContent, setSelectedContent] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())

  // Grouping state: 'none', 'extension', 'tag', 'device'
  const [groupBy, setGroupBy] = useState('none')
  const [expandedGroups, setExpandedGroups] = useState(new Set())

  // Fetch content
  const { data: contentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

  // Fetch tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch devices
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

  // Fetch all assignments to map content to tags/devices
  const { data: allAssignmentsData } = useQuery({
    queryKey: ['all-assignments'],
    queryFn: async () => {
      if (!contentData?.items) return {}

      const assignmentsMap = {}
      for (const content of contentData.items) {
        const res = await contentAPI.getAssignments(content.id)
        assignmentsMap[content.id] = res.data
      }
      return assignmentsMap
    },
    enabled: !!contentData?.items,
  })

  // Group content based on selected grouping mode
  const groupedContent = () => {
    if (!contentData?.items) return []

    if (groupBy === 'none') {
      return [{ name: 'All Content', items: contentData.items, key: 'all' }]
    }

    if (groupBy === 'extension') {
      const groups = {}
      contentData.items.forEach(content => {
        const mimeType = content.mime_type || 'unknown'
        const category = mimeType.startsWith('image/') ? 'Images'
                      : mimeType.startsWith('video/') ? 'Videos'
                      : 'Other'

        if (!groups[category]) {
          groups[category] = []
        }
        groups[category].push(content)
      })

      return Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: name.toLowerCase(),
        icon: name === 'Images' ? '🖼️' : name === 'Videos' ? '🎬' : '📄'
      }))
    }

    if (groupBy === 'tag' && allAssignmentsData) {
      const groups = {}
      const untagged = []

      contentData.items.forEach(content => {
        const assignments = allAssignmentsData[content.id] || []
        const contentTags = assignments.filter(a => a.tag_id).map(a => a.tag_id)

        if (contentTags.length === 0) {
          untagged.push(content)
        } else {
          contentTags.forEach(tagId => {
            const tag = tagsData?.items?.find(t => t.id === tagId)
            const tagName = tag?.tag_name || `Tag #${tagId}`

            if (!groups[tagName]) {
              groups[tagName] = []
            }
            groups[tagName].push(content)
          })
        }
      })

      const result = Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: `tag-${name}`,
        icon: '🏷️'
      }))

      if (untagged.length > 0) {
        result.push({ name: 'Untagged', items: untagged, key: 'untagged', icon: '❓' })
      }

      return result
    }

    if (groupBy === 'device' && allAssignmentsData) {
      const groups = {}
      const unassigned = []

      contentData.items.forEach(content => {
        const assignments = allAssignmentsData[content.id] || []
        const contentDevices = assignments.filter(a => a.device_id).map(a => a.device_id)

        if (contentDevices.length === 0) {
          unassigned.push(content)
        } else {
          contentDevices.forEach(deviceId => {
            const device = devicesData?.devices?.find(d => d.id === deviceId)
            const deviceName = device?.device_name || `Device #${deviceId}`

            if (!groups[deviceName]) {
              groups[deviceName] = []
            }
            groups[deviceName].push(content)
          })
        }
      })

      const result = Object.entries(groups).map(([name, items]) => ({
        name,
        items,
        key: `device-${name}`,
        icon: '📺'
      }))

      if (unassigned.length > 0) {
        result.push({ name: 'Unassigned', items: unassigned, key: 'unassigned', icon: '❓' })
      }

      return result
    }

    return []
  }

  const toggleGroup = (groupKey) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(groupKey)) {
        newSet.delete(groupKey)
      } else {
        newSet.add(groupKey)
      }
      return newSet
    })
  }

  const expandAllGroups = () => {
    const allKeys = groupedContent().map(g => g.key)
    setExpandedGroups(new Set(allKeys))
  }

  const collapseAllGroups = () => {
    setExpandedGroups(new Set())
  }

  // Upload content mutation
  const uploadMutation = useMutation({
    mutationFn: contentAPI.upload,
    onSuccess: () => {
      queryClient.invalidateQueries(['content'])
      setShowUploadForm(false)
      alert('Content uploaded successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Upload failed')
    }
  })

  // Assign content mutation
  const assignMutation = useMutation({
    mutationFn: ({ id, data }) => contentAPI.assign(id, data),
    onSuccess: (_, variables) => {
      // Invalidate assignments query to refresh the list
      queryClient.invalidateQueries(['content-assignments', variables.id])
      setShowAssignForm(false)
      alert('Content assigned successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Delete content mutation
  const deleteMutation = useMutation({
    mutationFn: contentAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['content'])
      alert('Content deleted successfully!')
    },
  })

  const handleAssign = (e, content) => {
    e.stopPropagation()
    setSelectedContent(content)
    setShowAssignForm(true)
  }

  const handlePreview = (content) => {
    setSelectedContent(content)
    setShowPreviewModal(true)
  }

  const toggleSelection = (contentId, e) => {
    e.stopPropagation()
    setSelectedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(contentId)) {
        newSet.delete(contentId)
      } else {
        newSet.add(contentId)
      }
      return newSet
    })
  }

  const toggleSelectAll = () => {
    const allContent = contentData?.items || []
    if (selectedIds.size === allContent.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(allContent.map(c => c.id)))
    }
  }

  const clearSelection = () => {
    setSelectedIds(new Set())
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-gray-800">Content</h1>
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-3">
              <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                {selectedIds.size} selected
              </span>
              <button
                onClick={clearSelection}
                className="text-sm text-gray-600 hover:text-gray-800 underline"
              >
                Clear
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          {contentData?.items?.length > 0 && (
            <button
              onClick={toggleSelectAll}
              className="flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              {selectedIds.size === contentData?.items?.length ? (
                <CheckSquare className="w-5 h-5 mr-2" />
              ) : (
                <Square className="w-5 h-5 mr-2" />
              )}
              {selectedIds.size === contentData?.items?.length ? 'Deselect All' : 'Select All'}
            </button>
          )}
          {selectedIds.size > 0 && (
            <>
              <button
                onClick={() => setShowBulkEditForm(true)}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Edit className="w-5 h-5 mr-2" />
                Bulk Edit ({selectedIds.size})
              </button>
              <button
                onClick={() => setShowBulkTagForm(true)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Tag className="w-5 h-5 mr-2" />
                Bulk Tag ({selectedIds.size})
              </button>
            </>
          )}
          <button
            onClick={() => setShowUploadForm(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload Content
          </button>
        </div>
      </div>

      {/* Grouping Section */}
      <div className="bg-white rounded-xl shadow-md p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Group by:</span>

            {/* Grouping Options */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setGroupBy('none')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  groupBy === 'none'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                None
              </button>
              <button
                onClick={() => {
                  setGroupBy('extension')
                  expandAllGroups()
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  groupBy === 'extension'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🖼️ Extension
              </button>
              <button
                onClick={() => {
                  setGroupBy('tag')
                  expandAllGroups()
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  groupBy === 'tag'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🏷️ Tag
              </button>
              <button
                onClick={() => {
                  setGroupBy('device')
                  expandAllGroups()
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  groupBy === 'device'
                    ? 'bg-orange-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📺 Device
              </button>
            </div>
          </div>

          {/* Expand/Collapse All */}
          {groupBy !== 'none' && (
            <div className="flex items-center gap-2">
              <button
                onClick={expandAllGroups}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
              >
                Expand All
              </button>
              <button
                onClick={collapseAllGroups}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
              >
                Collapse All
              </button>
            </div>
          )}

          {/* Total Count */}
          <div className="text-sm text-gray-600">
            {contentData?.items?.length || 0} content total
          </div>
        </div>
      </div>

      {/* Grouped Content */}
      {groupedContent().map((group) => (
        <div key={group.key} className="mb-6">
          {/* Group Header */}
          {groupBy !== 'none' && (
            <button
              onClick={() => toggleGroup(group.key)}
              className="w-full bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-300 rounded-lg px-4 py-3 mb-4 flex items-center justify-between hover:from-gray-100 hover:to-gray-200 transition-all"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{group.icon}</span>
                <h2 className="text-xl font-bold text-gray-800">{group.name}</h2>
                <span className="bg-white px-3 py-1 rounded-full text-sm font-medium text-gray-600 shadow-sm">
                  {group.items.length} items
                </span>
              </div>
              <div className="text-gray-600">
                {expandedGroups.has(group.key) ? '▼' : '▶'}
              </div>
            </button>
          )}

          {/* Group Content */}
          {(groupBy === 'none' || expandedGroups.has(group.key)) && (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {group.items.map((content) => (
          <div
            key={content.id}
            onClick={() => handlePreview(content)}
            className={`bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-all cursor-pointer relative ${
              selectedIds.has(content.id) ? 'ring-4 ring-blue-500' : ''
            }`}
          >
            {/* Checkbox for selection */}
            <div className="absolute top-2 left-2 z-10">
              <input
                type="checkbox"
                checked={selectedIds.has(content.id)}
                onChange={(e) => toggleSelection(content.id, e)}
                onClick={(e) => e.stopPropagation()}
                className="w-5 h-5 rounded border-2 border-white shadow-lg cursor-pointer accent-blue-600"
              />
            </div>

            {/* Preview Thumbnail */}
            <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
              {content.content_type === 'video' ? (
                <VideoThumbnail content={content} />
              ) : (
                <>
                  <img
                    src={getImageUrl(content)}
                    alt={content.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none'
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <FileImage className="w-16 h-16 text-gray-400 opacity-50" />
                  </div>
                </>
              )}

              {/* Badges */}
              <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
                {content.is_active && (
                  <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                    Active
                  </div>
                )}
                <AssignmentBadge contentId={content.id} />
              </div>
            </div>

            {/* Info */}
            <div className="p-3">
              <h3 className="font-bold text-gray-800 mb-1 text-sm truncate">{content.title}</h3>

              {/* Metadata */}
              <div className="space-y-1 mb-2">
                {content.resolution && (
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <span className="font-medium">📐</span>
                    <span>{content.resolution}</span>
                  </div>
                )}
                {content.codec && (
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <span className="font-medium">🎞️</span>
                    <span className="uppercase">{content.codec}</span>
                    {content.fps && <span>@ {content.fps}fps</span>}
                  </div>
                )}
                {content.bitrate && (
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <span className="font-medium">⚡</span>
                    <span>{content.bitrate} kbps</span>
                  </div>
                )}
                {content.file_size && (
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <span className="font-medium">💾</span>
                    <span>{(content.file_size / 1024 / 1024).toFixed(1)} MB</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-gray-500 mb-2 pt-2 border-t">
                <span className="font-medium">{content.content_type.toUpperCase()}</span>
                <span>{content.duration}s</span>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={(e) => handleAssign(e, content)}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                >
                  <Edit className="w-4 h-4 mr-1" />
                  Edit
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm('Delete this content?')) {
                      deleteMutation.mutate(content.id)
                    }
                  }}
                  className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {contentData?.items?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No content uploaded yet</p>
        </div>
      )}

      {/* Upload Form Modal */}
      {showUploadForm && <UploadModal onClose={() => setShowUploadForm(false)} onSubmit={uploadMutation.mutate} />}

      {/* Assign Form Modal */}
      {showAssignForm && <AssignModal content={selectedContent} onClose={() => setShowAssignForm(false)} onSubmit={assignMutation.mutate} />}

      {/* Preview Modal */}
      {showPreviewModal && selectedContent && (
        <PreviewModal content={selectedContent} onClose={() => setShowPreviewModal(false)} />
      )}

      {/* Bulk Edit Modal */}
      {showBulkEditForm && (
        <BulkEditModal
          selectedIds={selectedIds}
          contentData={contentData}
          onClose={() => setShowBulkEditForm(false)}
          onComplete={() => {
            setShowBulkEditForm(false)
            clearSelection()
          }}
        />
      )}

      {/* Bulk Tag Modal */}
      {showBulkTagForm && (
        <BulkTagModal
          selectedIds={selectedIds}
          contentData={contentData}
          onClose={() => setShowBulkTagForm(false)}
          onComplete={() => {
            setShowBulkTagForm(false)
            clearSelection()
          }}
        />
      )}
    </div>
  )
}
