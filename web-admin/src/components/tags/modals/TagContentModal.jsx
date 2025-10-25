import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tagsAPI, contentAPI } from '../../../services/api'
import { X, Plus, Trash2, Film, Image as ImageIcon } from 'lucide-react'
import { showToast } from '../../../utils/toast'
import { Modal, Button } from '../../shared'

/**
 * TagContentModal Component
 * Modal for managing content assigned to a tag
 *
 * Features:
 * - List all content assigned to this tag
 * - Add new content to tag
 * - Remove content from tag
 * - Display order management
 *
 * @param {Object} tag - Tag object
 * @param {Function} onClose - Callback when modal should close
 */
export default function TagContentModal({ tag, onClose }) {
  const queryClient = useQueryClient()
  const [showContentSelector, setShowContentSelector] = useState(false)
  const [selectedContentId, setSelectedContentId] = useState(null)
  const [displayOrder, setDisplayOrder] = useState(0)

  // Fetch tag content
  const { data: tagContentData, isLoading } = useQuery({
    queryKey: ['tags', tag.id, 'content'],
    queryFn: () => tagsAPI.getContent(tag.id).then(res => res.data),
  })

  // Fetch all available content
  const { data: allContentData } = useQuery({
    queryKey: ['content'],
    queryFn: () => contentAPI.list().then(res => res.data),
    enabled: showContentSelector,
  })

  // Assign content mutation
  const assignMutation = useMutation({
    mutationFn: (data) => tagsAPI.assignContent(tag.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags', tag.id, 'content'])
      queryClient.invalidateQueries(['tags'])
      setShowContentSelector(false)
      setSelectedContentId(null)
      setDisplayOrder(0)
      showToast.success('Content assigned successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to assign content')
    }
  })

  // Unassign content mutation
  const unassignMutation = useMutation({
    mutationFn: (contentId) => tagsAPI.unassignContent(tag.id, contentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['tags', tag.id, 'content'])
      queryClient.invalidateQueries(['tags'])
      showToast.success('Content removed successfully!')
    },
    onError: (error) => {
      showToast.error(error.response?.data?.detail || 'Failed to remove content')
    }
  })

  const handleAssignContent = () => {
    if (!selectedContentId) {
      showToast.error('Please select content')
      return
    }

    assignMutation.mutate({
      content_id: parseInt(selectedContentId),
      display_order: parseInt(displayOrder) || 0,
      is_active: true
    })
  }

  const handleRemoveContent = (contentId) => {
    if (confirm('Remove this content from tag?')) {
      unassignMutation.mutate(contentId)
    }
  }

  // Get available content (not already assigned)
  const availableContent = allContentData?.items?.filter(
    content => !tagContentData?.some(tc => tc.content_id === content.id)
  ) || []

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="2xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Tag Content: {tag.tag_name}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage content assigned to this tag
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
          disabled={assignMutation.isLoading || unassignMutation.isLoading}
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Add Content Section */}
        {!showContentSelector ? (
          <div className="mb-6">
            <Button
              variant="primary"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setShowContentSelector(true)}
            >
              Add Content
            </Button>
          </div>
        ) : (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-gray-800">Add New Content</h3>
              <button
                onClick={() => {
                  setShowContentSelector(false)
                  setSelectedContentId(null)
                  setDisplayOrder(0)
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              {/* Content Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Content
                </label>
                <select
                  value={selectedContentId || ''}
                  onChange={(e) => setSelectedContentId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  disabled={assignMutation.isLoading}
                >
                  <option value="">-- Select Content --</option>
                  {availableContent.map(content => (
                    <option key={content.id} value={content.id}>
                      {content.title} ({content.content_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Display Order */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Order
                </label>
                <input
                  type="number"
                  value={displayOrder}
                  onChange={(e) => setDisplayOrder(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  disabled={assignMutation.isLoading}
                  min="0"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Lower numbers play first
                </p>
              </div>

              {/* Add Button */}
              <Button
                variant="primary"
                onClick={handleAssignContent}
                disabled={!selectedContentId || assignMutation.isLoading}
                className="w-full"
              >
                {assignMutation.isLoading ? 'Adding...' : 'Add to Tag'}
              </Button>
            </div>
          </div>
        )}

        {/* Content List */}
        <div>
          <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-xl">📋</span>
            Assigned Content ({tagContentData?.length || 0})
          </h3>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">
              Loading content...
            </div>
          ) : tagContentData && tagContentData.length > 0 ? (
            <div className="space-y-3">
              {tagContentData
                .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
                .map((item) => (
                  <div
                    key={item.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {/* Content Icon */}
                        <div className="flex-shrink-0">
                          {item.content_type === 'video' || item.content_type === 'webpage' ? (
                            <Film className="w-5 h-5 text-blue-600" />
                          ) : (
                            <ImageIcon className="w-5 h-5 text-green-600" />
                          )}
                        </div>

                        {/* Content Info */}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-800 truncate">
                            {item.title}
                          </h4>
                          {item.description && (
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {item.description}
                            </p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                            <span className="bg-gray-100 px-2 py-1 rounded">
                              {item.content_type}
                            </span>
                            <span>{item.duration}s</span>
                            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              Order: {item.display_order || 0}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Remove Button */}
                      <Button
                        variant="danger"
                        size="sm"
                        leftIcon={<Trash2 className="w-4 h-4" />}
                        onClick={() => handleRemoveContent(item.content_id)}
                        disabled={unassignMutation.isLoading}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-gray-200">
              <p>No content assigned to this tag</p>
              <p className="text-sm mt-1">Click "Add Content" to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t bg-gray-50 flex-shrink-0">
        <Button
          variant="secondary"
          onClick={onClose}
          className="w-full"
          disabled={assignMutation.isLoading || unassignMutation.isLoading}
        >
          Close
        </Button>
      </div>
    </Modal>
  )
}
