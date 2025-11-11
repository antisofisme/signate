/**
 * Application Constants
 * Centralized constants for the application
 */

// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'

// Content Types
export const CONTENT_TYPES = {
  IMAGE: 'image',
  VIDEO: 'video'
}

// Device Types
export const DEVICE_TYPES = {
  TV: 'tv',
  MONITOR: 'monitor'
}

// Device Status
export const DEVICE_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  INACTIVE: 'inactive'
}

// Device Status Labels
export const DEVICE_STATUS_LABELS = {
  [DEVICE_STATUS.PENDING]: 'Pending',
  [DEVICE_STATUS.ACTIVE]: 'Active',
  [DEVICE_STATUS.INACTIVE]: 'Inactive'
}

// Device Status Colors (for badges)
export const DEVICE_STATUS_COLORS = {
  [DEVICE_STATUS.PENDING]: 'warning',
  [DEVICE_STATUS.ACTIVE]: 'success',
  [DEVICE_STATUS.INACTIVE]: 'default'
}

// File Upload Limits
export const FILE_LIMITS = {
  MAX_SIZE_MB: 100,
  MAX_SIZE_BYTES: 100 * 1024 * 1024,
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_VIDEO_TYPES: ['video/mp4', 'video/webm', 'video/quicktime']
}

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100]
}

// Duration Limits (seconds)
export const DURATION_LIMITS = {
  MIN: 1,
  MAX: 300,
  DEFAULT: 10
}

// Routes
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  CONTENT: '/content',
  DEVICES: '/devices',
  TAGS: '/tags',
  LOGIN: '/login'
}

// Query Keys (React Query)
export const QUERY_KEYS = {
  CONTENT: 'content',
  CONTENT_DETAIL: 'content-detail',
  DEVICES: 'devices',
  DEVICE_DETAIL: 'device-detail',
  TAGS: 'tags',
  TAG_DETAIL: 'tag-detail',
  ASSIGNMENTS: 'assignments'
}

// Toast Messages
export const TOAST_MESSAGES = {
  // Content
  CONTENT_CREATED: 'Content uploaded successfully',
  CONTENT_UPDATED: 'Content updated successfully',
  CONTENT_DELETED: 'Content deleted successfully',
  CONTENT_ASSIGNED: 'Content assigned successfully',

  // Device
  DEVICE_CREATED: 'Device registered successfully',
  DEVICE_UPDATED: 'Device updated successfully',
  DEVICE_DELETED: 'Device deleted successfully',
  DEVICE_APPROVED: 'Device approved successfully',

  // Tag
  TAG_CREATED: 'Tag created successfully',
  TAG_UPDATED: 'Tag updated successfully',
  TAG_DELETED: 'Tag deleted successfully',

  // Errors
  ERROR_GENERIC: 'An error occurred. Please try again.',
  ERROR_UPLOAD: 'Failed to upload file',
  ERROR_NETWORK: 'Network error. Please check your connection.'
}

// Date Formats
export const DATE_FORMATS = {
  FULL: 'YYYY-MM-DD HH:mm:ss',
  DATE_ONLY: 'YYYY-MM-DD',
  TIME_ONLY: 'HH:mm:ss'
}
