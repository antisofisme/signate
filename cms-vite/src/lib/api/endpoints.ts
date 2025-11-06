/**
 * API Endpoints - Single Source of Truth
 *
 * ⚠️ CENTRALIZED - All API routes defined here
 *
 * Usage:
 *   import { API_ENDPOINTS } from '@/lib/api/endpoints';
 *   apiClient.get(API_ENDPOINTS.DEVICES.LIST)
 */

export const API_ENDPOINTS = {
  // ========================================
  // AUTH
  // ========================================
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
    REFRESH: '/auth/refresh',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
  },

  // ========================================
  // ORGANIZATIONS
  // ========================================
  ORGANIZATIONS: {
    LIST: '/organizations',
    GET: (id: number) => `/organizations/${id}`,
    CREATE: '/organizations',
    UPDATE: (id: number) => `/organizations/${id}`,
    DELETE: (id: number) => `/organizations/${id}`,
    VALIDATE_PIN: (id: number) => `/organizations/${id}/validate-pin`,
  },

  // ========================================
  // DEVICES
  // ========================================
  DEVICES: {
    LIST: '/devices',
    GET: (id: number) => `/devices/${id}`,
    TV_REGISTER: '/devices/tv/register',
    MONITOR_REGISTER: '/devices/monitor/register',
    ACTIVATE: '/devices/activate',
    UPDATE: (id: number) => `/devices/${id}`,
    DELETE: (id: number) => `/devices/${id}`,
    HEARTBEAT: '/devices/heartbeat',
    CHECK_ACTIVATION: (code: string) => `/devices/check-activation/${code}`,
    LOGS: (id: number) => `/devices/${id}/logs`,
    COMMANDS: (id: number) => `/devices/${id}/commands`,
    SEND_COMMAND: (id: number) => `/devices/${id}/commands`,
  },

  // ========================================
  // CONTENT
  // ========================================
  CONTENT: {
    LIST: '/contents',
    GET: (id: number) => `/contents/${id}`,
    UPLOAD: '/contents/upload',
    BULK_UPLOAD: '/contents/bulk-upload',
    UPDATE: (id: number) => `/contents/${id}`,
    DELETE: (id: number) => `/contents/${id}`,
    BULK_DELETE: '/contents/bulk-delete',
    BULK_UPDATE: '/contents/bulk-update',
    STATS: '/contents/stats',
  },

  // ========================================
  // PLAYLISTS
  // ========================================
  PLAYLISTS: {
    LIST: '/playlists',
    GET: (id: number) => `/playlists/${id}`,
    CREATE: '/playlists',
    UPDATE: (id: number) => `/playlists/${id}`,
    DELETE: (id: number) => `/playlists/${id}`,
    DUPLICATE: (id: number) => `/playlists/${id}/duplicate`,
    ASSIGN_DEVICE: (id: number) => `/playlists/${id}/assign`,
    UNASSIGN_DEVICE: (id: number) => `/playlists/${id}/unassign`,
    REORDER: (id: number) => `/playlists/${id}/reorder`,
  },

  // ========================================
  // USERS
  // ========================================
  USERS: {
    LIST: '/users',
    GET: (id: number) => `/users/${id}`,
    CREATE: '/users',
    UPDATE: (id: number) => `/users/${id}`,
    DELETE: (id: number) => `/users/${id}`,
    CHANGE_PASSWORD: (id: number) => `/users/${id}/change-password`,
  },

  // ========================================
  // AUDIT LOGS
  // ========================================
  AUDIT: {
    LIST: '/audit-logs',
    GET: (id: number) => `/audit-logs/${id}`,
  },

  // ========================================
  // TAGS
  // ========================================
  TAGS: {
    LIST: '/tags',
    GET: (id: number) => `/tags/${id}`,
    CREATE: '/tags',
    UPDATE: (id: number) => `/tags/${id}`,
    DELETE: (id: number) => `/tags/${id}`,
    USAGE: (id: number) => `/tags/${id}/usage`,
  },

  // ========================================
  // ANALYTICS
  // ========================================
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard',
    DEVICE_STATS: '/analytics/devices/stats',
    CONTENT_STATS: '/analytics/content/stats',
    DEVICE_LOGS: (deviceId: number) => `/analytics/devices/${deviceId}/logs`,
    ACTIVITY_TIMELINE: '/analytics/activity',
  },

  // ========================================
  // PREVIEW
  // ========================================
  PREVIEW: {
    DEVICE: (deviceId: number) => `/preview/device/${deviceId}`,
    PLAYLIST: (playlistId: number) => `/preview/playlist/${playlistId}`,
  },
} as const;
