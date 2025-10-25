import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI } from '../../../services/api'
import { Modal, ModalFooter, Button, FormInput } from '../../shared'
import { Copy, AlertCircle } from 'lucide-react'
import { showToast } from '../../../utils/toast'

/**
 * DuplicatePlaylistModal Component
 * Modal for duplicating an existing playlist with a new name
 *
 * Features:
 * - Pre-fills form with "Copy of [Original Name]"
 * - User can edit the name before duplicating
 * - Duplicates playlist structure and content
 * - Preserves schedule settings
 * - Does NOT copy device/tag assignments
 *
 * @param {Object} playlist - Playlist object to duplicate
 * @param {Function} onClose - Callback when modal should close
 */
export default function DuplicatePlaylistModal({ playlist, onClose }) {
  const queryClient = useQueryClient()
  const [newName, setNewName] = useState(`Copy of ${playlist.name}`)
  const [description, setDescription] = useState(playlist.description || '')

  // Duplicate playlist mutation
  const duplicateMutation = useMutation({
    mutationFn: async (data) => {
      // First, create the new playlist
      const createResponse = await playlistsAPI.create({
        name: data.name,
        description: data.description,
        is_active: false, // Start as inactive
        schedule: playlist.schedule // Copy schedule settings
      })

      const newPlaylistId = createResponse.data.id

      // Then, fetch content from original playlist
      const contentResponse = await playlistsAPI.getContent(playlist.id)
      const originalContent = contentResponse.data.items || []

      // Add content to the new playlist if there is any
      if (originalContent.length > 0) {
        const contentIds = originalContent.map(item => item.content_id)
        await playlistsAPI.assignContent(newPlaylistId, {
          content_ids: contentIds
        })
      }

      return createResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists'])
      onClose()
      showToast.success('Playlist duplicated successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to duplicate playlist')
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!newName.trim()) {
      showToast.error('Please enter a playlist name')
      return
    }

    duplicateMutation.mutate({
      name: newName.trim(),
      description: description.trim()
    })
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <Copy className="w-6 h-6 text-blue-600" />
          <span>Duplicate Playlist</span>
        </div>
      }
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          {/* Original Playlist Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">Duplicating:</span> {playlist.name}
            </p>
            <p className="text-xs text-blue-600 mt-1">
              {playlist.content_count || 0} content items will be copied
            </p>
          </div>

          {/* New Name Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Playlist Name *
            </label>
            <FormInput
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter new playlist name"
              required
              autoFocus
            />
          </div>

          {/* Description Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter description"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
            />
          </div>

          {/* Info Box */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-semibold mb-1">What will be copied:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Playlist name and description</li>
                <li>All content items and their order</li>
                <li>Schedule settings (start time, end time, days)</li>
              </ul>
              <p className="font-semibold mt-2 mb-1">What will NOT be copied:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Device and tag assignments</li>
                <li>Active status (will start as inactive)</li>
              </ul>
            </div>
          </div>

          {/* Footer */}
          <ModalFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={duplicateMutation.isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              leftIcon={<Copy className="w-4 h-4" />}
              disabled={duplicateMutation.isLoading}
            >
              {duplicateMutation.isLoading ? 'Duplicating...' : 'Duplicate Playlist'}
            </Button>
          </ModalFooter>
        </div>
      </form>
    </Modal>
  )
}
