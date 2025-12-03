/**
 * StatusBadge Component
 *
 * Unified badge for displaying status indicators with consistent styling
 *
 * Features:
 * - Multiple status variants with semantic colors
 * - Optional icon support
 * - Optional progress indicator
 * - Size variants
 * - Dark mode support
 *
 * @usage
 * <StatusBadge status="processing" label="Transcoding" progress={45} />
 * <StatusBadge status="success" label="Completed" icon={<Check />} />
 */

import { memo, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

type BadgeStatus =
  | 'pending'
  | 'processing'
  | 'failed'
  | 'completed'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'default';

type BadgeSize = 'xs' | 'sm' | 'md';

interface StatusBadgeProps {
  /** Status type determining color scheme */
  status: BadgeStatus;
  /** Text label to display */
  label?: string;
  /** Optional icon (replaces default status icon) */
  icon?: ReactNode;
  /** Show default spinning loader for processing status */
  showLoader?: boolean;
  /** Progress percentage (0-100) - shows when processing */
  progress?: number;
  /** Size variant */
  size?: BadgeSize;
  /** Additional className */
  className?: string;
}

// Status color mappings
const STATUS_STYLES: Record<BadgeStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

// Alternative solid styles for higher visibility
const STATUS_SOLID_STYLES: Record<BadgeStatus, string> = {
  pending: 'bg-yellow-500/80 text-white',
  processing: 'bg-blue-500/80 text-white',
  failed: 'bg-red-500/80 text-white',
  completed: 'bg-green-500/80 text-white',
  success: 'bg-green-500/80 text-white',
  warning: 'bg-orange-500/80 text-white',
  error: 'bg-red-500/80 text-white',
  info: 'bg-blue-500/80 text-white',
  default: 'bg-gray-500/80 text-white',
};

// Size mappings
const SIZE_STYLES: Record<BadgeSize, string> = {
  xs: 'px-1.5 py-0.5 text-xs gap-1',
  sm: 'px-2 py-0.5 text-xs gap-1',
  md: 'px-2.5 py-1 text-sm gap-1.5',
};

const ICON_SIZES: Record<BadgeSize, string> = {
  xs: 'w-2.5 h-2.5',
  sm: 'w-3 h-3',
  md: 'w-3.5 h-3.5',
};

const StatusBadge = memo<StatusBadgeProps>(function StatusBadge({
  status,
  label,
  icon,
  showLoader = true,
  progress,
  size = 'sm',
  className = '',
}) {
  // Determine if we should show the spinner
  const isProcessing = status === 'processing' && showLoader;
  const hasProgress = typeof progress === 'number' && status === 'processing';

  // Format progress text
  const progressText = hasProgress ? `${Math.round(progress)}%` : null;

  // Display label
  const displayLabel = progressText || label;

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded',
        SIZE_STYLES[size],
        STATUS_STYLES[status],
        className
      )}
    >
      {/* Icon or Loader */}
      {isProcessing ? (
        <Loader2 className={cn(ICON_SIZES[size], 'animate-spin')} aria-hidden="true" />
      ) : icon ? (
        <span className={cn('inline-flex', ICON_SIZES[size])}>{icon}</span>
      ) : null}

      {/* Label */}
      {displayLabel && <span>{displayLabel}</span>}
    </span>
  );
});

// Solid variant export
export const StatusBadgeSolid = memo<StatusBadgeProps>(function StatusBadgeSolid({
  status,
  label,
  icon,
  showLoader = true,
  progress,
  size = 'sm',
  className = '',
}) {
  const isProcessing = status === 'processing' && showLoader;
  const hasProgress = typeof progress === 'number' && status === 'processing';
  const progressText = hasProgress ? `${Math.round(progress)}%` : null;
  const displayLabel = progressText || label;

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded',
        SIZE_STYLES[size],
        STATUS_SOLID_STYLES[status],
        className
      )}
    >
      {isProcessing ? (
        <Loader2 className={cn(ICON_SIZES[size], 'animate-spin')} aria-hidden="true" />
      ) : icon ? (
        <span className={cn('inline-flex', ICON_SIZES[size])}>{icon}</span>
      ) : null}
      {displayLabel && <span>{displayLabel}</span>}
    </span>
  );
});

export default StatusBadge;
export type { StatusBadgeProps, BadgeStatus, BadgeSize };
