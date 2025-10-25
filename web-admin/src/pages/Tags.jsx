import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, devicesAPI } from '../services/api'
import { Tag, Plus, Trash2, Edit2, Users, Eye, Search, BarChart3 } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button, FormInput } from '../components/shared'

// Modal Components
import TagFormModal from '../components/tags/modals/TagFormModal'
import AssignTagModal from '../components/tags/modals/AssignTagModal'
import TagDevicesModal from '../components/tags/modals/TagDevicesModal'
import TagStatsModal from '../components/tags/modals/TagStatsModal'

export default function Tags() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [showDevicesModal, setShowDevicesModal] = useState(false)
  const [showStatsModal, setShowStatsModal] = useState(false)
  const [selectedTag, setSelectedTag] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

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
      showToast.success('Tag created successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Create failed')
    }
  })

  // Update tag mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => tagsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      setShowEditForm(false)
      setSelectedTag(null)
      showToast.success('Tag updated successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Update failed')
    }
  })

  // Delete tag mutation
  const deleteMutation = useMutation({
    mutationFn: tagsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['tags'])
      showToast.success('Tag deleted successfully!')
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

  const handleViewDevices = (tag) => {
    setSelectedTag(tag)
    setShowDevicesModal(true)
  }

  const handleViewStats = (tag) => {
    setSelectedTag(tag)
    setShowStatsModal(true)
  }

  // Filter tags based on search query
  const filteredTags = useMemo(() => {
    if (!tagsData?.items) return []

    if (!searchQuery.trim()) return tagsData.items

    const query = searchQuery.toLowerCase()
    return tagsData.items.filter(tag =>
      tag.tag_name.toLowerCase().includes(query) ||
      tag.description?.toLowerCase().includes(query)
    )
  }, [tagsData?.items, searchQuery])

  return (
    <div>
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="flex items-center justify-between pt-4 mb-4">
          <h1 className="text-3xl font-bold text-gray-800">Tags</h1>
          <Button
            variant="primary"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setShowCreateForm(true)}
          >
            Create Tag
          </Button>
        </div>

        {/* Search Bar */}
        <div className="max-w-md">
          <FormInput
            type="text"
            placeholder="Search tags by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4 text-gray-400" />}
          />
        </div>
      </div>

      {/* Tags Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTags.map((tag) => (
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
            <div className="space-y-2">
              <div className="flex gap-2">
                <Button
                  variant="info"
                  size="sm"
                  leftIcon={<BarChart3 className="w-4 h-4" />}
                  onClick={() => handleViewStats(tag)}
                  className="flex-1"
                >
                  Stats
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<Eye className="w-4 h-4" />}
                  onClick={() => handleViewDevices(tag)}
                  className="flex-1"
                >
                  Devices
                </Button>
                <Button
                  variant="success"
                  size="sm"
                  leftIcon={<Users className="w-4 h-4" />}
                  onClick={() => handleAssign(tag)}
                  className="flex-1"
                >
                  Assign
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="warning"
                  size="sm"
                  leftIcon={<Edit2 className="w-4 h-4" />}
                  onClick={() => handleEdit(tag)}
                  className="flex-1"
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  leftIcon={<Trash2 className="w-4 h-4" />}
                  onClick={() => {
                    if (confirm('Delete this tag?')) {
                      deleteMutation.mutate(tag.id)
                    }
                  }}
                  className="flex-1"
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty States */}
      {tagsData?.items?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <Tag className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No tags created yet</p>
        </div>
      )}

      {filteredTags.length === 0 && tagsData?.items?.length > 0 && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No tags found matching "{searchQuery}"</p>
          <button
            onClick={() => setSearchQuery('')}
            className="text-blue-600 hover:underline mt-2"
          >
            Clear search
          </button>
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

      {/* View Devices Modal */}
      {showDevicesModal && selectedTag && (
        <TagDevicesModal
          tag={selectedTag}
          onClose={() => {
            setShowDevicesModal(false)
            setSelectedTag(null)
          }}
          onOpenAssign={() => {
            setShowDevicesModal(false)
            setShowAssignForm(true)
          }}
        />
      )}

      {/* Stats Modal */}
      {showStatsModal && selectedTag && (
        <TagStatsModal
          tag={selectedTag}
          onClose={() => {
            setShowStatsModal(false)
            setSelectedTag(null)
          }}
        />
      )}
    </div>
  )
}
