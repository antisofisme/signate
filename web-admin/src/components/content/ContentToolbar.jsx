import { Upload, CheckSquare, Square, Edit, Tag } from 'lucide-react'

/**
 * ContentToolbar Component
 * Top toolbar with selection controls and action buttons
 *
 * Features:
 * - Page title with selected count badge
 * - Clear selection button
 * - Select/Deselect All toggle button
 * - Bulk Edit button (shown when items selected)
 * - Bulk Tag button (shown when items selected)
 * - Upload Content button (always shown)
 * - Responsive layout with proper spacing
 * - Visual feedback for selection state
 *
 * @param {Set} selectedIds - Set of selected content IDs
 * @param {number} totalCount - Total number of content items
 * @param {Function} onClearSelection - Callback to clear all selections
 * @param {Function} onToggleSelectAll - Callback to toggle select/deselect all
 * @param {Function} onBulkEdit - Callback when bulk edit is clicked
 * @param {Function} onBulkTag - Callback when bulk tag is clicked
 * @param {Function} onUpload - Callback when upload is clicked
 */
export default function ContentToolbar({
  selectedIds,
  totalCount,
  onClearSelection,
  onToggleSelectAll,
  onBulkEdit,
  onBulkTag,
  onUpload
}) {
  const selectedCount = selectedIds.size

  return (
    <div className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-4">
        <h1 className="text-3xl font-bold text-gray-800">Content</h1>
        {selectedCount > 0 && (
          <div className="flex items-center gap-3">
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
              {selectedCount} selected
            </span>
            <button
              onClick={onClearSelection}
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Clear
            </button>
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        {totalCount > 0 && (
          <button
            onClick={onToggleSelectAll}
            className="flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            {selectedCount === totalCount ? (
              <CheckSquare className="w-5 h-5 mr-2" />
            ) : (
              <Square className="w-5 h-5 mr-2" />
            )}
            {selectedCount === totalCount ? 'Deselect All' : 'Select All'}
          </button>
        )}
        {selectedCount > 0 && (
          <>
            <button
              onClick={onBulkEdit}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Edit className="w-5 h-5 mr-2" />
              Bulk Edit ({selectedCount})
            </button>
            <button
              onClick={onBulkTag}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Tag className="w-5 h-5 mr-2" />
              Bulk Tag ({selectedCount})
            </button>
          </>
        )}
        <button
          onClick={onUpload}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Upload className="w-5 h-5 mr-2" />
          Upload Content
        </button>
      </div>
    </div>
  )
}
