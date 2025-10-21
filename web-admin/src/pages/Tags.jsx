import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, devicesAPI } from '../services/api'
import { Tag, Plus, Trash2, Edit2, Users } from 'lucide-react'

export default function Tags() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [selectedTag, setSelectedTag] = useState(null)

  // Fetch tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Create tag mutation
  const createMutation = useMutation({
    mutationFn: tagsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      setShowCreateForm(false)
      alert('Tag created successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Create failed')
    }
  })

  // Update tag mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => tagsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      setShowEditForm(false)
      setSelectedTag(null)
      alert('Tag updated successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Update failed')
    }
  })

  // Delete tag mutation
  const deleteMutation = useMutation({
    mutationFn: tagsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      alert('Tag deleted successfully!')
    },
  })

  const handleEdit = (tag) => {
    setSelectedTag(tag)
    setShowEditForm(true)
  }

  const handleAssign = (tag) => {
    setSelectedTag(tag)
    setShowAssignForm(true)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Tags</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5 mr-2" />
          Create Tag
        </button>
      </div>

      {/* Tags Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tagsData?.items?.map((tag) => (
          <div key={tag.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
            {/* Tag Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <div
                  className="w-4 h-4 rounded-full mr-3"
                  style={{ backgroundColor: tag.color }}
                />
                <h3 className="font-bold text-gray-800">{tag.tag_name}</h3>
              </div>
              <Tag className="w-5 h-5 text-gray-400" />
            </div>

            {/* Description */}
            <p className="text-sm text-gray-600 mb-4 min-h-[40px]">
              {tag.description || 'No description'}
            </p>

            {/* Device Count */}
            <div className="flex items-center text-sm text-gray-600 mb-4">
              <Users className="w-4 h-4 mr-1" />
              <span>{tag.device_count} device{tag.device_count !== 1 ? 's' : ''}</span>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => handleAssign(tag)}
                className="flex-1 flex items-center justify-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
              >
                <Users className="w-4 h-4 mr-1" />
                Assign
              </button>
              <button
                onClick={() => handleEdit(tag)}
                className="px-3 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm('Delete this tag?')) {
                    deleteMutation.mutate(tag.id)
                  }
                }}
                className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {tagsData?.items?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <Tag className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No tags created yet</p>
        </div>
      )}

      {/* Create Form Modal */}
      {showCreateForm && <TagForm onClose={() => setShowCreateForm(false)} onSubmit={createMutation.mutate} />}

      {/* Edit Form Modal */}
      {showEditForm && selectedTag && (
        <TagForm
          tag={selectedTag}
          onClose={() => {
            setShowEditForm(false)
            setSelectedTag(null)
          }}
          onSubmit={(data) => updateMutation.mutate({ id: selectedTag.id, data })}
        />
      )}

      {/* Assign Form Modal */}
      {showAssignForm && selectedTag && (
        <AssignTagForm
          tag={selectedTag}
          onClose={() => {
            setShowAssignForm(false)
            setSelectedTag(null)
          }}
        />
      )}
    </div>
  )
}

function TagForm({ tag, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    tag_name: tag?.tag_name || '',
    description: tag?.description || '',
    color: tag?.color || '#3B82F6',
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const colorPresets = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#14B8A6', // Teal
    '#F97316', // Orange
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">{tag ? 'Edit Tag' : 'Create Tag'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Tag Name</label>
            <input
              type="text"
              value={formData.tag_name}
              onChange={(e) => setFormData({...formData, tag_name: e.target.value})}
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
            <label className="block text-sm font-medium mb-1">Color</label>
            <div className="flex items-center gap-2 mb-2">
              {colorPresets.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setFormData({...formData, color})}
                  className={`w-8 h-8 rounded-full border-2 ${
                    formData.color === color ? 'border-gray-800' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <input
              type="color"
              value={formData.color}
              onChange={(e) => setFormData({...formData, color: e.target.value})}
              className="w-full h-10 border rounded-lg cursor-pointer"
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 bg-blue-600 text-white py-2 rounded-lg">
              {tag ? 'Update' : 'Create'}
            </button>
            <button type="button" onClick={onClose} className="flex-1 bg-gray-200 py-2 rounded-lg">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function AssignTagForm({ tag, onClose }) {
  const queryClient = useQueryClient()
  const [selectedDevices, setSelectedDevices] = useState([])

  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then(res => res.data),
  })

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
      alert('Tag assigned successfully!')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Assignment failed')
    }
  })

  // Unassign tag mutation
  const unassignMutation = useMutation({
    mutationFn: tagsAPI.unassign,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      queryClient.invalidateQueries(['tag-devices', tag.id])
      alert('Tag removed successfully!')
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <div
              className="w-4 h-4 rounded-full mr-3"
              style={{ backgroundColor: tag.color }}
            />
            <h2 className="text-xl font-bold">Assign Devices: {tag.tag_name}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <div className="space-y-2">
          {devicesData?.items?.map((device) => {
            const isAssigned = assignedDeviceIds.includes(device.id)
            return (
              <div
                key={device.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-800">{device.device_name}</p>
                  <p className="text-sm text-gray-600">
                    {device.device_type.toUpperCase()} • {device.ip_address || 'N/A'}
                  </p>
                </div>
                <button
                  onClick={() => isAssigned ? handleUnassign(device.id) : handleAssign(device.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
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

        {devicesData?.items?.length === 0 && (
          <p className="text-center py-8 text-gray-500">No devices available</p>
        )}
      </div>
    </div>
  )
}
