import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI } from '../services/api'
import { ListVideo, Plus, Trash2, Edit2, Play, Users, Copy, Monitor } from 'lucide-react'
import { showToast } from '../utils/toast'
import { Button } from '../components/shared'
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

  // Fetch playlists
  const { data: playlistsData, isLoading } = useQuery({
    queryKey: ['playlists'],
    queryFn: () => playlistsAPI.list().then(res => res.data),
  })

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

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
        <div className="flex items-center justify-between pt-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Playlists</h1>
            <p className="text-gray-600 text-sm mt-1">
              Organize content into playlists for scheduled playback
            </p>
          </div>
          <Button
            variant="primary"
            leftIcon={<Plus className="w-5 h-5" />}
            onClick={() => setShowCreateModal(true)}
          >
            Create Playlist
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!playlistsData?.items || playlistsData.items.length === 0) && (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <ListVideo className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Playlists Yet</h3>
          <p className="text-gray-600 mb-6">
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
      {!isLoading && playlistsData?.items && playlistsData.items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlistsData.items.map((playlist) => (
            <div
              key={playlist.id}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow overflow-hidden"
            >
              {/* Playlist Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                      <ListVideo className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-800 text-lg">{playlist.name}</h3>
                      <p className="text-sm text-gray-600">
                        {playlist.content_count || 0} items
                      </p>
                    </div>
                  </div>
                </div>

                {playlist.description && (
                  <p className="text-sm text-gray-600 line-clamp-2">
                    {playlist.description}
                  </p>
                )}
              </div>

              {/* Playlist Stats */}
              <div className="px-6 py-4 bg-gray-50">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Duration</p>
                    <p className="font-semibold text-gray-800">
                      {playlist.total_duration ? `${Math.floor(playlist.total_duration / 60)}m` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Status</p>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                      playlist.is_active
                        ? 'bg-green-100 text-green-700'
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
