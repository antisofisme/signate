import { Upload, CheckSquare, Square, Edit, Tag } from 'lucide-react'
import { Button } from '../shared'

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
    <div className="sticky top-0 z-50 bg-white pb-4 mb-4 border-b border-gray-200 px-6">
      <div className="flex items-center justify-between pt-4">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-gray-800">Content</h1>
        {selectedCount > 0 && (
          <div className="flex items-center gap-3">
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
              {selectedCount} selected
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              className="underline"
            >
              Clear
            </Button>
          </div>
        )}
        </div>
        <div className="flex items-center gap-3">
        {totalCount > 0 && (
          <Button
            variant="secondary"
            leftIcon={selectedCount === totalCount ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
            onClick={onToggleSelectAll}
          >
            {selectedCount === totalCount ? 'Deselect All' : 'Select All'}
          </Button>
        )}
        {selectedCount > 0 && (
          <>
            <Button
              variant="warning"
              leftIcon={<Edit className="w-5 h-5" />}
              onClick={onBulkEdit}
            >
              Bulk Edit ({selectedCount})
            </Button>
            <Button
              variant="success"
              leftIcon={<Tag className="w-5 h-5" />}
              onClick={onBulkTag}
            >
              Bulk Tag ({selectedCount})
            </Button>
          </>
        )}
        <Button
          variant="primary"
          leftIcon={<Upload className="w-5 h-5" />}
          onClick={onUpload}
        >
          Upload Content
        </Button>
        </div>
      </div>
    </div>
  )
}
