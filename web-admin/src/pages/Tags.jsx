import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, devicesAPI } from '../services/api'
import { Tag, Plus, Trash2, Edit2, Users, Search, BarChart3, Film } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button, FormInput, PageHeader } from '../components/shared'

// Modal Components
import TagFormModal from '../components/tags/modals/TagFormModal'
import TagDeviceManagementModal from '../components/tags/modals/TagDeviceManagementModal'
import TagStatsModal from '../components/tags/modals/TagStatsModal'
import TagContentModal from '../components/tags/modals/TagContentModal'

export default function Tags() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [showManageDevices, setShowManageDevices] = useState(false)
  const [showStatsModal, setShowStatsModal] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
  const [selectedTag, setSelectedTag] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('newest')
  const [activeFilter, setActiveFilter] = useState('all')

  // Fetch tags with sorting
  const { data: tagsData } = useQuery({
    queryKey: ['tags', sortBy],
    queryFn: () => tagsAPI.list({ sort_by: sortBy }).then(res => res.data),
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

  const handleManageDevices = (tag) => {
    setSelectedTag(tag)
    setShowManageDevices(true)
  }

  const handleViewStats = (tag) => {
    setSelectedTag(tag)
    setShowStatsModal(true)
  }

  const handleManageContent = (tag) => {
    setSelectedTag(tag)
    setShowContentModal(true)
  }

  // Filter tags based on search query AND active filter
  const filteredTags = useMemo(() => {
    if (!tagsData?.items) return []

    let filtered = tagsData.items

    // Apply stat filter
    if (activeFilter === 'with_devices') {
      filtered = filtered.filter(tag => tag.device_count > 0)
    } else if (activeFilter === 'without_devices') {
      filtered = filtered.filter(tag => tag.device_count === 0)
    }
    // 'all' shows everything

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(tag =>
        tag.tag_name.toLowerCase().includes(query) ||
        tag.description?.toLowerCase().includes(query)
      )
    }

    return filtered
  }, [tagsData?.items, searchQuery, activeFilter])

  // Calculate stats with filterKey
  const stats = useMemo(() => {
    if (!tagsData?.items) return []

    const total = tagsData.items.length
    const active = tagsData.items.filter(tag => tag.device_count > 0).length
    const inactive = total - active
    const totalDevices = tagsData.items.reduce((sum, tag) => sum + (tag.device_count || 0), 0)

    return [
      { label: 'Total Tags', value: total, color: 'blue', filterKey: 'all' },
      { label: 'With Devices', value: active, color: 'green', filterKey: 'with_devices' },
      { label: 'Without Devices', value: inactive, color: 'gray', filterKey: 'without_devices' },
      { label: 'Total Devices', value: totalDevices, color: 'purple', filterKey: null }
    ]
  }, [tagsData?.items])

  return (
    <div className="min-h-screen bg-slate-50">
      <PageHeader
        title="Tags"
        description="Organize and manage tags for device grouping and content assignment"
        actions={
          <Button
            variant="primary"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setShowCreateForm(true)}
          >
            Create Tag
          </Button>
        }
        searchBar={
          <div className="flex gap-3 max-w-xl">
            <div className="flex-1">
              <FormInput
                type="text"
                placeholder="Search tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="w-4 h-4 text-gray-400" />}
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="newest">Terbaru</option>
              <option value="oldest">Terlama</option>
              <option value="name_asc">Nama: A-Z</option>
              <option value="name_desc">Nama: Z-A</option>
            </select>
          </div>
        }
        stats={stats}
        activeFilter={activeFilter}
        onStatClick={setActiveFilter}
      />

      {/* Content with padding to account for fixed header */}
      {/* pt-40 (160px) mobile, pt-[172px] tablet (custom value between pt-42/168px and pt-44/176px), pt-44 (176px) desktop */}
      <div className="pt-40 sm:pt-[172px] lg:pt-44">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTags.map((tag) => (
          <div key={tag.id} className="bg-white rounded-xl shadow-lg border border-gray-300 p-6 hover:shadow-xl transition-shadow">
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
                  leftIcon={<Users className="w-4 h-4" />}
                  onClick={() => handleManageDevices(tag)}
                  className="flex-1"
                >
                  Devices ({tag.device_count})
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="success"
                  size="sm"
                  leftIcon={<Film className="w-4 h-4" />}
                  onClick={() => handleManageContent(tag)}
                  className="flex-1"
                >
                  Content
                </Button>
                <Button
                  variant="warning"
                  size="sm"
                  leftIcon={<Edit2 className="w-4 h-4" />}
                  onClick={() => handleEdit(tag)}
                  className="flex-1"
                >
                  Edit
                </Button>
              </div>
              <div className="flex gap-2">
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
        </div>
      </div>

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

      {/* Manage Devices Modal */}
      {showManageDevices && selectedTag && (
        <TagDeviceManagementModal
          tag={selectedTag}
          onClose={() => {
            setShowManageDevices(false)
            setSelectedTag(null)
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

      {/* Content Modal */}
      {showContentModal && selectedTag && (
        <TagContentModal
          tag={selectedTag}
          onClose={() => {
            setShowContentModal(false)
            setSelectedTag(null)
          }}
        />
      )}
    </div>
  )
}
