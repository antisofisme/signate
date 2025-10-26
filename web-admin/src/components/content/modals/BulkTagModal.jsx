import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { contentAPI, tagsAPI } from '../../../services/api'
import { Thumbnail, Modal, ModalFooter, Button } from '../../shared'
import { showToast } from '../../../utils/toast'

/**
 * BulkTagModal Component
 * Modal for bulk tag assignment/unassignment to multiple content items
 *
 * Features:
 * - Assign/unassign tags to multiple content items at once
 * - Visual tag pill interface (green=selected, gray=unselected)
 * - Pre-populates existing tag assignments
 * - Horizontal layout: thumbnail (left) + clickable tag pills (right)
 * - Diff-based updates (only adds/removes changed tags)
 * - Comprehensive error handling
 *
 * @param {Set} selectedIds - Set of selected content IDs
 * @param {Object} contentData - Content data containing all items
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onComplete - Callback after successful updates
 */
export default function BulkTagModal({ selectedIds, contentData, onClose, onComplete }) {
  const queryClient = useQueryClient()
  const [updating, setUpdating] = useState(false)

  // Get selected content items
  const selectedContent = contentData?.items?.filter(c => selectedIds.has(c.id)) || []

  // Fetch all tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsAPI.list().then(res => res.data),
  })

  // Fetch assignments for all selected content items
  const assignmentQueries = useQuery({
    queryKey: ['bulk-tag-assignments', [...selectedIds]],
    queryFn: async () => {
      const assignmentsMap = {}
      for (const contentId of selectedIds) {
        const res = await contentAPI.getAssignments(contentId)
        assignmentsMap[contentId] = res.data
      }
      return assignmentsMap
    },
    enabled: selectedIds.size > 0
  })

  // State: Map of contentId -> Set of selected tag IDs
  const [tagSelections, setTagSelections] = useState(() => {
    const initial = {}
    selectedContent.forEach(content => {
      initial[content.id] = new Set()
    })
    return initial
  })

  // Pre-populate tag selections when assignments load
  const [initialized, setInitialized] = useState(false)
  if (assignmentQueries.data && !assignmentQueries.isLoading && !initialized) {
    const newSelections = {}
    selectedContent.forEach(content => {
      const assignments = assignmentQueries.data[content.id] || []
      const tagIds = new Set()
      assignments.forEach(assignment => {
        if (assignment.tag_id) {
          tagIds.add(assignment.tag_id)
        }
      })
      newSelections[content.id] = tagIds
    })
    setTagSelections(newSelections)
    setInitialized(true)
  }

  const toggleTag = (contentId, tagId) => {
    setTagSelections(prev => {
      const newSelections = { ...prev }
      const currentSet = new Set(prev[contentId] || [])

      if (currentSet.has(tagId)) {
        currentSet.delete(tagId)
      } else {
        currentSet.add(tagId)
      }

      newSelections[contentId] = currentSet
      return newSelections
    })
  }

  const handleUpdateAll = async () => {
    setUpdating(true)

    try {
      // For each content item
      for (const content of selectedContent) {
        const currentAssignments = assignmentQueries.data[content.id] || []
        const currentTagIds = new Set(
          currentAssignments
            .filter(a => a.tag_id)
            .map(a => a.tag_id)
        )
        const selectedTagIds = tagSelections[content.id] || new Set()

        // Tags to add
        const tagsToAdd = [...selectedTagIds].filter(id => !currentTagIds.has(id))
        // Tags to remove
        const tagsToRemove = [...currentTagIds].filter(id => !selectedTagIds.has(id))

        // Add new tags
        for (const tagId of tagsToAdd) {
          try {
            await contentAPI.assign(content.id, {
              tag_id: tagId,
              priority: 0
            })
          } catch (err) {
            // Ignore if already assigned
            if (!err.response?.data?.detail?.includes('already exists')) {
              throw err
            }
          }
        }

        // Remove unselected tags
        for (const tagId of tagsToRemove) {
          try {
            await contentAPI.unassign(content.id, {
              tag_id: tagId
            })
          } catch (err) {
            console.error('Unassign error:', err)
          }
        }
      }

      // Refresh queries
      queryClient.invalidateQueries(['bulk-tag-assignments'])
      queryClient.invalidateQueries(['content'])
      queryClient.invalidateQueries(['content-assignments'])

      showToast.success('Tags updated successfully!')
      onComplete()
    } catch (error) {
      showToast.error(error.response?.data?.detail || 'Failed to update tags')
    }

    setUpdating(false)
  }

  const allTags = tagsData?.items || []

  if (assignmentQueries.isLoading) {
    return (
      <Modal isOpen={true} onClose={onClose} size="md">
        <p className="text-gray-600 dark:text-gray-400 text-center">Loading assignments...</p>
      </Modal>
    )
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      size="3xl"
      showCloseButton={false}
      bodyClassName="flex-1 overflow-hidden flex flex-col p-0"
    >
      {/* Custom Header - Fixed */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Bulk Tag Assignment</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{selectedContent.length} content items selected</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
            aria-label="Close modal"
            disabled={updating}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content list with tag checkboxes - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {selectedContent.map((content) => {
              const selectedTags = tagSelections[content.id] || new Set()

              return (
                <div
                  key={content.id}
                  className="bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-gray-200 dark:border-gray-700 p-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  {/* Title di atas */}
                  <div className="mb-3">
                    <p className="font-bold text-gray-900 dark:text-white text-lg">{content.title}</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {content.content_type.toUpperCase()} • {content.duration}s
                    </p>
                  </div>

                  {/* Horizontal layout: Thumbnail (left) + Tag pills (right) */}
                  <div className="grid grid-cols-12 gap-4">
                    {/* Left: Thumbnail saja (30-35%) */}
                    <div className="col-span-4">
                      <Thumbnail
                        content={content}
                        size="md"
                        aspectRatio="video"
                        showPlayIcon={false}
                      />
                    </div>

                    {/* Right: Tag pills (65-70%) */}
                    <div className="col-span-8">
                      <div className="flex flex-wrap gap-2">
                        {allTags.map((tag) => {
                          const isSelected = selectedTags.has(tag.id)
                          return (
                            <div
                              key={tag.id}
                              onClick={() => !updating && toggleTag(content.id, tag.id)}
                              className={`inline-flex flex-col px-3 py-2 rounded-xl cursor-pointer transition-all ${
                                isSelected
                                  ? 'bg-green-500 text-white shadow-md'
                                  : 'bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-400 dark:hover:bg-gray-600'
                              }`}
                              style={{
                                userSelect: 'none',
                                fontSize: '11px'
                              }}
                            >
                              <div className="flex items-center gap-1">
                                <span>🏷️</span>
                                <span className="font-medium">{tag.tag_name}</span>
                              </div>
                              {tag.description && (
                                <span className="text-[10px] opacity-90 mt-0.5">
                                  {tag.description}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      {selectedTags.size > 0 && (
                        <div className="mt-3 text-xs text-gray-600 dark:text-gray-400">
                          ✓ {selectedTags.size} tag(s) selected
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      {/* Footer - Fixed */}
      <div className="p-6 border-t bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 flex-shrink-0">
        <ModalFooter align="right">
          <Button
            type="button"
            onClick={onClose}
            disabled={updating}
            variant="secondary"
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleUpdateAll}
            disabled={updating}
            variant="success"
            className="flex-1"
          >
            {updating ? 'Updating...' : 'Update All'}
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  )
}
