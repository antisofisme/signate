import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, devicesAPI } from '../services/api'
import { Tag, Plus, Trash2, Edit2, Users } from 'lucide-react'

// Modal Components
import TagFormModal from '../components/tags/modals/TagFormModal'
import AssignTagModal from '../components/tags/modals/AssignTagModal'

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
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="flex items-center justify-between pt-4">
          <h1 className="text-3xl font-bold text-gray-800">Tags</h1>
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Tag
          </button>
        </div>
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
      {showCreateForm && <TagFormModal onClose={() => setShowCreateForm(false)} onSubmit={createMutation.mutate} />}

      {/* Edit Form Modal */}
      {showEditForm && selectedTag && (
        <TagFormModal
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
        <AssignTagModal
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
