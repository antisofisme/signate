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
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Group by:</span>

          {/* Grouping Options */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onGroupByChange('none')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'none'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              None
            </button>
            <button
              onClick={() => onGroupByChange('extension')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'extension'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              🖼️ Extension
            </button>
            <button
              onClick={() => onGroupByChange('tag')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'tag'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              🏷️ Tag
            </button>
            <button
              onClick={() => onGroupByChange('device')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                groupBy === 'device'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
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
              className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              Expand All
            </button>
            <button
              onClick={onCollapseAll}
              className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              Collapse All
            </button>
          </div>
        )}

        {/* Total Count */}
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {totalCount || 0} content total
        </div>
      </div>
    </div>
  )
}
