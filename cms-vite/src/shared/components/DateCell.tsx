/**
 * DateCell Component
 * Displays relative time with absolute date in tooltip
 *
 * Usage:
 * <DateCell date={item.created_at} />
 * <DateCell date={item.uploaded_at} emptyText="Not uploaded" />
 */

import { formatRelativeTimeCompact, formatAbsoluteDate } from '../utils/formatters';

interface DateCellProps {
  /** ISO datetime string */
  date: string | undefined | null;
  /** Custom text when date is empty */
  emptyText?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * DateCell - Shows relative time with absolute date tooltip
 * @example
 * // Shows "2h ago" with tooltip "Dec 5, 2024 14:30"
 * <DateCell date="2024-12-05T14:30:00Z" />
 */
export function DateCell({ date, emptyText = '-', className = '' }: DateCellProps) {
  if (!date) {
    return <span className={`text-gray-400 dark:text-gray-500 ${className}`}>{emptyText}</span>;
  }

  const relativeTime = formatRelativeTimeCompact(date);
  const absoluteDate = formatAbsoluteDate(date);

  return (
    <span
      title={absoluteDate}
      className={`cursor-help text-gray-600 dark:text-gray-400 ${className}`}
    >
      {relativeTime}
    </span>
  );
}

/**
 * OnlineStatusCell - Shows online/offline status with duration
 * Used specifically for device last_seen display
 */
interface OnlineStatusCellProps {
  /** ISO datetime string of last seen */
  lastSeen: string | undefined | null;
  /** Whether device is currently online */
  isOnline?: boolean;
  /** Threshold in minutes for warning (default: 60) */
  warningThreshold?: number;
  /** Threshold in minutes for danger (default: 1440 = 24h) */
  dangerThreshold?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * OnlineStatusCell - Shows online duration or offline time with color coding
 * @example
 * // Online: "Online 2h" (green)
 * // Offline <1h: "Offline 45m" (yellow)
 * // Offline >24h: "Offline 3d" (red)
 * <OnlineStatusCell lastSeen="2024-12-05T14:30:00Z" isOnline={true} />
 */
export function OnlineStatusCell({
  lastSeen,
  isOnline = false,
  warningThreshold = 60,
  dangerThreshold = 1440,
  className = '',
}: OnlineStatusCellProps) {
  if (!lastSeen) {
    return <span className={`text-gray-400 dark:text-gray-500 ${className}`}>-</span>;
  }

  const now = new Date();
  const lastSeenDate = new Date(lastSeen);
  const diffMinutes = Math.floor((now.getTime() - lastSeenDate.getTime()) / 60000);

  // Format duration
  let durationText: string;
  if (diffMinutes < 1) {
    durationText = 'just now';
  } else if (diffMinutes < 60) {
    durationText = `${diffMinutes}m`;
  } else if (diffMinutes < 1440) { // 24 hours
    durationText = `${Math.floor(diffMinutes / 60)}h`;
  } else if (diffMinutes < 10080) { // 7 days
    durationText = `${Math.floor(diffMinutes / 1440)}d`;
  } else {
    durationText = `${Math.floor(diffMinutes / 10080)}w`;
  }

  // Determine color based on status and duration
  let colorClass: string;
  let statusText: string;

  if (isOnline) {
    colorClass = 'text-green-600 dark:text-green-400';
    statusText = `Online ${durationText}`;
  } else {
    if (diffMinutes < warningThreshold) {
      colorClass = 'text-yellow-600 dark:text-yellow-400';
    } else if (diffMinutes < dangerThreshold) {
      colorClass = 'text-orange-600 dark:text-orange-400';
    } else {
      colorClass = 'text-red-600 dark:text-red-400';
    }
    statusText = `Offline ${durationText}`;
  }

  const absoluteDate = formatAbsoluteDate(lastSeen);

  return (
    <span
      title={`Last seen: ${absoluteDate}`}
      className={`cursor-help font-medium ${colorClass} ${className}`}
    >
      {statusText}
    </span>
  );
}

export default DateCell;
