import { FileImage, Edit, Trash2 } from 'lucide-react'
import VideoThumbnail from './VideoThumbnail'
import AssignmentBadge from './AssignmentBadge'

/**
 * ContentCard Component
 * Displays a single content item with thumbnail, metadata, and action buttons
 *
 * Features:
 * - Checkbox selection for bulk operations
 * - Video thumbnail preview with HTML5 video
 * - Image thumbnail with fallback
 * - Comprehensive metadata display (resolution, codec, bitrate, file size)
 * - Active status badge
 * - Assignment badge showing device/tag counts
 * - Edit and delete action buttons
 * - Click to preview functionality
 * - Visual selection state with ring indicator
 *
 * @param {Object} content - Content object to display
 * @param {boolean} isSelected - Whether the content is selected
 * @param {Function} onToggleSelection - Callback when checkbox is toggled
 * @param {Function} onPreview - Callback when card is clicked for preview
 * @param {Function} onEdit - Callback when edit button is clicked
 * @param {Function} onDelete - Callback when delete button is clicked
 * @param {Function} getImageUrl - Helper function to get image URL for content
 */
export default function ContentCard({
  content,
  isSelected,
  onToggleSelection,
  onPreview,
  onEdit,
  onDelete,
  getImageUrl
}) {
  return (
    <div
      onClick={() => onPreview(content)}
      className={`bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-all cursor-pointer relative ${
        isSelected ? 'ring-4 ring-blue-500' : ''
      }`}
    >
      {/* Checkbox for selection */}
      <div className="absolute top-2 left-2 z-10">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => onToggleSelection(content.id, e)}
          onClick={(e) => e.stopPropagation()}
          className="w-5 h-5 rounded border-2 border-white shadow-lg cursor-pointer accent-blue-600"
        />
      </div>

      {/* Preview Thumbnail */}
      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
        {content.content_type === 'video' ? (
          <VideoThumbnail content={content} />
        ) : (
          <>
            <img
              src={getImageUrl(content)}
              alt={content.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <FileImage className="w-16 h-16 text-gray-400 opacity-50" />
            </div>
          </>
        )}

        {/* Badges */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
          {content.is_active && (
            <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
              Active
            </div>
          )}
          <AssignmentBadge contentId={content.id} />
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="font-bold text-gray-800 mb-1 text-sm truncate">{content.title}</h3>

        {/* Metadata */}
        <div className="space-y-1 mb-2">
          {content.resolution && (
            <div className="flex items-center gap-1 text-xs text-gray-600">
              <span className="font-medium">📐</span>
              <span>{content.resolution}</span>
            </div>
          )}
          {content.codec && (
            <div className="flex items-center gap-1 text-xs text-gray-600">
              <span className="font-medium">🎞️</span>
              <span className="uppercase">{content.codec}</span>
              {content.fps && <span>@ {content.fps}fps</span>}
            </div>
          )}
          {content.bitrate && (
            <div className="flex items-center gap-1 text-xs text-gray-600">
              <span className="font-medium">⚡</span>
              <span>{content.bitrate} kbps</span>
            </div>
          )}
          {content.file_size && (
            <div className="flex items-center gap-1 text-xs text-gray-600">
              <span className="font-medium">💾</span>
              <span>{(content.file_size / 1024 / 1024).toFixed(1)} MB</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 mb-2 pt-2 border-t">
          <span className="font-medium">{content.content_type.toUpperCase()}</span>
          <span>{content.duration}s</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={(e) => onEdit(e, content)}
            className="flex-1 flex items-center justify-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <Edit className="w-4 h-4 mr-1" />
            Edit
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (confirm('Delete this content?')) {
                onDelete(content.id)
              }
            }}
            className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
