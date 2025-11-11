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
