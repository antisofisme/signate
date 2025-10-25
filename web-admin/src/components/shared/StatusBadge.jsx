import { memo } from 'react'
import { statusColors } from '../../styles/tokens'

/**
 * StatusBadge Component
 * Reusable status badge component with consistent styling across the application
 *
 * Features:
 * - Uses design token statusColors for consistency
 * - Multiple status variants (active, pending, inactive, online, offline, error)
 * - Multiple size variants (sm, md, lg)
 * - Optional dot indicator
 * - Optional icon
 * - Rounded pill shape
 *
 * @param {string} status - Status type: 'active' | 'pending' | 'inactive' | 'online' | 'offline' | 'error'
 * @param {string} size - Size variant: 'sm' | 'md' | 'lg' (default: 'md')
 * @param {boolean} showDot - Show status dot indicator (default: false)
 * @param {string} label - Optional custom label (overrides default status label)
 * @param {string} icon - Optional icon/emoji to display
 * @param {string} className - Additional CSS classes
 */
const StatusBadge = memo(function StatusBadge({
  status,
  size = 'md',
  showDot = false,
  label,
  icon,
  className = ''
}) {
  // Get status colors from design tokens
  const colors = statusColors[status] || statusColors.inactive

  // Default labels for each status
  const defaultLabels = {
    active: 'Active',
    pending: 'Pending',
    inactive: 'Inactive',
    online: 'Online',
    offline: 'Offline',
    error: 'Error',
  }

  // Size variants
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',      // Small - for compact layouts
    md: 'text-xs px-2 py-1',        // Medium - default size
    lg: 'text-sm px-3 py-1.5',      // Large - for prominent displays
  }

  // Dot size variants
  const dotSizeClasses = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  }

  const displayLabel = label || defaultLabels[status] || status

  return (
    <div
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium
        ${colors.bg} ${colors.text}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {/* Optional dot indicator */}
      {showDot && (
        <span
          className={`
            rounded-full ${colors.dot}
            ${dotSizeClasses[size]}
          `}
        />
      )}

      {/* Optional icon */}
      {icon && <span>{icon}</span>}

      {/* Label */}
      <span>{displayLabel}</span>
    </div>
  )
})

export default StatusBadge
