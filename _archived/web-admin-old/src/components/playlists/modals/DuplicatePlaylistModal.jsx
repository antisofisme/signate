import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI } from '../../../services/api'
import { Modal, Button, FormInput } from '../../shared'
import { Copy, AlertCircle } from 'lucide-react'
import { showToast } from '../../../utils/toast'

/**
 * DuplicatePlaylistModal Component
 * Modal for duplicating an existing playlist with a new name
 *
 * Features:
 * - Proper modal structure: sticky header, scrollable content, sticky footer
 * - Pre-fills form with "Copy of [Original Name]"
 * - User can edit the name before duplicating
 * - Duplicates playlist structure and content
 * - Preserves schedule settings
 * - Does NOT copy device/tag assignments
 * - Click outside to close, ESC to close
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

  // Footer with action buttons
  const footer = (
    <div className="flex gap-3">
      <Button
        type="button"
        variant="secondary"
        onClick={onClose}
        disabled={duplicateMutation.isLoading}
        className="flex-1"
      >
        Cancel
      </Button>
      <Button
        type="submit"
        variant="primary"
        leftIcon={<Copy className="w-4 h-4" />}
        disabled={duplicateMutation.isLoading}
        onClick={handleSubmit}
        className="flex-1"
      >
        {duplicateMutation.isLoading ? 'Duplicating...' : 'Duplicate Playlist'}
      </Button>
    </div>
  )

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
      footer={footer}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Original Playlist Info */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <span className="font-semibold">Duplicating:</span> {playlist.name}
          </p>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            {playlist.content_count || 0} content items will be copied
          </p>
        </div>

        {/* New Name Input */}
        <FormInput
          label="New Playlist Name"
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Enter new playlist name"
          required
          autoFocus
        />

        {/* Description Input */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            Description (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description of what this playlist contains..."
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 resize-none"
          />
        </div>

        {/* Info Box */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800 dark:text-yellow-300">
            <p className="font-semibold mb-2">What will be copied:</p>
            <ul className="list-disc list-inside space-y-1 text-xs mb-3">
              <li>Playlist name and description</li>
              <li>All content items and their order</li>
              <li>Schedule settings (start time, end time, days)</li>
            </ul>
            <p className="font-semibold mb-2">What will NOT be copied:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Device and tag assignments</li>
              <li>Active status (will start as inactive)</li>
            </ul>
          </div>
        </div>
      </form>
    </Modal>
  )
}
