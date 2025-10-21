import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI, devicesAPI } from '../services/api'
import { Upload, FileImage, Trash2, Link as LinkIcon } from 'lucide-react'

export default function Content() {
  const queryClient = useQueryClient()
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
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
    onSuccess: () => {
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

  const handleAssign = (content) => {
    setSelectedContent(content)
    setShowAssignForm(true)
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
          <div key={content.id} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            {/* Preview */}
            <div className="aspect-video bg-gray-100 flex items-center justify-center">
              {content.content_type === 'image' ? (
                <img
                  src={content.anthias_url}
                  alt={content.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.parentElement.innerHTML = '<div class="text-gray-400 text-6xl">📷</div>'
                  }}
                />
              ) : (
                <div className="text-gray-400 text-6xl">🎥</div>
              )}
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
                  onClick={() => handleAssign(content)}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  <LinkIcon className="w-4 h-4 mr-1" />
                  Assign
                </button>
                <button
                  onClick={() => {
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
  const [assignData, setAssignData] = useState({
    device_id: null,
    tag_id: null,
    priority: 0,
  })

  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
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
          <div>
            <label className="block text-sm font-medium mb-1">Assign to Device</label>
            <select
              value={assignData.device_id || ''}
              onChange={(e) => setAssignData({...assignData, device_id: parseInt(e.target.value) || null, tag_id: null})}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Select Device...</option>
              {devicesData?.items?.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.device_name} ({device.device_type})
                </option>
              ))}
            </select>
          </div>
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
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-green-600 text-white py-2 rounded-lg">Assign</button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}
