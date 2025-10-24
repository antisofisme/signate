import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { contentAPI } from '../../../services/api'

/**
 * Helper function to get proxy image URL
 */
const getImageUrl = (content) => {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'
  return `${baseUrl}/api/content/${content.id}/image`
}

/**
 * BulkEditModal Component
 * Modal for editing multiple content items individually with side-by-side preview and form layout
 *
 * Features:
 * - Individual edit fields for each selected content item
 * - Side-by-side layout: preview (left) + edit form (right)
 * - Parallel bulk update with per-item progress tracking
 * - Change detection (only sends changed fields to API)
 * - Visual status indicators (pending, updating, success, failed)
 * - Comprehensive error handling with error messages
 *
 * @param {Set} selectedIds - Set of selected content IDs
 * @param {Object} contentData - Content data containing all items
 * @param {Function} onClose - Callback when modal should close
 * @param {Function} onComplete - Callback after successful updates
 */
export default function BulkEditModal({ selectedIds, contentData, onClose, onComplete }) {
  const queryClient = useQueryClient()
  const [updating, setUpdating] = useState(false)
  const [updateProgress, setUpdateProgress] = useState([])

  // Get selected content items
  const selectedContent = contentData?.items?.filter(c => selectedIds.has(c.id)) || []

  // State for individual edits - Map of contentId -> {title, description, duration, video_start_time, video_end_time}
  const [edits, setEdits] = useState(() => {
    const initialEdits = {}
    selectedContent.forEach(content => {
      const startTime = content.video_start_time || 0
      const endTime = content.video_end_time

      // Auto-calculate duration for videos
      let duration = content.duration
      if (content.content_type === 'video') {
        if (endTime && endTime > startTime) {
          // Calculate from segment
          duration = Math.ceil(endTime - startTime)
        } else if (content.video_duration) {
          // Calculate from total video length - start time
          duration = Math.ceil(content.video_duration - startTime)
        }
      }

      initialEdits[content.id] = {
        title: content.title,
        description: content.description || '',
        duration: duration,
        video_start_time: startTime,
        video_end_time: endTime
      }
    })
    return initialEdits
  })

  const updateEdit = (contentId, field, value) => {
    setEdits(prev => {
      const newEdits = {
        ...prev,
        [contentId]: {
          ...prev[contentId],
          [field]: value
        }
      }

      // Auto-calculate duration for video segments
      const content = selectedContent.find(c => c.id === contentId)
      if (content?.content_type === 'video' && (field === 'video_start_time' || field === 'video_end_time')) {
        const startTime = field === 'video_start_time' ? value : newEdits[contentId].video_start_time || 0
        const endTime = field === 'video_end_time' ? value : newEdits[contentId].video_end_time

        if (endTime && endTime > startTime) {
          // Calculate duration from segment
          newEdits[contentId].duration = Math.ceil(endTime - startTime)
        } else if (content.video_duration && !endTime) {
          // If no end time, duration = total video length - start time
          newEdits[contentId].duration = Math.ceil(content.video_duration - startTime)
        }
      }

      return newEdits
    })
  }

  const handleBulkUpdate = async (e) => {
    e.preventDefault()

    setUpdating(true)
    setUpdateProgress(selectedContent.map(() => ({ status: 'pending', error: null })))

    let successCount = 0
    let failCount = 0

    // Update all items with their individual edits
    const updatePromises = selectedContent.map(async (content, index) => {
      try {
        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'updating', error: null }
          return newProgress
        })

        const editedData = edits[content.id]
        const updateData = {}

        // Only include fields that have changed
        if (editedData.title !== content.title) {
          updateData.title = editedData.title
        }
        if (editedData.description !== (content.description || '')) {
          updateData.description = editedData.description
        }
        if (editedData.duration !== content.duration) {
          updateData.duration = editedData.duration
        }

        // Video segment timing (only for videos)
        if (content.content_type === 'video') {
          if (editedData.video_start_time !== (content.video_start_time || 0)) {
            updateData.video_start_time = editedData.video_start_time
          }
          if (editedData.video_end_time !== content.video_end_time) {
            updateData.video_end_time = editedData.video_end_time
          }
        }

        // Only call API if there are changes
        if (Object.keys(updateData).length > 0) {
          await contentAPI.update(content.id, updateData)
        }

        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = { status: 'success', error: null }
          return newProgress
        })
        successCount++
      } catch (error) {
        setUpdateProgress(prev => {
          const newProgress = [...prev]
          newProgress[index] = {
            status: 'failed',
            error: error.response?.data?.detail || 'Update failed'
          }
          return newProgress
        })
        failCount++
      }
    })

    await Promise.all(updatePromises)
    queryClient.invalidateQueries(['content'])
    setUpdating(false)

    alert(`Bulk update complete!\n✅ Success: ${successCount}\n❌ Failed: ${failCount}`)

    if (successCount > 0) {
      onComplete()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Bulk Edit Content</h2>
            <p className="text-sm text-gray-600 mt-1">{selectedContent.length} items selected</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-3xl leading-none"
            disabled={updating}
          >
            ×
          </button>
        </div>

        {/* Form - List of individual item editors */}
        <form onSubmit={handleBulkUpdate} className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Individual Item Editors */}
            <div className="space-y-4">
              <h3 className="font-bold text-gray-700 text-lg flex items-center gap-2">
                <span>✏️</span>
                Edit Individual Items
              </h3>
              {selectedContent.map((content, index) => (
              <div
                key={content.id}
                className="bg-gray-50 p-4 rounded-lg border-2 border-gray-200"
              >
                {/* Side-by-side layout: Preview LEFT, Form RIGHT */}
                <div className="grid grid-cols-12 gap-4 items-start">
                  {/* LEFT: Preview Content (30-35% width) */}
                  <div className="col-span-4 flex flex-col">
                    <div className="relative bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg overflow-hidden max-h-48 flex items-center justify-center">
                      {content.content_type === 'video' ? (
                        <video
                          src={getImageUrl(content)}
                          className="w-full h-full object-contain"
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
                          className="w-full h-full object-contain"
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

                      {/* Status badge */}
                      <div className="absolute top-2 right-2 text-3xl bg-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg">
                        {updateProgress[index]?.status === 'pending' && '⏳'}
                        {updateProgress[index]?.status === 'updating' && '🔄'}
                        {updateProgress[index]?.status === 'success' && '✅'}
                        {updateProgress[index]?.status === 'failed' && '❌'}
                      </div>
                    </div>

                    {/* Original info below preview */}
                    <div className="mt-2 px-2 flex-shrink-0">
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Original</p>
                      <p className="font-medium text-gray-800 truncate">{content.title}</p>
                      <p className="text-xs text-gray-500">{content.content_type.toUpperCase()} • {content.duration}s</p>
                    </div>
                  </div>

                  {/* RIGHT: Form Fields (65-70% width) */}
                  <div className="col-span-8 flex flex-col space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Title
                      </label>
                      <input
                        type="text"
                        value={edits[content.id]?.title || ''}
                        onChange={(e) => updateEdit(content.id, 'title', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={updating}
                        placeholder="Content title"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <textarea
                        value={edits[content.id]?.description || ''}
                        onChange={(e) => updateEdit(content.id, 'description', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={updating}
                        rows={3}
                        placeholder="Content description (optional)"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Duration (seconds)
                        {content.content_type === 'video' && (
                          <span className="text-xs text-blue-600 ml-2">
                            ⚡ Auto-calculated from segment
                          </span>
                        )}
                      </label>
                      <input
                        type="number"
                        value={edits[content.id]?.duration || 10}
                        onChange={(e) => updateEdit(content.id, 'duration', parseInt(e.target.value) || 10)}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm ${
                          content.content_type === 'video'
                            ? 'border-gray-300 bg-gray-100 cursor-not-allowed'
                            : 'border-gray-300'
                        }`}
                        disabled={updating || content.content_type === 'video'}
                        min={1}
                        readOnly={content.content_type === 'video'}
                      />
                      {content.content_type === 'video' && (
                        <p className="text-xs text-gray-500 mt-1">
                          📊 Auto-calculated: {edits[content.id]?.video_end_time
                            ? `${edits[content.id]?.video_end_time}s - ${edits[content.id]?.video_start_time}s = ${edits[content.id]?.duration}s`
                            : `Total video (${content.video_duration?.toFixed(0) || '?'}s) - Start (${edits[content.id]?.video_start_time}s) = ${edits[content.id]?.duration}s`
                          }
                        </p>
                      )}
                    </div>

                    {/* Video Segment Timing (only for videos) */}
                    {content.content_type === 'video' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            🎬 Start Time (seconds)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            value={edits[content.id]?.video_start_time || 0}
                            onChange={(e) => updateEdit(content.id, 'video_start_time', parseFloat(e.target.value) || 0)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            disabled={updating}
                            min={0}
                            placeholder="0 (from beginning)"
                          />
                          <p className="text-xs text-gray-500 mt-1">Start video playback from this time</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            🏁 End Time (seconds)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            value={edits[content.id]?.video_end_time || ''}
                            onChange={(e) => updateEdit(content.id, 'video_end_time', e.target.value ? parseFloat(e.target.value) : null)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                            disabled={updating}
                            min={0}
                            placeholder="(play until end)"
                          />
                          <p className="text-xs text-gray-500 mt-1">Stop video at this time (leave empty to play until end)</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Show error if failed - Full width below */}
                {updateProgress[index]?.status === 'failed' && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    Error: {updateProgress[index]?.error}
                  </div>
                )}
              </div>
              ))}
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex gap-3">
          <button
            type="submit"
            onClick={handleBulkUpdate}
            disabled={updating}
            className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {updating ? 'Updating...' : `Update ${selectedContent.length} Items`}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={updating}
            className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {updating ? 'Please wait...' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}
