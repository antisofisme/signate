import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { contentAPI, tagsAPI } from '../../../services/api'

/**
 * Helper function to get proxy image URL
 */
const getImageUrl = (content) => {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
  return `${baseUrl}/api/content/${content.id}/image`
}

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

      alert('Tags updated successfully!')
      onComplete()
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to update tags')
    }

    setUpdating(false)
  }

  const allTags = tagsData?.items || []

  if (assignmentQueries.isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6">
          <p className="text-gray-600">Loading assignments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Bulk Tag Assignment</h2>
            <p className="text-sm text-gray-600 mt-1">{selectedContent.length} content items selected</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            disabled={updating}
          >
            ✕
          </button>
        </div>

        {/* Content list with tag checkboxes */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {selectedContent.map((content) => {
              const selectedTags = tagSelections[content.id] || new Set()

              return (
                <div
                  key={content.id}
                  className="bg-gray-50 rounded-lg border-2 border-gray-200 p-4"
                >
                  {/* Title di atas */}
                  <div className="mb-3">
                    <p className="font-bold text-gray-800 text-lg">{content.title}</p>
                    <p className="text-sm text-gray-600">
                      {content.content_type.toUpperCase()} • {content.duration}s
                    </p>
                  </div>

                  {/* Horizontal layout: Thumbnail (left) + Tag pills (right) */}
                  <div className="grid grid-cols-12 gap-4">
                    {/* Left: Thumbnail saja (30-35%) */}
                    <div className="col-span-4">
                      {/* Thumbnail with aspect-video */}
                      <div className="relative bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
                        {content.content_type === 'video' ? (
                          <video
                            src={getImageUrl(content)}
                            className="w-full h-full object-cover"
                            preload="metadata"
                            controls
                            onLoadedMetadata={(e) => {
                              e.target.currentTime = 0.1 // Load first frame as thumbnail
                            }}
                          />
                        ) : (
                          <img
                            src={getImageUrl(content)}
                            alt={content.title}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none'
                              const parent = e.target.parentElement
                              if (!parent.querySelector('.video-icon-fallback')) {
                                const fallback = document.createElement('div')
                                fallback.className = 'video-icon-fallback flex flex-col items-center justify-center'
                                fallback.innerHTML = `
                                  <span class="text-5xl mb-2">📷</span>
                                  <span class="text-xs text-gray-600">Image</span>
                                `
                                parent.appendChild(fallback)
                              }
                            }}
                          />
                        )}
                      </div>
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
                                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
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
                        <div className="mt-3 text-xs text-gray-600">
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

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            type="button"
            onClick={handleUpdateAll}
            disabled={updating}
            className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {updating ? 'Updating...' : 'Update All'}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={updating}
            className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
