/**
 * API Endpoints - Single Source of Truth
 *
 * ⚠️ CENTRALIZED - All API routes defined here
 * ⚠️ All endpoints include full path with /api/v1 prefix
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
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    ME: '/api/v1/auth/me',
    REFRESH: '/api/v1/auth/refresh',
    FORGOT_PASSWORD: '/api/v1/auth/forgot-password',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
  },

  // ========================================
  // ORGANIZATIONS
  // ========================================
  ORGANIZATIONS: {
    LIST: '/api/v1/organizations',
    GET: (id: number) => `/api/v1/organizations/${id}`,
    CREATE: '/api/v1/organizations',
    UPDATE: (id: number) => `/api/v1/organizations/${id}`,
    DELETE: (id: number) => `/api/v1/organizations/${id}`,
    VALIDATE_PIN: (id: number) => `/api/v1/organizations/${id}/validate-pin`,
  },

  // ========================================
  // DEVICES
  // ========================================
  DEVICES: {
    LIST: '/api/v1/devices',
    GET: (id: number) => `/api/v1/devices/${id}`,
    TV_REGISTER: '/api/v1/devices/tv',
    MONITOR_REGISTER: '/api/v1/devices/monitor',
    ACTIVATE: '/api/v1/devices/activate',
    UPDATE: (id: number) => `/api/v1/devices/${id}`,
    DELETE: (id: number) => `/api/v1/devices/${id}`,
    HEARTBEAT: (id: number) => `/api/v1/devices/${id}/heartbeat`,
    CHECK_ACTIVATION: (code: string) => `/api/v1/devices/check-activation/${code}`,
    LOGS: (id: number) => `/api/v1/devices/${id}/logs`,
    COMMANDS: (id: number) => `/api/v1/devices/${id}/commands`,
    SEND_COMMAND: (id: number) => `/api/v1/devices/${id}/commands`,
    CONTENT_RESOLVED: (id: number) => `/api/v1/devices/${id}/content/resolved`,
    RELEASE: (id: number) => `/api/v1/devices/${id}/release`,
    SPEED_TEST: (id: number) => `/api/v1/devices/${id}/speed-test`,
    SPEED_TESTS: (id: number) => `/api/v1/devices/${id}/speed-tests`,

    // Device Groups
    GROUPS: {
      LIST: '/api/v1/devices/groups',
      ROOTS: '/api/v1/devices/groups/roots',
      GET: (id: number) => `/api/v1/devices/groups/${id}`,
      CHILDREN: (id: number) => `/api/v1/devices/groups/${id}/children`,
      DEVICES: (id: number) => `/api/v1/devices/groups/${id}/devices`,
      STATS: (id: number) => `/api/v1/devices/groups/${id}/stats`,
      CREATE: '/api/v1/devices/groups',
      UPDATE: (id: number) => `/api/v1/devices/groups/${id}`,
      DELETE: (id: number) => `/api/v1/devices/groups/${id}`,
      ADD_DEVICE: (groupId: number) => `/api/v1/devices/groups/${groupId}/devices`,
      REMOVE_DEVICE: (groupId: number, deviceId: number) => `/api/v1/devices/groups/${groupId}/devices/${deviceId}`,
    },
  },

  // ========================================
  // CONTENT
  // ========================================
  CONTENT: {
    LIST: '/api/v1/contents',
    GET: (id: number) => `/api/v1/contents/${id}`,
    UPLOAD: '/api/v1/contents/upload',
    BULK_UPLOAD: '/api/v1/contents/bulk-upload',
    UPDATE: (id: number) => `/api/v1/contents/${id}`,
    DELETE: (id: number) => `/api/v1/contents/${id}`,
    DOWNLOAD: (id: number) => `/api/v1/contents/${id}/download`,
    BULK_DELETE: '/api/v1/contents/bulk-delete',
    BULK_UPDATE: '/api/v1/contents/bulk-update',
    STATS: '/api/v1/contents/stats',
  },

  // ========================================
  // TAGS
  // ========================================
  TAGS: {
    LIST: '/api/v1/tags',
    GET: (id: number) => `/api/v1/tags/${id}`,
    CREATE: '/api/v1/tags',
    UPDATE: (id: number) => `/api/v1/tags/${id}`,
    DELETE: (id: number) => `/api/v1/tags/${id}`,
    USAGE: (id: number) => `/api/v1/tags/${id}/usage`,
    ASSIGN_TO_CONTENT: (tagId: number) => `/api/v1/tags/${tagId}/assign-content`,
    ASSIGN_TO_CONTENTS: (tagId: number) => `/api/v1/tags/${tagId}/assign-contents`,
    UNASSIGN_FROM_CONTENT: (tagId: number) => `/api/v1/tags/${tagId}/unassign-content`,
    UNASSIGN_FROM_CONTENTS: (tagId: number) => `/api/v1/tags/${tagId}/unassign-contents`,
    GET_CONTENT_TAGS: (contentId: number) => `/api/v1/contents/${contentId}/tags`,
  },

  // ========================================
  // PLAYLISTS
  // ========================================
  PLAYLISTS: {
    // CRUD
    LIST: '/api/v1/playlists',
    GET: (id: number) => `/api/v1/playlists/${id}`,
    CREATE: '/api/v1/playlists',
    UPDATE: (id: number) => `/api/v1/playlists/${id}`,
    DELETE: (id: number) => `/api/v1/playlists/${id}`,

    // Content Management
    GET_CONTENT: (id: number) => `/api/v1/playlists/${id}/content`,
    ADD_CONTENT: (id: number) => `/api/v1/playlists/${id}/content`,
    REMOVE_CONTENT: (playlistId: number, itemId: number) => `/api/v1/playlists/${playlistId}/content/${itemId}`,
    REORDER_CONTENT: (id: number) => `/api/v1/playlists/${id}/reorder`,

    // Assignments
    GET_ASSIGNMENTS: (id: number) => `/api/v1/playlists/${id}/assignments`,
    ASSIGN_DEVICES: (id: number) => `/api/v1/playlists/${id}/assign/devices`,
    ASSIGN_TAGS: (id: number) => `/api/v1/playlists/${id}/assign/tags`,
    UNASSIGN_DEVICES: (id: number) => `/api/v1/playlists/${id}/assign/devices`,
    UNASSIGN_TAGS: (id: number) => `/api/v1/playlists/${id}/assign/tags`,
  },

  // ========================================
  // USERS
  // ========================================
  USERS: {
    LIST: '/api/v1/users',
    GET: (id: number) => `/api/v1/users/${id}`,
    CREATE: '/api/v1/users',
    UPDATE: (id: number) => `/api/v1/users/${id}`,
    DELETE: (id: number) => `/api/v1/users/${id}`,
    CHANGE_PASSWORD: (id: number) => `/api/v1/users/${id}/change-password`,
  },

  // ========================================
  // AUDIT LOGS
  // ========================================
  AUDIT: {
    LIST: '/api/v1/audit-logs',
    GET: (id: number) => `/api/v1/audit-logs/${id}`,
  },

  // ========================================
  // ANALYTICS
  // ========================================
  ANALYTICS: {
    DASHBOARD: '/api/v1/analytics/dashboard',
    DEVICE_STATS: '/api/v1/analytics/devices/stats',
    CONTENT_STATS: '/api/v1/analytics/content/stats',
    DEVICE_LOGS: (deviceId: number) => `/api/v1/analytics/devices/${deviceId}/logs`,
    ACTIVITY_TIMELINE: '/api/v1/analytics/activity',
  },

  // ========================================
  // PREVIEW
  // ========================================
  PREVIEW: {
    DEVICE: (deviceId: number) => `/api/v1/preview/device/${deviceId}`,
    PLAYLIST: (playlistId: number) => `/api/v1/preview/playlist/${playlistId}`,
  },
} as const;
