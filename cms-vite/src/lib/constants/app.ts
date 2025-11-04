/**
 * Application Constants
 * Centralized application-wide constants
 */

export const APP_NAME = 'Digital Signage CMS';
export const APP_VERSION = '1.0.0-phase2';

// File upload limits
export const MAX_FILE_SIZE_MB = 100;
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
export const ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/ogg'];

// Pagination
export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// Timeouts
export const API_TIMEOUT_MS = 30000;
export const TOKEN_REFRESH_THRESHOLD_MINUTES = 5;

// Device
export const ACTIVATION_CODE_LENGTH = 6;
export const DEVICE_HEARTBEAT_INTERVAL_SECONDS = 30;
export const DEVICE_ONLINE_THRESHOLD_MINUTES = 5;

// Date formats
export const DATE_FORMAT = 'DD/MM/YYYY';
export const DATETIME_FORMAT = 'DD/MM/YYYY HH:mm';
export const TIME_FORMAT = 'HH:mm';

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  USER: 'auth_user',
  THEME: 'app_theme',
  LANGUAGE: 'app_language',
} as const;

// Roles
export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  VIEWER: 'viewer',
} as const;

// Device types
export const DEVICE_TYPES = {
  TV: 'tv',
  MONITOR: 'monitor',
} as const;

// Content types
export const CONTENT_TYPES = {
  IMAGE: 'image',
  VIDEO: 'video',
  URL: 'url',
  WIDGET: 'widget',
} as const;
