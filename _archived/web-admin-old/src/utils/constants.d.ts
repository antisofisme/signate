/**
 * Type declarations for constants.js
 */

export const API_BASE_URL: string

export const CONTENT_TYPES: {
  readonly IMAGE: 'image'
  readonly VIDEO: 'video'
}

export const DEVICE_TYPES: {
  readonly TV: 'tv'
  readonly MONITOR: 'monitor'
}

export const DEVICE_STATUS: {
  readonly PENDING: 'pending'
  readonly ACTIVE: 'active'
  readonly INACTIVE: 'inactive'
}

export const DEVICE_STATUS_LABELS: {
  readonly [key: string]: string
}

export const DEVICE_STATUS_COLORS: {
  readonly [key: string]: string
}

export const FILE_LIMITS: {
  readonly MAX_SIZE_MB: number
  readonly MAX_SIZE_BYTES: number
  readonly ALLOWED_IMAGE_TYPES: readonly string[]
  readonly ALLOWED_VIDEO_TYPES: readonly string[]
}

export const PAGINATION: {
  readonly DEFAULT_PAGE_SIZE: number
  readonly PAGE_SIZE_OPTIONS: readonly number[]
}

export const DURATION_LIMITS: {
  readonly MIN: number
  readonly MAX: number
  readonly DEFAULT: number
}

export const ROUTES: {
  readonly HOME: string
  readonly DASHBOARD: string
  readonly CONTENT: string
  readonly DEVICES: string
  readonly TAGS: string
  readonly LOGIN: string
}

export const QUERY_KEYS: {
  readonly CONTENT: string
  readonly CONTENT_DETAIL: string
  readonly DEVICES: string
  readonly DEVICE_DETAIL: string
  readonly TAGS: string
  readonly TAG_DETAIL: string
  readonly ASSIGNMENTS: string
}

export const TOAST_MESSAGES: {
  readonly CONTENT_CREATED: string
  readonly CONTENT_UPDATED: string
  readonly CONTENT_DELETED: string
  readonly CONTENT_ASSIGNED: string
  readonly DEVICE_CREATED: string
  readonly DEVICE_UPDATED: string
  readonly DEVICE_DELETED: string
  readonly DEVICE_APPROVED: string
  readonly TAG_CREATED: string
  readonly TAG_UPDATED: string
  readonly TAG_DELETED: string
  readonly ERROR_GENERIC: string
  readonly ERROR_UPLOAD: string
  readonly ERROR_NETWORK: string
}

export const DATE_FORMATS: {
  readonly FULL: string
  readonly DATE_ONLY: string
  readonly TIME_ONLY: string
}
