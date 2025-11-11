import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI } from '../services/api'
import { ListVideo, Plus, Trash2, Edit2, Play, Users, Copy, Monitor, Search } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button, PageHeader, FormInput, LoadingSkeleton } from '../components/shared'
import PlaylistFormModal from '../components/playlists/modals/PlaylistFormModal'
import PlaylistContentModal from '../components/playlists/modals/PlaylistContentModal'
import PlaylistAssignmentModal from '../components/playlists/modals/PlaylistAssignmentModal'
import DuplicatePlaylistModal from '../components/playlists/modals/DuplicatePlaylistModal'
import PlaylistPreviewModal from '../components/playlists/modals/PlaylistPreviewModal'

/**
 * Playlists Page
 * Manage playlists for content scheduling and organization
 *
 * Features:
 * - List all playlists with content count
 * - Create new playlists
 * - Edit playlist details
 * - Delete playlists
 * - Assign content to playlists
 * - Preview playlist order
 */
export default function Playlists() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showContentModal, setShowContentModal] = useState(false)
  const [showAssignmentModal, setShowAssignmentModal] = useState(false)
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [selectedPlaylist, setSelectedPlaylist] = useState(null)
  const [activeFilter, setActiveFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('newest')

  // Fetch playlists
  const { data: playlistsData, isLoading } = useQuery({
    queryKey: ['playlists'],
    queryFn: () => playlistsAPI.list().then(res => res.data),
  })

  // Filter and sort playlists
  const filteredPlaylists = useMemo(() => {
    if (!playlistsData?.items) return []

    let filtered = playlistsData.items

    // Apply status filter
    if (activeFilter === 'active') {
      filtered = filtered.filter(p => p.is_active)
    } else if (activeFilter === 'inactive') {
      filtered = filtered.filter(p => !p.is_active)
    }
    // 'all' shows everything

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(playlist =>
        playlist.name?.toLowerCase().includes(query) ||
        playlist.description?.toLowerCase().includes(query)
      )
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at) - new Date(a.created_at)
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at)
        case 'name_asc':
          return (a.name || '').localeCompare(b.name || '')
        case 'name_desc':
          return (b.name || '').localeCompare(a.name || '')
        default:
          return 0
      }
    })

    return sorted
  }, [playlistsData?.items, activeFilter, searchQuery, sortBy])

  // Create playlist mutation
  const createMutation = useMutation({
    mutationFn: playlistsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists'])
      setShowCreateModal(false)
      showToast.success('Playlist created successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to create playlist')
    }
  })

  // Update playlist mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => playlistsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists'])
      setShowEditModal(false)
      setSelectedPlaylist(null)
      showToast.success('Playlist updated successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to update playlist')
    }
  })

  // Delete playlist mutation
  const deleteMutation = useMutation({
    mutationFn: playlistsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Playlist deleted successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to delete playlist')
    }
  })

  const handleEdit = (playlist) => {
    setSelectedPlaylist(playlist)
    setShowEditModal(true)
  }

  const handleManageContent = (playlist) => {
    setSelectedPlaylist(playlist)
    setShowContentModal(true)
  }

  const handleAssignDevices = (playlist) => {
    setSelectedPlaylist(playlist)
    setShowAssignmentModal(true)
  }

  const handleDuplicate = (playlist) => {
    setSelectedPlaylist(playlist)
    setShowDuplicateModal(true)
  }

  const handlePreview = (playlist) => {
    setSelectedPlaylist(playlist)
    setShowPreviewModal(true)
  }

  const handleDelete = (id, name) => {
    if (confirm(`Delete playlist "${name}"?\n\nThis will NOT delete the content, only the playlist.`)) {
      deleteMutation.mutate(id)
    }
  }

  // Calculate stats
  const stats = useMemo(() => {
    const total = playlistsData?.items?.length || 0
    const active = playlistsData?.items?.filter(p => p.is_active).length || 0
    const inactive = total - active
    const totalContent = playlistsData?.items?.reduce((sum, p) => sum + (p.content_count || 0), 0) || 0
    const totalDuration = playlistsData?.items?.reduce((sum, p) => sum + (p.total_duration || 0), 0) || 0
    const durationMinutes = Math.floor(totalDuration / 60)

    return [
      { label: 'Total Playlists', value: total, color: 'blue', filterKey: 'all' },
      { label: 'Active', value: active, color: 'green', filterKey: 'active' },
      { label: 'Inactive', value: inactive, color: 'gray', filterKey: 'inactive' },
      { label: 'Total Items', value: totalContent, color: 'purple', filterKey: null },
      { label: 'Total Duration', value: `${durationMinutes}m`, color: 'blue', filterKey: null }
    ]
  }, [playlistsData?.items])

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900">
      <PageHeader
        title="Playlists"
        description="Organize content into playlists for scheduled playback"
        actions={
          <Button
            variant="primary"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setShowCreateModal(true)}
          >
            Create Playlist
          </Button>
        }
        searchBar={
          <div className="flex gap-3 max-w-xl">
            <div className="flex-1">
              <FormInput
                icon={Search}
                type="text"
                placeholder="Search playlists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          {/* Loading State */}
          {isLoading && (
            <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <LoadingSkeleton variant="grid-playlist" count={6} />
            </div>
          )}

          {/* Empty State */}
          {!isLoading && (!playlistsData?.items || playlistsData.items.length === 0) && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 text-center">
              <ListVideo className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">No Playlists Yet</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Create your first playlist to organize content for scheduled playback
              </p>
              <Button
                variant="primary"
                leftIcon={<Plus className="w-5 h-5" />}
                onClick={() => setShowCreateModal(true)}
              >
                Create First Playlist
              </Button>
            </div>
          )}

          {/* Playlists Grid */}
          {!isLoading && filteredPlaylists.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 animate-fade-in">
          {filteredPlaylists.map((playlist) => (
            <div
              key={playlist.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 hover:shadow-xl transition-shadow overflow-hidden"
            >
              {/* Playlist Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                      <ListVideo className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-800 dark:text-gray-100 text-lg">{playlist.name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {playlist.content_count || 0} items
                      </p>
                    </div>
                  </div>
                </div>

                {playlist.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {playlist.description}
                  </p>
                )}
              </div>

              {/* Playlist Stats */}
              <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">Duration</p>
                    <p className="font-semibold text-gray-800 dark:text-gray-100">
                      {playlist.total_duration ? `${Math.floor(playlist.total_duration / 60)}m` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">Status</p>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                      playlist.is_active
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {playlist.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="px-6 py-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    leftIcon={<Play className="w-4 h-4" />}
                    onClick={() => handleManageContent(playlist)}
                    className="flex-1"
                  >
                    Content
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    leftIcon={<Users className="w-4 h-4" />}
                    onClick={() => handleAssignDevices(playlist)}
                    className="flex-1"
                  >
                    Assign
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="info"
                    size="sm"
                    leftIcon={<Monitor className="w-4 h-4" />}
                    onClick={() => handlePreview(playlist)}
                    className="flex-1"
                  >
                    Preview
                  </Button>
                  <Button
                    variant="info"
                    size="sm"
                    leftIcon={<Copy className="w-4 h-4" />}
                    onClick={() => handleDuplicate(playlist)}
                    className="flex-1"
                  >
                    Duplicate
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    leftIcon={<Edit2 className="w-4 h-4" />}
                    onClick={() => handleEdit(playlist)}
                    className="flex-1"
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDelete(playlist.id, playlist.name)}
                    className="flex-1"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <PlaylistFormModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => createMutation.mutate(data)}
        />
      )}

      {showEditModal && selectedPlaylist && (
        <PlaylistFormModal
          playlist={selectedPlaylist}
          onClose={() => {
            setShowEditModal(false)
            setSelectedPlaylist(null)
          }}
          onSubmit={(data) => updateMutation.mutate({ id: selectedPlaylist.id, data })}
        />
      )}

      {showContentModal && selectedPlaylist && (
        <PlaylistContentModal
          playlist={selectedPlaylist}
          onClose={() => {
            setShowContentModal(false)
            setSelectedPlaylist(null)
          }}
        />
      )}

      {showAssignmentModal && selectedPlaylist && (
        <PlaylistAssignmentModal
          playlist={selectedPlaylist}
          onClose={() => {
            setShowAssignmentModal(false)
            setSelectedPlaylist(null)
          }}
        />
      )}

      {showDuplicateModal && selectedPlaylist && (
        <DuplicatePlaylistModal
          playlist={selectedPlaylist}
          onClose={() => {
            setShowDuplicateModal(false)
            setSelectedPlaylist(null)
          }}
        />
      )}

      {showPreviewModal && selectedPlaylist && (
        <PlaylistPreviewModal
          playlist={selectedPlaylist}
          onClose={() => {
            setShowPreviewModal(false)
            setSelectedPlaylist(null)
          }}
        />
      )}
    </div>
  )
}
