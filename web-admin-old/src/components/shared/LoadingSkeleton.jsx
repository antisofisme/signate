/**
 * LoadingSkeleton Component
 * Reusable loading skeleton with multiple variants for different UI patterns
 *
 * Features:
 * - Multiple variants: card, table, stats, grid, grid-playlist, grid-content, list, pending-approvals
 * - Animated pulse effect with smooth transitions
 * - Customizable count for repeating skeletons
 * - Responsive and accessible
 * - Fade-in animation support
 *
 * Variants:
 * - stats: Dashboard stat cards (icon + value + subtitle)
 * - grid-playlist: Playlist cards (icon + title + stats + action buttons)
 * - grid-content: Content cards (thumbnail + metadata + tags + action buttons)
 * - grid: Generic grid items (simple thumbnail + text)
 * - table: Table rows with columns
 * - list: List items with avatar + text
 * - pending-approvals: Special pending device cards
 * - card: Generic card skeleton
 * - custom: Custom placeholder
 *
 * @param {string} variant - Type of skeleton
 * @param {number} count - Number of skeleton items to render (default: 1)
 * @param {string} className - Additional classes for customization
 */
export default function LoadingSkeleton({ variant = 'card', count = 1, className = '' }) {
  const renderSkeleton = () => {
    switch (variant) {
      case 'stats':
        return (
          <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 p-4 hover:shadow-xl transition-shadow ${className}`}>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-10 w-16 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mt-2"></div>
                <div className="h-3 w-1/2 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mt-1"></div>
              </div>
              <div className="p-3 rounded-full bg-gray-200 dark:bg-gray-600">
                <div className="w-6 h-6 bg-gray-300 dark:bg-gray-500 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        )

      case 'card':
        return (
          <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
            <div className="h-40 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse mb-4"></div>
            <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
            <div className="h-3 w-1/2 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-3"></div>
            <div className="flex gap-2">
              <div className="h-6 w-16 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
              <div className="h-6 w-16 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
            </div>
          </div>
        )

      case 'table':
        return (
          <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
            {/* Table Header */}
            <div className="bg-gray-50 dark:bg-gray-900 border-b px-6 py-4">
              <div className="flex gap-4">
                <div className="h-4 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-4 w-24 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-4 w-40 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-4 w-28 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
              </div>
            </div>
            {/* Table Rows */}
            {Array.from({ length: count }).map((_, idx) => (
              <div key={idx} className="border-b border-gray-200 dark:border-gray-700 px-6 py-4 last:border-b-0">
                <div className="flex gap-4 items-center">
                  <div className="h-10 w-10 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                  <div className="flex-1">
                    <div className="h-4 w-48 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                    <div className="h-3 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                  </div>
                  <div className="h-8 w-20 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'grid':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
            <div className="h-32 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse mb-3"></div>
            <div className="h-4 w-full bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
            <div className="h-3 w-2/3 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
          </div>
        ))

      case 'grid-playlist':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 overflow-hidden ${className}`}>
            {/* Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-12 h-12 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                <div className="flex-1">
                  <div className="h-5 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                  <div className="h-4 w-20 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                </div>
              </div>
              <div className="h-3 w-full bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
            </div>
            {/* Stats */}
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="h-3 w-16 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                  <div className="h-4 w-12 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                </div>
                <div>
                  <div className="h-3 w-16 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                  <div className="h-6 w-16 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
            {/* Actions */}
            <div className="px-6 py-4 space-y-2">
              <div className="flex gap-2">
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
              </div>
              <div className="flex gap-2">
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                <div className="h-8 w-8 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
              </div>
            </div>
          </div>
        ))

      case 'grid-content':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-600 overflow-hidden ${className}`}>
            {/* Thumbnail - aspect ratio 16:9 */}
            <div className="relative aspect-video bg-gray-200 dark:bg-gray-600 animate-pulse">
              <div className="absolute top-2 left-2 w-5 h-5 bg-gray-300 dark:bg-gray-500 rounded animate-pulse"></div>
              <div className="absolute top-2 right-2 space-y-1">
                <div className="h-5 w-14 bg-gray-300 dark:bg-gray-500 rounded-full animate-pulse"></div>
                <div className="h-5 w-10 bg-gray-300 dark:bg-gray-500 rounded-full animate-pulse"></div>
              </div>
            </div>
            {/* Content */}
            <div className="p-3">
              {/* Title */}
              <div className="h-4 w-full bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
              {/* Metadata - 4 items */}
              <div className="space-y-1 mb-2">
                <div className="h-3 w-24 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-3 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-3 w-20 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                <div className="h-3 w-16 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
              </div>
              {/* Tags */}
              <div className="flex gap-1 mb-3">
                <div className="h-5 w-12 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
                <div className="h-5 w-16 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
              </div>
              {/* Action Buttons */}
              <div className="flex gap-2">
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
                <div className="h-8 flex-1 bg-gray-200 dark:bg-gray-600 rounded-lg animate-pulse"></div>
              </div>
            </div>
          </div>
        ))

      case 'list':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-3 ${className}`}>
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
              <div className="flex-1">
                <div className="h-4 w-48 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                <div className="h-3 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
              </div>
              <div className="h-8 w-24 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
            </div>
          </div>
        ))

      case 'pending-approvals':
        return (
          <div className={`bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200 dark:border-yellow-700 rounded-xl p-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-yellow-300 dark:bg-yellow-500 rounded-full animate-pulse"></div>
                <div className="h-6 w-48 bg-yellow-200 dark:bg-yellow-700 rounded animate-pulse"></div>
              </div>
              <div className="h-9 w-24 bg-yellow-200 dark:bg-yellow-700 rounded-lg animate-pulse"></div>
            </div>
            {/* Device Cards */}
            <div className="grid gap-3">
              {Array.from({ length: count }).map((_, idx) => (
                <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 bg-gray-200 dark:bg-gray-600 rounded-full animate-pulse"></div>
                    <div>
                      <div className="h-4 w-32 bg-gray-200 dark:bg-gray-600 rounded animate-pulse mb-2"></div>
                      <div className="h-3 w-48 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <div className="h-8 w-20 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                    <div className="h-8 w-20 bg-gray-200 dark:bg-gray-600 rounded animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      case 'custom':
        return (
          <div className={`bg-gray-200 rounded animate-pulse ${className}`}></div>
        )

      default:
        return (
          <div className={`h-40 bg-gray-200 rounded-lg animate-pulse ${className}`}></div>
        )
    }
  }

  // For stats variant, render multiple stats cards (no wrapper, parent handles grid)
  if (variant === 'stats') {
    return (
      <>
        {Array.from({ length: count }).map((_, idx) => (
          <div key={idx}>{renderSkeleton()}</div>
        ))}
      </>
    )
  }

  // For table variant, render single table with multiple rows
  if (variant === 'table') {
    return renderSkeleton()
  }

  // For grid variants and list, already handled inside renderSkeleton
  if (variant === 'grid' || variant === 'grid-playlist' || variant === 'grid-content' || variant === 'list') {
    return <>{renderSkeleton()}</>
  }

  // For other variants, render count times
  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <div key={idx}>{renderSkeleton()}</div>
      ))}
    </>
  )
}
