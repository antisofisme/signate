/**
 * Utility functions for formatting dates, times, and other data
 */

/**
 * Format ISO date string to readable date
 * @param dateString ISO date string
 * @returns Formatted date (e.g., "2025-01-11")
 */
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toISOString().split('T')[0]
  } catch {
    return dateString
  }
}

/**
 * Format ISO time string to readable time
 * @param timeString Time string (HH:mm:ss)
 * @returns Formatted time (e.g., "14:30")
 */
export const formatTime = (timeString: string): string => {
  try {
    if (timeString.includes('T')) {
      const date = new Date(timeString)
      return date.toTimeString().substring(0, 5)
    }
    return timeString.substring(0, 5)
  } catch {
    return timeString
  }
}

/**
 * Format ISO datetime string to readable datetime
 * @param datetimeString ISO datetime string
 * @returns Formatted datetime (e.g., "Jan 11, 2025 2:30 PM")
 */
export const formatDateTime = (datetimeString: string): string => {
  try {
    const date = new Date(datetimeString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return datetimeString
  }
}

/**
 * Format ISO datetime string to relative time
 * @param datetimeString ISO datetime string
 * @returns Relative time (e.g., "2 hours ago", "just now")
 */
export const formatRelativeTime = (datetimeString: string): string => {
  try {
    const date = new Date(datetimeString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
    return formatDateTime(datetimeString)
  } catch {
    return datetimeString
  }
}

/**
 * Format ISO datetime string to compact relative time (for table columns)
 * @param datetimeString ISO datetime string
 * @returns Compact relative time (e.g., "2h", "3d", "1w", "just now")
 */
export const formatRelativeTimeCompact = (datetimeString: string | undefined | null): string => {
  if (!datetimeString) return '-'
  try {
    const date = new Date(datetimeString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 0) return 'just now' // Future date
    if (seconds < 60) return 'just now'
    if (seconds < 3600) {
      const mins = Math.floor(seconds / 60)
      return `${mins}m ago`
    }
    if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600)
      return `${hours}h ago`
    }
    if (seconds < 604800) {
      const days = Math.floor(seconds / 86400)
      return `${days}d ago`
    }
    if (seconds < 2592000) { // 30 days
      const weeks = Math.floor(seconds / 604800)
      return `${weeks}w ago`
    }
    if (seconds < 31536000) { // 365 days
      const months = Math.floor(seconds / 2592000)
      return `${months}mo ago`
    }
    const years = Math.floor(seconds / 31536000)
    return `${years}y ago`
  } catch {
    return '-'
  }
}

/**
 * Format ISO datetime string to absolute date for tooltips
 * @param datetimeString ISO datetime string
 * @returns Formatted date (e.g., "Dec 5, 2024 14:30")
 */
export const formatAbsoluteDate = (datetimeString: string | undefined | null): string => {
  if (!datetimeString) return '-'
  try {
    const date = new Date(datetimeString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } catch {
    return '-'
  }
}

/**
 * Get date display props for components (relative time with tooltip)
 * @param datetimeString ISO datetime string
 * @returns Object with text (relative) and tooltip (absolute)
 */
export const getDateDisplayProps = (datetimeString: string | undefined | null): { text: string; tooltip: string } => {
  return {
    text: formatRelativeTimeCompact(datetimeString),
    tooltip: formatAbsoluteDate(datetimeString)
  }
}

/**
 * Format bytes to human readable size
 * @param bytes Number of bytes
 * @returns Formatted size (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format number with thousand separators
 * @param num Number to format
 * @returns Formatted number (e.g., "1,000,000")
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString('en-US')
}

/**
 * Format duration in seconds to readable format
 * @param seconds Duration in seconds
 * @returns Formatted duration (e.g., "1:30:45")
 */
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}
