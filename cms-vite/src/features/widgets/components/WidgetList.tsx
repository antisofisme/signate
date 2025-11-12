/**
 * Widget List Component
 * Display widgets in a data table with actions
 */

import { useState } from 'react'
import { Palette, ClipboardList, Edit, Trash2 } from 'lucide-react'
import { WIDGET_TYPES, type Widget, type WidgetType } from '../types/widget.types'
import { formatDateTime } from '@/shared/utils/formatters'
import { renderIcon } from '@/shared/utils/iconHelper'

interface WidgetListProps {
  widgets: Widget[]
  isLoading?: boolean
  onEdit: (widget: Widget) => void
  onDelete: (widget: Widget) => void
  onAssign: (widget: Widget) => void
}

export const WidgetList = ({
  widgets,
  isLoading,
  onEdit,
  onDelete,
  onAssign,
}: WidgetListProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<WidgetType | 'all'>('all')

  // Filter widgets
  const filteredWidgets = widgets.filter((widget) => {
    const matchesSearch = widget.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || widget.widget_type === filterType

    return matchesSearch && matchesType
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-16 bg-gray-100 dark:bg-gray-700 rounded-lg animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (widgets.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
        <Palette className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No widgets yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Create your first widget to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search widgets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Type filter */}
        <div className="w-full md:w-48">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as WidgetType | 'all')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="all">All Types</option>
            {Object.values(WIDGET_TYPES).map((type) => (
              <option key={type.type} value={type.type}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {filteredWidgets.length} of {widgets.length} widgets
      </div>

      {/* Widget cards */}
      <div className="space-y-3">
        {filteredWidgets.map((widget) => {
          const typeInfo = WIDGET_TYPES[widget.widget_type]

          return (
            <div
              key={widget.id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* Widget info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {renderIcon(typeInfo.icon, { className: 'w-8 h-8' })}
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{widget.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                          {typeInfo.label}
                        </span>
                        <span>•</span>
                        <span>
                          {widget.layout.width}×{widget.layout.height} px
                        </span>
                        <span>•</span>
                        <span>
                          Position: ({widget.layout.x}, {widget.layout.y})
                        </span>
                      </div>
                    </div>
                  </div>

                  {widget.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{widget.description}</p>
                  )}

                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Created {formatDateTime(widget.created_at)}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => onAssign(widget)}
                    className="px-3 py-1.5 text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/50 flex items-center gap-1"
                    title="Assign to Playlist"
                  >
                    <ClipboardList className="w-4 h-4" />
                    Assign
                  </button>
                  <button
                    onClick={() => onEdit(widget)}
                    className="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50 flex items-center gap-1"
                    title="Edit Widget"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(widget)}
                    className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-100 dark:hover:bg-red-900/50 flex items-center gap-1"
                    title="Delete Widget"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* No results */}
      {filteredWidgets.length === 0 && (
        <div className="text-center py-8 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">No widgets match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterType('all')
            }}
            className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

export default WidgetList
