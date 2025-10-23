/**
 * GroupingControls Component
 * Provides UI controls for grouping content by different criteria
 *
 * Features:
 * - Group by: None, Extension (Images/Videos), Tag, Device
 * - Visual feedback for active grouping mode
 * - Expand/Collapse all groups functionality
 * - Total content count display
 * - Icon indicators for each grouping mode
 * - Responsive layout with flex-wrap
 *
 * @param {string} groupBy - Current grouping mode: 'none', 'extension', 'tag', 'device'
 * @param {Function} onGroupByChange - Callback when grouping mode changes
 * @param {Function} onExpandAll - Callback when expand all is clicked
 * @param {Function} onCollapseAll - Callback when collapse all is clicked
 * @param {number} totalCount - Total number of content items
 */
export default function GroupingControls({
  groupBy,
  onGroupByChange,
  onExpandAll,
  onCollapseAll,
  totalCount
}) {
  return (
    <div className="bg-white rounded-xl shadow-md p-4 mb-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">Group by:</span>

          {/* Grouping Options */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onGroupByChange('none')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'none'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              None
            </button>
            <button
              onClick={() => onGroupByChange('extension')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'extension'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🖼️ Extension
            </button>
            <button
              onClick={() => onGroupByChange('tag')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'tag'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🏷️ Tag
            </button>
            <button
              onClick={() => onGroupByChange('device')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'device'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📺 Device
            </button>
          </div>
        </div>

        {/* Expand/Collapse All */}
        {groupBy !== 'none' && (
          <div className="flex items-center gap-2">
            <button
              onClick={onExpandAll}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
            >
              Expand All
            </button>
            <button
              onClick={onCollapseAll}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
            >
              Collapse All
            </button>
          </div>
        )}

        {/* Total Count */}
        <div className="text-sm text-gray-600">
          {totalCount || 0} content total
        </div>
      </div>
    </div>
  )
}
