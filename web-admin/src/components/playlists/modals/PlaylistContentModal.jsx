import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { playlistsAPI } from '../../../services/api'
import { Modal, ModalFooter, Button, Thumbnail } from '../../shared'
import { Plus, Trash2, GripVertical, Clock } from 'lucide-react'
import { showToast } from '../../../utils/toast'
import ContentSelectorModal from './ContentSelectorModal'

/**
 * PlaylistContentModal Component
 * Modal for managing content items in a playlist
 *
 * Features:
 * - View all content items in the playlist
 * - Add new content (opens ContentSelectorModal)
 * - Remove content items
 * - Drag & drop reordering with visual feedback
 * - Edit duration for each content item
 * - Real-time total duration calculation
 * - Auto-save on changes
 *
 * @param {Object} playlist - Playlist object to manage
 * @param {Function} onClose - Callback when modal should close
 */
export default function PlaylistContentModal({ playlist, onClose }) {
  const queryClient = useQueryClient()
  const [showContentSelector, setShowContentSelector] = useState(false)
  const [contentItems, setContentItems] = useState([])
  const [draggedIndex, setDraggedIndex] = useState(null)
  const saveTimeoutRef = useRef(null)

  // Fetch playlist content
  const { data: playlistContent, isLoading } = useQuery({
    queryKey: ['playlists', playlist.id, 'content'],
    queryFn: () => playlistsAPI.getContent(playlist.id).then(res => res.data),
  })

  // Initialize content items when data loads
  useEffect(() => {
    if (playlistContent?.items) {
      setContentItems(playlistContent.items)
    }
  }, [playlistContent])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [])

  // Add content mutation
  const addContentMutation = useMutation({
    mutationFn: (contentIds) => playlistsAPI.assignContent(playlist.id, { content_ids: contentIds }),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'content'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Content added to playlist!')
      setShowContentSelector(false)
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to add content')
    }
  })

  // Remove content mutation
  const removeContentMutation = useMutation({
    mutationFn: (contentId) => playlistsAPI.removeContent(playlist.id, contentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['playlists', playlist.id, 'content'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Content removed from playlist!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to remove content')
    }
  })

  // Reorder content mutation
  const reorderContentMutation = useMutation({
    mutationFn: (orderedItems) => {
      const orderData = orderedItems.map((item, index) => ({
        id: item.id,  // PlaylistContent.id (not content_id!)
        order_index: index,
        duration: item.duration
      }))
      console.log('📤 Sending reorder request:', { content_items: orderData })
      return playlistsAPI.reorderContent(playlist.id, { content_items: orderData })  // Match backend schema!
    },
    onSuccess: (response) => {
      console.log('✅ Reorder successful!', response)
      queryClient.invalidateQueries(['playlists', playlist.id, 'content'])
      queryClient.invalidateQueries(['playlists'])
      showToast.success('Content order updated!')
    },
    onError: (error) => {
      console.error('❌ Reorder failed:', error.response?.data || error.message)
      showToast.error(error.response?.data?.detail || 'Failed to reorder content')
    }
  })

  // Handle adding content
  const handleAddContent = (selectedContent) => {
    const contentIds = selectedContent.map(c => c.id)
    addContentMutation.mutate(contentIds)
  }

  // Handle removing content
  const handleRemoveContent = (item) => {
    if (confirm(`Remove "${item.content_name}" from playlist?`)) {
      removeContentMutation.mutate(item.id)
    }
  }

  // Handle duration change with debouncing
  const handleDurationChange = (index, newDuration) => {
    const updatedItems = [...contentItems]
    updatedItems[index].duration = parseInt(newDuration) || 0
    setContentItems(updatedItems)

    // Clear previous timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    // Auto-save after 1 second delay
    saveTimeoutRef.current = setTimeout(() => {
      reorderContentMutation.mutate(updatedItems)
    }, 1000)
  }

  // Drag and Drop handlers
  const handleDragStart = (e, index) => {
    console.log('🟢 Drag started from index:', index)
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e, index) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'

    if (draggedIndex === null || draggedIndex === index) return

    console.log(`🔄 Dragging from ${draggedIndex} to ${index}`)

    // Reorder items
    const newItems = [...contentItems]
    const draggedItem = newItems[draggedIndex]
    newItems.splice(draggedIndex, 1)
    newItems.splice(index, 0, draggedItem)

    setContentItems(newItems)
    setDraggedIndex(index)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    console.log('🎯 Drop! Final order:', contentItems.map((item, i) => ({ index: i, name: item.content_name, id: item.id })))

    // Save new order
    if (draggedIndex !== null) {
      reorderContentMutation.mutate(contentItems)
    }

    setDraggedIndex(null)
  }

  const handleDragEnd = () => {
    console.log('🏁 DragEnd triggered (cleanup only)')
    setDraggedIndex(null)
  }

  // Calculate total duration
  const totalDuration = contentItems.reduce((sum, item) => sum + (item.duration || 0), 0)

  // Get already selected content IDs to prevent duplicates
  const alreadySelectedIds = contentItems.map(item => item.content_id)

  return (
    <>
      <Modal
        isOpen={true}
        onClose={onClose}
        title={`Manage Content: ${playlist.name}`}
        size="2xl"
      >
        <div className="space-y-4">
          {/* Header with Add Button */}
          <div className="flex items-center justify-between pb-3 border-b">
            <div>
              <p className="text-sm text-gray-600">
                {contentItems.length} item{contentItems.length !== 1 ? 's' : ''} • Total: {Math.floor(totalDuration / 60)}m {totalDuration % 60}s
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setShowContentSelector(true)}
            >
              Add Content
            </Button>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && contentItems.length === 0 && (
            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
              <p className="text-gray-600 font-medium mb-2">No content in this playlist</p>
              <p className="text-sm text-gray-500 mb-4">Add content to start building your playlist</p>
              <Button
                variant="primary"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => setShowContentSelector(true)}
              >
                Add Content
              </Button>
            </div>
          )}

          {/* Content List with Drag & Drop */}
          {!isLoading && contentItems.length > 0 && (
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
              {contentItems.map((item, index) => (
                <div
                  key={`${item.content_id}-${index}`}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDrop={handleDrop}
                  className={`
                    flex items-center gap-3 p-3 bg-white rounded-lg border-2
                    transition-all
                    ${draggedIndex === index
                      ? 'border-blue-500 shadow-lg opacity-50'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                    }
                  `}
                >
                  {/* Drag Handle - Only this is draggable! */}
                  <div
                    draggable
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragEnd={handleDragEnd}
                    className="flex-shrink-0 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
                  >
                    <GripVertical className="w-5 h-5" />
                  </div>

                  {/* Order Number */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-600">
                    {index + 1}
                  </div>

                  {/* Thumbnail */}
                  <div className="flex-shrink-0 w-24">
                    <Thumbnail
                      content={{
                        id: item.content_id,
                        content_type: item.content_type,
                        title: item.content_name
                      }}
                      size="sm"
                      aspectRatio="video"
                    />
                  </div>

                  {/* Content Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 truncate">
                      {item.content_name}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">
                      {item.content_type}
                    </p>
                  </div>

                  {/* Duration Input */}
                  <div className="flex-shrink-0 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={item.duration || 10}
                      onChange={(e) => handleDurationChange(index, e.target.value)}
                      className="w-16 px-2 py-1 border rounded text-sm text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <span className="text-xs text-gray-500">sec</span>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => handleRemoveContent(item)}
                    className="flex-shrink-0 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove from playlist"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Info Text */}
          {contentItems.length > 0 && (
            <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
              💡 Drag and drop to reorder content. Changes are saved automatically.
            </div>
          )}

          {/* Footer */}
          <ModalFooter>
            <Button variant="secondary" onClick={onClose} className="flex-1">
              Close
            </Button>
          </ModalFooter>
        </div>
      </Modal>

      {/* Content Selector Modal */}
      {showContentSelector && (
        <ContentSelectorModal
          alreadySelected={alreadySelectedIds}
          onClose={() => setShowContentSelector(false)}
          onSubmit={handleAddContent}
        />
      )}
    </>
  )
}
