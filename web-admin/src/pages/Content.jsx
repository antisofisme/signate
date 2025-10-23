import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI, tagsAPI } from '../services/api'
import { Upload, FileImage, Trash2, Link as LinkIcon, Edit, CheckSquare, Square, ArrowRight, ArrowLeft, Tag } from 'lucide-react'

// Helper function to get proxy image URL
const getImageUrl = (content) => {
  // Use backend proxy endpoint which serves images with correct Content-Type
  const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
  return `${baseUrl}/api/content/${content.id}/image`
}

// Helper function to get proxy video URL
const getVideoUrl = (content) => {
  // Use backend proxy endpoint which serves videos with correct Content-Type and avoids CORS issues
  const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
  return `${baseUrl}/api/content/${content.id}/video`
}

// VideoThumbnail component with error handling and fallback
function VideoThumbnail({ content }) {
  const [hasError, setHasError] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const videoUrl = getVideoUrl(content)

  if (hasError) {
    // Show fallback icon if video fails to load
    return (
      <>
        <div className="flex flex-col items-center justify-center">
          <svg className="w-16 h-16 text-gray-400 mb-2" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
          </svg>
          <span className="text-xs text-gray-500">Video</span>
        </div>
        {/* Play icon overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-black bg-opacity-50 rounded-full p-4">
            <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      {/* Video element with error handling */}
      <video
        src={videoUrl}
        className="w-full h-full object-cover"
        preload="metadata"
        muted
        playsInline
        onLoadedMetadata={(e) => {
          // Successfully loaded metadata, seek to first frame
          try {
            e.target.currentTime = 0.1
            setIsLoaded(true)
          } catch (err) {
            console.error('Error seeking video:', err)
            setHasError(true)
          }
        }}
        onError={(e) => {
          console.error('Video load error for content:', content.id, videoUrl, e)
          setHasError(true)
        }}
        style={{ display: isLoaded || !hasError ? 'block' : 'none' }}
      />

      {/* Loading placeholder while video loads */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center">
            <svg className="w-12 h-12 text-gray-400 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
            </svg>
          </div>
        </div>
      )}

      {/* Play icon overlay */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="bg-black bg-opacity-50 rounded-full p-4">
          <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>
    </>
  )
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
      {showUploadForm && <UploadForm onClose={() => setShowUploadForm(false)} onSubmit={uploadMutation.mutate} />}

      {/* Assign Form Modal */}
      {showAssignForm && <AssignForm content={selectedContent} onClose={() => setShowAssignForm(false)} onSubmit={assignMutation.mutate} />}

      {/* Preview Modal */}
      {showPreviewModal && selectedContent && (
        <PreviewModal content={selectedContent} onClose={() => setShowPreviewModal(false)} />
      )}

      {/* Bulk Edit Modal */}
      {showBulkEditForm && (
        <BulkEditForm
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
        <BulkTagForm
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

// Small component to display assignment count badge
function AssignmentBadge({ contentId }) {
  const { data: assignmentsData } = useQuery({
    queryKey: ['content-assignments', contentId],
    queryFn: () => contentAPI.getAssignments(contentId).then(res => res.data),
  })

  const count = assignmentsData?.length || 0

  if (count === 0) return null

  return (
    <div className="bg-purple-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
      <LinkIcon className="w-3 h-3" />
      {count}
    </div>
  )
}

function UploadForm({ onClose, onSubmit }) {
  const queryClient = useQueryClient()
  const [files, setFiles] = useState([])
  const [duration, setDuration] = useState(10)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState([])

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files)
    setFiles(selectedFiles)
    // Initialize progress for each file
    setUploadProgress(selectedFiles.map(() => ({ status: 'pending', error: null })))
  }

  const handleBulkUpload = async (e) => {
    e.preventDefault()
    if (files.length === 0) {
      alert('Please select at least one file')
      return
    }

    setUploading(true)
    let successCount = 0
    let failCount = 0

    // Upload all files in parallel
    const uploadPromises = files.map(async (file, index) => {
      try {
        // Update status to uploading
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'uploading', error: null }
          return newProgress
        })

        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name.split('.')[0]) // Use filename as title
        formData.append('description', '')
        formData.append('duration', duration)
        formData.append('is_active', 'true')

        await contentAPI.upload(formData)

        // Update status to success
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'success', error: null }
          return newProgress
        })
        successCount++
      } catch (error) {
        // Update status to failed
        setUploadProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = {
            status: 'failed',
            error: error.response?.data?.detail || 'Upload failed'
          }
          return newProgress
        })
        failCount++
      }
    })

    // Wait for all uploads to complete
    await Promise.all(uploadPromises)

    // Refresh content list
    queryClient.invalidateQueries(['content'])

    setUploading(false)

    // Show summary
    alert(`Upload complete!\n✅ Success: ${successCount}\n❌ Failed: ${failCount}`)

    if (successCount > 0) {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] flex flex-col">
        <h2 className="text-xl font-bold mb-4">Upload Content</h2>

        <form onSubmit={handleBulkUpload} className="flex-1 flex flex-col space-y-4 overflow-hidden">
          {/* File Input */}
          <div>
            <label className="block text-sm font-medium mb-1">Select Files</label>
            <input
              type="file"
              accept="image/*,video/*"
              multiple
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border rounded-lg"
              disabled={uploading}
            />
            <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs font-semibold text-blue-800 mb-1">📋 Supported File Formats:</p>
              <div className="text-xs text-blue-700 space-y-1">
                <p><strong>Images:</strong> .jpg, .jpeg, .png, .gif, .bmp</p>
                <p><strong>Videos:</strong> .mp4 (H264 MPEG4, max 1920x1080 @ 30FPS)</p>
              </div>
              <p className="text-xs text-gray-600 mt-2 italic">💡 You can select multiple files to upload at once</p>
            </div>
          </div>

          {/* Duration Setting */}
          <div>
            <label className="block text-sm font-medium mb-1">Default Duration (seconds)</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-lg"
              min={1}
              disabled={uploading}
            />
            <p className="text-xs text-gray-500 mt-1">This duration will be applied to all files</p>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="flex-1 overflow-hidden flex flex-col">
              <h3 className="text-sm font-medium mb-2">Selected Files ({files.length})</h3>
              <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="ml-3 flex items-center gap-2">
                      {uploadProgress[index]?.status === 'pending' && (
                        <span className="text-gray-400">⏳</span>
                      )}
                      {uploadProgress[index]?.status === 'uploading' && (
                        <span className="text-blue-500 animate-spin">🔄</span>
                      )}
                      {uploadProgress[index]?.status === 'success' && (
                        <span className="text-green-500">✅</span>
                      )}
                      {uploadProgress[index]?.status === 'failed' && (
                        <span className="text-red-500" title={uploadProgress[index]?.error}>
                          ❌
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={uploading || files.length === 0}
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {uploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {uploading ? 'Please wait...' : 'Cancel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function AssignForm({ content, onClose, onSubmit }) {
  const queryClient = useQueryClient()
  const [saving, setSaving] = useState(false)

  // State for content metadata
  const [title, setTitle] = useState(content.title)
  const [description, setDescription] = useState(content.description || '')
  const [duration, setDuration] = useState(content.duration)

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

  // State for initial assignments (to track what to add/remove)
  const [initialDeviceIds, setInitialDeviceIds] = useState(new Set())
  const [initialTagIds, setInitialTagIds] = useState(new Set())

  // Pre-populate selections when assignments load
  // Using useEffect instead of useState for side effects
  const [initialized, setInitialized] = useState(false)

  if (assignmentsData && !assignmentsLoading && !initialized) {
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
    setInitialized(true)
  }

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
      if (title !== content.title || description !== (content.description || '') || duration !== content.duration) {
        await contentAPI.update(content.id, {
          title,
          description,
          duration: parseInt(duration)
        })
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
          priority: 0
        })
      }

      // Add new tag assignments
      for (const tagId of tagsToAdd) {
        await contentAPI.assign(content.id, {
          tag_id: tagId,
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
      alert('Content updated successfully!')
      onClose()
    } catch (error) {
      setSaving(false)
      alert(error.response?.data?.detail || 'Failed to update content')
    }
  }

  if (assignmentsLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-2xl">
          <p className="text-center text-gray-600">Loading assignments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Edit Content</h2>
            <p className="text-sm text-gray-600 mt-1">Edit content details and assignments</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
            disabled={saving}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Content Details Section */}
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">✏️</span>
                <h3 className="font-bold text-gray-800 text-lg">Content Details</h3>
              </div>

              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={saving}
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                    disabled={saving}
                  />
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Duration (seconds)
                  </label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={saving}
                    min="1"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Devices Section */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">📱</span>
                <h3 className="font-bold text-gray-800 text-lg">Devices</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Select devices to assign this content to
              </p>
              {devicesData?.devices && devicesData.devices.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {devicesData.devices.map((device) => (
                    <label
                      key={device.id}
                      className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedDeviceIds.has(device.id)
                          ? 'bg-blue-100 border-blue-500 shadow-md'
                          : 'bg-white border-gray-200 hover:border-blue-300 hover:bg-blue-50'
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
                        <span className="text-sm font-medium text-gray-800 block truncate">
                          {device.device_name}
                        </span>
                        <span className="text-xs text-gray-500 block">
                          {device.device_type.toUpperCase()}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-500 text-sm">
                  No active devices available
                </div>
              )}
              {selectedDeviceIds.size > 0 && (
                <div className="mt-3 p-2 bg-blue-100 rounded border border-blue-300">
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
                <h3 className="font-bold text-gray-800 text-lg">Tags</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Select tags to assign this content to (affects all devices with these tags)
              </p>
              {tagsData?.items && tagsData.items.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {tagsData.items.map((tag) => (
                    <label
                      key={tag.id}
                      className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedTagIds.has(tag.id)
                          ? 'bg-green-100 border-green-500 shadow-md'
                          : 'bg-white border-gray-200 hover:border-green-300 hover:bg-green-50'
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
                        <span className="text-sm font-medium text-gray-800 block truncate">
                          {tag.tag_name}
                        </span>
                        {tag.description && (
                          <span className="text-xs text-gray-500 block truncate">
                            {tag.description}
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-500 text-sm">
                  No tags available
                </div>
              )}
              {selectedTagIds.size > 0 && (
                <div className="mt-3 p-2 bg-green-100 rounded border border-green-300">
                  <p className="text-sm text-green-800">
                    ✓ {selectedTagIds.size} tag(s) selected
                  </p>
                </div>
              )}
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={saving}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {saving ? 'Please wait...' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}

// VideoPlayer component for modal with better error handling
function ModalVideoPlayer({ content }) {
  const [hasError, setHasError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const videoUrl = getVideoUrl(content)

  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] bg-gray-900 text-white rounded-lg p-8">
        <svg className="w-20 h-20 text-red-400 mb-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <h3 className="text-xl font-bold mb-2">Cannot Play Video</h3>
        <p className="text-sm text-gray-300 mb-4 text-center max-w-md">{errorMessage}</p>
        <div className="bg-gray-800 p-3 rounded text-xs font-mono text-left w-full max-w-md">
          <p className="text-gray-400">Proxy URL: {videoUrl}</p>
          <p className="text-gray-400 mt-1">Original URL: {content.anthias_url}</p>
          <p className="text-gray-400 mt-1">Type: {content.mime_type || 'unknown'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative bg-black rounded-lg overflow-hidden">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-white text-center">
            <svg className="w-12 h-12 mx-auto mb-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm">Loading video...</p>
          </div>
        </div>
      )}
      <video
        controls
        autoPlay={false}
        preload="auto"
        className="w-full h-auto max-h-[60vh]"
        style={{ minHeight: '300px' }}
        onLoadStart={() => {
          console.log('Video loading started (proxy):', videoUrl)
          console.log('Original Anthias URL:', content.anthias_url)
          setIsLoading(true)
        }}
        onLoadedMetadata={(e) => {
          console.log('Video metadata loaded:', {
            duration: e.target.duration,
            videoWidth: e.target.videoWidth,
            videoHeight: e.target.videoHeight
          })
          setIsLoading(false)
        }}
        onCanPlay={() => {
          console.log('Video can play')
          setIsLoading(false)
        }}
        onError={(e) => {
          console.error('Video error:', e.target.error)
          console.error('Error code:', e.target.error?.code)
          console.error('Error message:', e.target.error?.message)
          console.error('Proxy Video URL:', videoUrl)
          console.error('Original Anthias URL:', content.anthias_url)

          let errorMsg = 'Unable to load video. '
          if (e.target.error?.code === 4) {
            errorMsg += 'Video format not supported or file not found.'
          } else if (e.target.error?.code === 2) {
            errorMsg += 'Network error while loading video.'
          } else if (e.target.error?.code === 3) {
            errorMsg += 'Video decoding failed.'
          } else {
            errorMsg += 'Unknown error occurred.'
          }

          setErrorMessage(errorMsg)
          setHasError(true)
          setIsLoading(false)
        }}
      >
        <source src={videoUrl} type={content.mime_type || 'video/mp4'} />
        Your browser does not support the video tag.
      </video>
    </div>
  )
}

function PreviewModal({ content, onClose }) {
  const imageUrl = getImageUrl(content)
  console.log('PreviewModal - Image URL:', imageUrl)
  console.log('PreviewModal - Content:', content)

  // Fetch assignments for this content
  const { data: assignmentsData } = useQuery({
    queryKey: ['content-assignments', content.id],
    queryFn: () => contentAPI.getAssignments(content.id).then(res => res.data),
  })

  // Fetch devices and tags to show names
  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">{content.title}</h2>
            <p className="text-sm text-gray-600 mt-1">
              {content.content_type.toUpperCase()} • {content.duration}s • {content.is_active ? 'Active' : 'Inactive'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content Preview */}
        <div className="p-6">
          {/* Media Display */}
          <div className="mb-6">
            {content.content_type === 'image' ? (
              <div className="bg-gray-100 rounded-lg overflow-hidden min-h-[300px] flex items-center justify-center">
                <img
                  src={imageUrl}
                  alt={content.title}
                  className="w-full h-auto max-h-[60vh] object-contain"
                  style={{ minHeight: '200px' }}
                  onLoad={() => console.log('Image loaded successfully')}
                  onError={(e) => {
                    console.error('Image load error:', e)
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect fill="%23ddd" width="400" height="300"/><text fill="%23999" x="50%" y="50%" text-anchor="middle" dy=".3em">Image not available</text></svg>'
                  }}
                />
              </div>
            ) : (
              <ModalVideoPlayer content={content} />
            )}
          </div>

          {/* Details */}
          <div className="space-y-4">
            {content.description && (
              <div>
                <h3 className="font-semibold text-gray-700 mb-1">Description</h3>
                <p className="text-gray-600">{content.description}</p>
              </div>
            )}

            {/* Media Metadata Section */}
            {(content.resolution || content.codec || content.fps || content.bitrate) && (
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-700 mb-3">Media Information</h3>
                <div className="grid grid-cols-2 gap-3">
                  {content.resolution && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Resolution</div>
                      <div className="font-semibold text-gray-800">{content.resolution}</div>
                    </div>
                  )}
                  {content.codec && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Codec</div>
                      <div className="font-semibold text-gray-800 uppercase">{content.codec}</div>
                    </div>
                  )}
                  {content.fps && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Frame Rate</div>
                      <div className="font-semibold text-gray-800">{content.fps} fps</div>
                    </div>
                  )}
                  {content.bitrate && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Bitrate</div>
                      <div className="font-semibold text-gray-800">{content.bitrate} kbps</div>
                    </div>
                  )}
                  {content.video_duration && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Video Duration</div>
                      <div className="font-semibold text-gray-800">{content.video_duration.toFixed(2)}s</div>
                    </div>
                  )}
                  {content.audio_codec && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Audio Codec</div>
                      <div className="font-semibold text-gray-800 uppercase">{content.audio_codec}</div>
                    </div>
                  )}
                  {content.audio_bitrate && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Audio Bitrate</div>
                      <div className="font-semibold text-gray-800">{content.audio_bitrate} kbps</div>
                    </div>
                  )}
                  {content.audio_sample_rate && (
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-xs text-gray-500 mb-1">Sample Rate</div>
                      <div className="font-semibold text-gray-800">{content.audio_sample_rate} Hz</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* File Information Section */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold text-gray-700 mb-1">File Size</h3>
                <p className="text-gray-600">
                  {content.file_size ? `${(content.file_size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 mb-1">MIME Type</h3>
                <p className="text-gray-600">{content.mime_type || 'N/A'}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 mb-1">Anthias Asset ID</h3>
                <p className="text-gray-600 text-sm font-mono">{content.anthias_asset_id}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-700 mb-1">Created</h3>
                <p className="text-gray-600 text-sm">
                  {new Date(content.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            {/* URL */}
            <div>
              <h3 className="font-semibold text-gray-700 mb-1">Image URL</h3>
              <a
                href={getImageUrl(content)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm break-all"
              >
                {getImageUrl(content)}
              </a>
            </div>

            {/* Assignments Section */}
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Assigned To</h3>
              {assignmentsData && assignmentsData.length > 0 ? (
                <div className="space-y-2">
                  {assignmentsData.map((assignment) => {
                    // Find device or tag name
                    let displayName = 'Unknown'
                    let displayType = ''
                    let displayColor = 'bg-gray-100 text-gray-700'

                    if (assignment.device_id) {
                      const device = devicesData?.devices?.find(d => d.id === assignment.device_id)
                      displayName = device ? device.device_name : `Device #${assignment.device_id}`
                      displayType = 'Device'
                      displayColor = 'bg-blue-100 text-blue-700'
                    } else if (assignment.tag_id) {
                      const tag = tagsData?.items?.find(t => t.id === assignment.tag_id)
                      displayName = tag ? tag.tag_name : `Tag #${assignment.tag_id}`
                      displayType = 'Tag'
                      displayColor = 'bg-green-100 text-green-700'
                    }

                    return (
                      <div
                        key={assignment.id}
                        className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${displayColor}`}>
                            {displayType}
                          </span>
                          <span className="font-medium text-gray-800">{displayName}</span>
                          {assignment.priority > 0 && (
                            <span className="text-xs text-gray-500">
                              Priority: {assignment.priority}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(assignment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-500 text-sm">
                  No assignments yet. Click "Assign" button to assign this content to devices or tags.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4">
          <button
            onClick={onClose}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-lg font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function BulkEditForm({ selectedIds, contentData, onClose, onComplete }) {
  const queryClient = useQueryClient()
  const [updating, setUpdating] = useState(false)
  const [updateProgress, setUpdateProgress] = useState([])

  // Get selected content items
  const selectedContent = contentData?.items?.filter(c => selectedIds.has(c.id)) || []

  // State for individual edits - Map of contentId -> {title, description, duration}
  const [edits, setEdits] = useState(() => {
    const initialEdits = {}
    selectedContent.forEach(content => {
      initialEdits[content.id] = {
        title: content.title,
        description: content.description || '',
        duration: content.duration
      }
    })
    return initialEdits
  })

  const updateEdit = (contentId, field, value) => {
    setEdits(prev => ({
      ...prev,
      [contentId]: {
        ...prev[contentId],
        [field]: value
      }
    }))
  }

  const handleBulkUpdate = async (e) => {
    e.preventDefault()

    setUpdating(true)
    setUpdateProgress(selectedContent.map(() => ({ status: 'pending', error: null })))

    let successCount = 0
    let failCount = 0

    // Update all items with their individual edits
    const updatePromises = selectedContent.map(async (content, index) => {
      try {
        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'updating', error: null }
          return newProgress
        })

        const editedData = edits[content.id]
        const updateData = {}

        // Only include fields that have changed
        if (editedData.title !== content.title) {
          updateData.title = editedData.title
        }
        if (editedData.description !== (content.description || '')) {
          updateData.description = editedData.description
        }
        if (editedData.duration !== content.duration) {
          updateData.duration = editedData.duration
        }

        // Only call API if there are changes
        if (Object.keys(updateData).length > 0) {
          await contentAPI.update(content.id, updateData)
        }

        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'success', error: null }
          return newProgress
        })
        successCount++
      } catch (error) {
        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = {
            status: 'failed',
            error: error.response?.data?.detail || 'Update failed'
          }
          return newProgress
        })
        failCount++
      }
    })

    await Promise.all(updatePromises)
    queryClient.invalidateQueries(['content'])
    setUpdating(false)

    alert(`Bulk update complete!\n✅ Success: ${successCount}\n❌ Failed: ${failCount}`)

    if (successCount > 0) {
      onComplete()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Bulk Edit Content</h2>
            <p className="text-sm text-gray-600 mt-1">{selectedContent.length} items selected</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
            disabled={updating}
          >
            ×
          </button>
        </div>

        {/* Form - List of individual item editors */}
        <form onSubmit={handleBulkUpdate} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Individual Item Editors */}
            <div className="space-y-4">
              <h3 className="font-bold text-gray-700 text-lg flex items-center gap-2">
                <span>✏️</span>
                Edit Individual Items
              </h3>
              {selectedContent.map((content, index) => (
              <div
                key={content.id}
                className="bg-gray-50 p-4 rounded-lg border-2 border-gray-200"
              >
                {/* Side-by-side layout: Preview LEFT, Form RIGHT */}
                <div className="grid grid-cols-12 gap-4 items-start">
                  {/* LEFT: Preview Content (30-35% width) */}
                  <div className="col-span-4 flex flex-col">
                    <div className="relative bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg overflow-hidden max-h-48 flex items-center justify-center">
                      {content.content_type === 'video' ? (
                        <video
                          src={getImageUrl(content)}
                          className="w-full h-full object-contain"
                          preload="metadata"
                          controls
                          onLoadedMetadata={(e) => {
                            e.target.currentTime = 0.1 // Load first frame as thumbnail
                          }}
                        />
                      ) : (
                        <img
                          src={getImageUrl(content)}
                          alt={content.title}
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            e.target.style.display = 'none'
                            const parent = e.target.parentElement
                            if (!parent.querySelector('.video-icon-fallback')) {
                              const fallback = document.createElement('div')
                              fallback.className = 'video-icon-fallback flex flex-col items-center justify-center'
                              fallback.innerHTML = `
                                <span class="text-5xl mb-2">📷</span>
                                <span class="text-xs text-gray-600">Image</span>
                              `
                              parent.appendChild(fallback)
                            }
                          }}
                        />
                      )}

                      {/* Status badge */}
                      <div className="absolute top-2 right-2 text-3xl bg-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg">
                        {updateProgress[index]?.status === 'pending' && '⏳'}
                        {updateProgress[index]?.status === 'updating' && '🔄'}
                        {updateProgress[index]?.status === 'success' && '✅'}
                        {updateProgress[index]?.status === 'failed' && '❌'}
                      </div>
                    </div>

                    {/* Original info below preview */}
                    <div className="mt-2 px-2 flex-shrink-0">
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Original</p>
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-xs text-gray-500">{content.content_type.toUpperCase()} • {content.duration}s</p>
                    </div>
                  </div>

                  {/* RIGHT: Form Fields (65-70% width) */}
                  <div className="col-span-8 flex flex-col space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Title
                      </label>
                      <input
                        type="text"
                        value={edits[content.id]?.title || ''}
                        onChange={(e) => updateEdit(content.id, 'title', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={updating}
                        placeholder="Content title"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <textarea
                        value={edits[content.id]?.description || ''}
                        onChange={(e) => updateEdit(content.id, 'description', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={updating}
                        rows={3}
                        placeholder="Content description (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Duration (seconds)
                      </label>
                      <input
                        type="number"
                        value={edits[content.id]?.duration || 10}
                        onChange={(e) => updateEdit(content.id, 'duration', parseInt(e.target.value) || 10)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={updating}
                        min={1}
                      />
                    </div>
                  </div>
                </div>

                {/* Show error if failed - Full width below */}
                {updateProgress[index]?.status === 'failed' && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    Error: {updateProgress[index]?.error}
                  </div>
                )}
              </div>
              ))}
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            type="submit"
            onClick={handleBulkUpdate}
            disabled={updating}
            className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {updating ? 'Updating...' : `Update ${selectedContent.length} Items`}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={updating}
            className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {updating ? 'Please wait...' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}

function BulkTagForm({ selectedIds, contentData, onClose, onComplete }) {
  const queryClient = useQueryClient()
  const [updating, setUpdating] = useState(false)

  // Get selected content items
  const selectedContent = contentData?.items?.filter(c => selectedIds.has(c.id)) || []

  // Fetch all tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch assignments for all selected content items
  const assignmentQueries = useQuery({
    queryKey: ['bulk-tag-assignments', [...selectedIds]],
    queryFn: async () => {
      const assignmentsMap = {}
      for (const contentId of selectedIds) {
        const res = await contentAPI.getAssignments(contentId)
        assignmentsMap[contentId] = res.data
      }
      return assignmentsMap
    },
    enabled: selectedIds.size > 0
  })

  // State: Map of contentId -> Set of selected tag IDs
  const [tagSelections, setTagSelections] = useState(() => {
    const initial = {}
    selectedContent.forEach(content => {
      initial[content.id] = new Set()
    })
    return initial
  })

  // Pre-populate tag selections when assignments load
  const [initialized, setInitialized] = useState(false)
  if (assignmentQueries.data && !assignmentQueries.isLoading && !initialized) {
    const newSelections = {}
    selectedContent.forEach(content => {
      const assignments = assignmentQueries.data[content.id] || []
      const tagIds = new Set()
      assignments.forEach(assignment => {
        if (assignment.tag_id) {
          tagIds.add(assignment.tag_id)
        }
      })
      newSelections[content.id] = tagIds
    })
    setTagSelections(newSelections)
    setInitialized(true)
  }

  const toggleTag = (contentId, tagId) => {
    setTagSelections(prev => {
      const newSelections = { ...prev }
      const currentSet = new Set(prev[contentId] || [])

      if (currentSet.has(tagId)) {
        currentSet.delete(tagId)
      } else {
        currentSet.add(tagId)
      }

      newSelections[contentId] = currentSet
      return newSelections
    })
  }

  const handleUpdateAll = async () => {
    setUpdating(true)

    try {
      // For each content item
      for (const content of selectedContent) {
        const currentAssignments = assignmentQueries.data[content.id] || []
        const currentTagIds = new Set(
          currentAssignments
            .filter(a => a.tag_id)
            .map(a => a.tag_id)
        )
        const selectedTagIds = tagSelections[content.id] || new Set()

        // Tags to add
        const tagsToAdd = [...selectedTagIds].filter(id => !currentTagIds.has(id))
        // Tags to remove
        const tagsToRemove = [...currentTagIds].filter(id => !selectedTagIds.has(id))

        // Add new tags
        for (const tagId of tagsToAdd) {
          try {
            await contentAPI.assign(content.id, {
              tag_id: tagId,
              priority: 0
            })
          } catch (err) {
            // Ignore if already assigned
            if (!err.response?.data?.detail?.includes('already exists')) {
              throw err
            }
          }
        }

        // Remove unselected tags
        for (const tagId of tagsToRemove) {
          try {
            await contentAPI.unassign(content.id, {
              tag_id: tagId
            })
          } catch (err) {
            console.error('Unassign error:', err)
          }
        }
      }

      // Refresh queries
      queryClient.invalidateQueries(['bulk-tag-assignments'])
      queryClient.invalidateQueries(['content'])
      queryClient.invalidateQueries(['content-assignments'])

      alert('Tags updated successfully!')
      onComplete()
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update tags')
    }

    setUpdating(false)
  }

  const allTags = tagsData?.items || []

  if (assignmentQueries.isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6">
          <p className="text-gray-600">Loading assignments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Bulk Tag Assignment</h2>
            <p className="text-sm text-gray-600 mt-1">{selectedContent.length} content items selected</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            disabled={updating}
          >
            ✕
          </button>
        </div>

        {/* Content list with tag checkboxes */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {selectedContent.map((content) => {
              const selectedTags = tagSelections[content.id] || new Set()

              return (
                <div
                  key={content.id}
                  className="bg-gray-50 rounded-lg border-2 border-gray-200 p-4"
                >
                  {/* Title di atas */}
                  <div className="mb-3">
                    <p className="font-bold text-gray-800 text-lg">{content.title}</p>
                    <p className="text-sm text-gray-600">
                      {content.content_type.toUpperCase()} • {content.duration}s
                    </p>
                  </div>

                  {/* Horizontal layout: Thumbnail (left) + Tag pills (right) */}
                  <div className="grid grid-cols-12 gap-4">
                    {/* Left: Thumbnail saja (30-35%) */}
                    <div className="col-span-4">
                      {/* Thumbnail with aspect-video */}
                      <div className="relative bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
                        {content.content_type === 'video' ? (
                          <video
                            src={getImageUrl(content)}
                            className="w-full h-full object-cover"
                            preload="metadata"
                            controls
                            onLoadedMetadata={(e) => {
                              e.target.currentTime = 0.1 // Load first frame as thumbnail
                            }}
                          />
                        ) : (
                          <img
                            src={getImageUrl(content)}
                            alt={content.title}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none'
                              const parent = e.target.parentElement
                              if (!parent.querySelector('.video-icon-fallback')) {
                                const fallback = document.createElement('div')
                                fallback.className = 'video-icon-fallback flex flex-col items-center justify-center'
                                fallback.innerHTML = `
                                  <span class="text-5xl mb-2">📷</span>
                                  <span class="text-xs text-gray-600">Image</span>
                                `
                                parent.appendChild(fallback)
                              }
                            }}
                          />
                        )}
                      </div>
                    </div>

                    {/* Right: Tag pills (65-70%) */}
                    <div className="col-span-8">
                      <div className="flex flex-wrap gap-2">
                        {allTags.map((tag) => {
                          const isSelected = selectedTags.has(tag.id)
                          return (
                            <div
                              key={tag.id}
                              onClick={() => !updating && toggleTag(content.id, tag.id)}
                              className={`inline-flex flex-col px-3 py-2 rounded-xl cursor-pointer transition-all ${
                                isSelected
                                  ? 'bg-green-500 text-white shadow-md'
                                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                              }`}
                              style={{
                                userSelect: 'none',
                                fontSize: '11px'
                              }}
                            >
                              <div className="flex items-center gap-1">
                                <span>🏷️</span>
                                <span className="font-medium">{tag.tag_name}</span>
                              </div>
                              {tag.description && (
                                <span className="text-[10px] opacity-90 mt-0.5">
                                  {tag.description}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      {selectedTags.size > 0 && (
                        <div className="mt-3 text-xs text-gray-600">
                          ✓ {selectedTags.size} tag(s) selected
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            type="button"
            onClick={handleUpdateAll}
            disabled={updating}
            className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {updating ? 'Updating...' : 'Update All'}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={updating}
            className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
