import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI, tagsAPI } from '../services/api'
import { Upload, FileImage, Trash2, Link as LinkIcon } from 'lucide-react'

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
  const [selectedContent, setSelectedContent] = useState(null)

  // Fetch content
  const { data: contentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
  })

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

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Content</h1>
        <button
          onClick={() => setShowUploadForm(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Upload className="w-5 h-5 mr-2" />
          Upload Content
        </button>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {contentData?.items?.map((content) => (
          <div
            key={content.id}
            onClick={() => handlePreview(content)}
            className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
          >
            {/* Preview Thumbnail */}
            <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
              {content.content_type === 'image' ? (
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
              ) : (
                <div className="flex flex-col items-center justify-center">
                  <div className="text-6xl mb-2">🎥</div>
                  <span className="text-sm text-gray-500">Video</span>
                </div>
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
            <div className="p-4">
              <h3 className="font-bold text-gray-800 mb-1">{content.title}</h3>
              <p className="text-sm text-gray-600 mb-2">{content.description || 'No description'}</p>

              <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
                <span>{content.content_type.toUpperCase()}</span>
                <span>{content.duration}s</span>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={(e) => handleAssign(e, content)}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  <LinkIcon className="w-4 h-4 mr-1" />
                  Assign
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
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    duration: 10,
  })
  const [file, setFile] = useState(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!file) {
      alert('Please select a file')
      return
    }

    const data = new FormData()
    data.append('file', file)
    data.append('title', formData.title)
    data.append('description', formData.description || '')
    data.append('duration', formData.duration)
    data.append('is_active', 'true')

    onSubmit(data)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Upload Content</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">File</label>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Duration (seconds)</label>
            <input
              type="number"
              value={formData.duration}
              onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border rounded-lg"
              min={1}
              required
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg">Upload</button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

function AssignForm({ content, onClose, onSubmit }) {
  const [assignType, setAssignType] = useState('device') // 'device' or 'tag'
  const [assignData, setAssignData] = useState({
    device_id: null,
    tag_id: null,
    priority: 0,
  })

  const { data: devicesData } = useQuery({
    queryKey: ['devices', 'active'],
    queryFn: () => devicesAPI.list({ status: 'active' }).then(res => res.data),
  })

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validate that either device_id or tag_id is set
    if (!assignData.device_id && !assignData.tag_id) {
      alert('Please select a device or tag')
      return
    }

    onSubmit({
      id: content.id,
      data: assignData,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Assign: {content.title}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Assignment Type Toggle */}
          <div>
            <label className="block text-sm font-medium mb-2">Assign to</label>
            <div className="flex gap-2 mb-3">
              <button
                type="button"
                onClick={() => {
                  setAssignType('device')
                  setAssignData({...assignData, device_id: null, tag_id: null})
                }}
                className={`flex-1 px-4 py-2 rounded-lg font-medium ${
                  assignType === 'device'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Device
              </button>
              <button
                type="button"
                onClick={() => {
                  setAssignType('tag')
                  setAssignData({...assignData, device_id: null, tag_id: null})
                }}
                className={`flex-1 px-4 py-2 rounded-lg font-medium ${
                  assignType === 'tag'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Tag
              </button>
            </div>
          </div>

          {/* Device Selector */}
          {assignType === 'device' && (
            <div>
              <label className="block text-sm font-medium mb-1">Select Device</label>
              <select
                value={assignData.device_id || ''}
                onChange={(e) => setAssignData({...assignData, device_id: parseInt(e.target.value) || null, tag_id: null})}
                className="w-full px-3 py-2 border rounded-lg"
                required={assignType === 'device'}
              >
                <option value="">Select Device...</option>
                {devicesData?.devices?.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.device_name} ({device.device_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Tag Selector */}
          {assignType === 'tag' && (
            <div>
              <label className="block text-sm font-medium mb-1">Select Tag</label>
              <select
                value={assignData.tag_id || ''}
                onChange={(e) => setAssignData({...assignData, tag_id: parseInt(e.target.value) || null, device_id: null})}
                className="w-full px-3 py-2 border rounded-lg"
                required={assignType === 'tag'}
              >
                <option value="">Select Tag...</option>
                {tagsData?.items?.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.tag_name} ({tag.device_count} devices)
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Content will be assigned to all devices with this tag
              </p>
            </div>
          )}

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <input
              type="number"
              value={assignData.priority}
              onChange={(e) => setAssignData({...assignData, priority: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border rounded-lg"
              min={0}
            />
            <p className="text-xs text-gray-500 mt-1">Higher priority = displayed first</p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700">
              Assign
            </button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300">
              Cancel
            </button>
          </div>
        </form>
      </div>
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
          <div className="bg-gray-100 rounded-lg overflow-hidden mb-6 min-h-[300px] flex items-center justify-center">
            {content.content_type === 'image' ? (
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
            ) : (
              <div className="aspect-video flex items-center justify-center bg-gray-200">
                <div className="text-center">
                  <div className="text-8xl mb-4">🎥</div>
                  <p className="text-gray-600">Video Preview</p>
                  <p className="text-sm text-gray-500 mt-2">Duration: {content.duration}s</p>
                </div>
              </div>
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
