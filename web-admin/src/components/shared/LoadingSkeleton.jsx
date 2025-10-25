/**
 * LoadingSkeleton Component
 * Reusable loading skeleton with multiple variants for different UI patterns
 *
 * Features:
 * - Multiple variants: card, table, stats, grid, list
 * - Animated pulse effect
 * - Customizable count for repeating skeletons
 * - Responsive and accessible
 *
 * @param {string} variant - Type of skeleton (card, table, stats, grid, list, custom)
 * @param {number} count - Number of skeleton items to render (default: 1)
 * @param {string} className - Additional classes for customization
 */
export default function LoadingSkeleton({ variant = 'card', count = 1, className = '' }) {
  const renderSkeleton = () => {
    switch (variant) {
      case 'stats':
        return (
          <div className={`bg-white rounded-lg border p-6 ${className}`}>
            <div className="flex items-center justify-between mb-4">
              <div className="h-10 w-10 bg-gray-200 rounded-lg animate-pulse"></div>
              <div className="h-8 w-20 bg-gray-200 rounded animate-pulse"></div>
            </div>
            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
            <div className="h-3 w-48 bg-gray-200 rounded animate-pulse"></div>
          </div>
        )

      case 'card':
        return (
          <div className={`bg-white rounded-lg border p-4 ${className}`}>
            <div className="h-40 bg-gray-200 rounded-lg animate-pulse mb-4"></div>
            <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse mb-2"></div>
            <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse mb-3"></div>
            <div className="flex gap-2">
              <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse"></div>
            </div>
          </div>
        )

      case 'table':
        return (
          <div className={`bg-white rounded-lg border overflow-hidden ${className}`}>
            {/* Table Header */}
            <div className="bg-gray-50 border-b px-6 py-4">
              <div className="flex gap-4">
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 w-40 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 w-28 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
            {/* Table Rows */}
            {Array.from({ length: count }).map((_, idx) => (
              <div key={idx} className="border-b px-6 py-4 last:border-b-0">
                <div className="flex gap-4 items-center">
                  <div className="h-10 w-10 bg-gray-200 rounded animate-pulse"></div>
                  <div className="flex-1">
                    <div className="h-4 w-48 bg-gray-200 rounded animate-pulse mb-2"></div>
                    <div className="h-3 w-32 bg-gray-200 rounded animate-pulse"></div>
                  </div>
                  <div className="h-8 w-20 bg-gray-200 rounded-full animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'grid':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white rounded-lg border p-4 ${className}`}>
            <div className="h-32 bg-gray-200 rounded-lg animate-pulse mb-3"></div>
            <div className="h-4 w-full bg-gray-200 rounded animate-pulse mb-2"></div>
            <div className="h-3 w-2/3 bg-gray-200 rounded animate-pulse"></div>
          </div>
        ))

      case 'list':
        return Array.from({ length: count }).map((_, idx) => (
          <div key={idx} className={`bg-white rounded-lg border p-4 mb-3 ${className}`}>
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="flex-1">
                <div className="h-4 w-48 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-3 w-32 bg-gray-200 rounded animate-pulse"></div>
              </div>
              <div className="h-8 w-24 bg-gray-200 rounded animate-pulse"></div>
            </div>
          </div>
        ))

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

  // For stats variant, render multiple stats cards
  if (variant === 'stats') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: count }).map((_, idx) => (
          <div key={idx}>{renderSkeleton()}</div>
        ))}
      </div>
    )
  }

  // For table variant, render single table with multiple rows
  if (variant === 'table') {
    return renderSkeleton()
  }

  // For grid and list, already handled inside renderSkeleton
  if (variant === 'grid' || variant === 'list') {
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
