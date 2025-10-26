/**
 * PageHeader Component
 * Reusable sticky header for all pages with consistent layout
 *
 * Features:
 * - Sticky header that doesn't scroll
 * - Title and description
 * - Right-aligned action buttons
 * - Optional search bar (left of buttons)
 * - Optional stats bar below header
 * - Fully responsive (mobile/tablet/desktop)
 * - Floating action button on mobile
 *
 * Usage:
 * <PageHeader
 *   title="Tags"
 *   description="Organize and manage tags for device grouping"
 *   actions={<Button>Create Tag</Button>}
 *   searchBar={<SearchInput />}
 *   stats={[
 *     { label: 'Total', value: 24, color: 'blue' },
 *     { label: 'Active', value: 20, color: 'green' }
 *   ]}
 * />
 */

import { Plus } from 'lucide-react'

export default function PageHeader({
  title,
  description,
  actions,
  searchBar,
  stats,
  activeFilter,
  onStatClick
}) {
  // Extract the onClick handler from actions prop
  const getActionHandler = () => {
    if (!actions) return null

    // If actions is a React element with onClick
    if (actions.props && actions.props.onClick) {
      return actions.props.onClick
    }
    return null
  }

  const actionHandler = getActionHandler()

  return (
    <>
      <div className="fixed top-0 left-0 right-0 lg:left-64 z-40 bg-white border-b border-gray-200 shadow-md">
        <div className="px-4 sm:px-6 lg:px-8 pt-3 sm:pt-4 pb-1">
          {/* Title & Description */}
          <div className="mb-3 pl-12 lg:pl-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              {title}
            </h1>
            {description && (
              <p className="text-xs sm:text-sm text-gray-600 mt-1">
                {description}
              </p>
            )}
          </div>

          {/* Search Bar + Actions Row */}
          {(searchBar || actions) && (
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              {/* Search Bar (left, limited width) */}
              {searchBar && (
                <div className="w-full sm:w-auto">
                  {searchBar}
                </div>
              )}

              {/* Actions (right, fixed width) - Hidden on mobile */}
              {actions && (
                <div className="hidden sm:flex flex-shrink-0 sm:ml-auto">
                  {actions}
                </div>
              )}
            </div>
          )}

        {/* Stats Row as Tabs (if provided) */}
        {stats && stats.length > 0 && (
          <div className="flex flex-nowrap overflow-x-auto gap-1 mt-2 border-b border-gray-200">
            {stats.map((stat, index) => {
              const isActive = activeFilter === stat.filterKey
              const isClickable = !!onStatClick && !!stat.filterKey

              if (!isClickable) return null // Skip non-clickable stats

              return (
                <button
                  key={index}
                  onClick={() => onStatClick(stat.filterKey)}
                  className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all whitespace-nowrap ${
                    isActive
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-transparent hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span className={`text-sm font-medium ${
                    isActive ? 'text-blue-700' : 'text-gray-600'
                  }`}>
                    {stat.label}
                  </span>
                  <span
                    className={`text-sm font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? 'bg-blue-200 text-blue-900'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {stat.value}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>

    {/* Floating Action Button - Mobile Only */}
    {actionHandler && (
      <button
        onClick={actionHandler}
        className="fixed bottom-6 right-6 sm:hidden z-[55] w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 active:bg-blue-800 transition-colors flex items-center justify-center"
        aria-label="Add"
      >
        <Plus className="w-6 h-6" />
      </button>
    )}
    </>
  )
}
