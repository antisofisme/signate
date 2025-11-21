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
    // Quota endpoints
    QUOTA: (id: number) => `/api/v1/organizations/${id}/quota`,
    UPDATE_QUOTA: (id: number) => `/api/v1/organizations/${id}/quota`,
    CHECK_DEVICE_QUOTA: (id: number) => `/api/v1/organizations/${id}/quota/check/device`,
    CHECK_USER_QUOTA: (id: number) => `/api/v1/organizations/${id}/quota/check/user`,
    CHECK_CONTENT_QUOTA: (id: number) => `/api/v1/organizations/${id}/quota/check/content`,
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
    CONNECTION_LOGS: (id: number) => `/api/v1/devices/${id}/connection-logs`,
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

  // ========================================
  // WIDGETS
  // ========================================
  WIDGETS: {
    LIST: '/api/v1/widgets',
    GET: (id: number) => `/api/v1/widgets/${id}`,
    CREATE: '/api/v1/widgets',
    UPDATE: (id: number) => `/api/v1/widgets/${id}`,
    DELETE: (id: number) => `/api/v1/widgets/${id}`,

    // Playlist Widget Assignment
    GET_PLAYLIST_WIDGETS: (playlistId: number) => `/api/v1/widgets/playlists/${playlistId}/widgets`,
    ASSIGN_TO_PLAYLIST: (playlistId: number) => `/api/v1/widgets/playlists/${playlistId}/widgets`,
    UPDATE_PLAYLIST_WIDGET: (id: number) => `/api/v1/widgets/playlist-widgets/${id}`,
    REMOVE_FROM_PLAYLIST: (playlistId: number, widgetId: number) => `/api/v1/widgets/playlists/${playlistId}/widgets/${widgetId}`,
  },

  // ========================================
  // TEMPLATES
  // ========================================
  TEMPLATES: {
    LIST: '/api/v1/templates',
    GET: (id: number) => `/api/v1/templates/${id}`,
    CREATE: '/api/v1/templates',
    UPDATE: (id: number) => `/api/v1/templates/${id}`,
    DELETE: (id: number) => `/api/v1/templates/${id}`,
    PREVIEW: (id: number) => `/api/v1/templates/${id}/preview`,
    RENDER: (id: number) => `/api/v1/templates/${id}/render`,
    VALIDATE: '/api/v1/templates/validate',
    EXTRACT_VARIABLES: '/api/v1/templates/extract-variables',
  },

  // ========================================
  // SCHEDULES
  // ========================================
  SCHEDULES: {
    LIST: '/api/v1/schedules',
    GET: (id: number) => `/api/v1/schedules/${id}`,
    CREATE: '/api/v1/schedules',
    UPDATE: (id: number) => `/api/v1/schedules/${id}`,
    DELETE: (id: number) => `/api/v1/schedules/${id}`,
    GET_BY_PLAYLIST: (playlistId: number) => `/api/v1/schedules/playlist/${playlistId}`,
    GET_BY_DEVICE: (deviceId: number) => `/api/v1/schedules/device/${deviceId}`,
    ACTIVATE: (id: number) => `/api/v1/schedules/${id}/activate`,
    DEACTIVATE: (id: number) => `/api/v1/schedules/${id}/deactivate`,
    PAUSE: (id: number) => `/api/v1/schedules/${id}/pause`,
    CHECK_CONFLICTS: '/api/v1/schedules/check-conflicts',
    GET_OCCURRENCES: '/api/v1/schedules/occurrences',
    // Advanced scheduling features
    CHECK_CONFLICT: '/api/v1/schedules/check-conflict',
    VALIDATE: '/api/v1/schedules/validate',
    NEXT_OCCURRENCE: (id: number) => `/api/v1/schedules/${id}/next-occurrence`,
    ACTIVE: '/api/v1/schedules/active',
  },

  // ========================================
  // TRANSLATIONS
  // ========================================
  TRANSLATIONS: {
    LIST: '/api/v1/translations',
    GET: (id: number) => `/api/v1/translations/${id}`,
    CREATE: '/api/v1/translations',
    UPDATE: (id: number) => `/api/v1/translations/${id}`,
    DELETE: (id: number) => `/api/v1/translations/${id}`,
    GET_BY_LOCALE: (locale: string) => `/api/v1/translations/locale/${locale}`,
    GET_BY_KEY: (key: string) => `/api/v1/translations/key/${key}`,
    GET_ENTITY_TRANSLATIONS: (entityType: string, entityId: number) => `/api/v1/translations/${entityType}/${entityId}`,
    BULK_CREATE: '/api/v1/translations/bulk',
    BULK_IMPORT: '/api/v1/translations/import',
    STATS: '/api/v1/translations/stats',
    APPROVE: (id: number) => `/api/v1/translations/${id}/approve`,
    REJECT: (id: number) => `/api/v1/translations/${id}/reject`,
  },

  // ========================================
  // SESSIONS
  // ========================================
  SESSIONS: {
    LIST: '/api/v1/sessions',
    GET: (id: string) => `/api/v1/sessions/${id}`,
    DELETE: (id: string) => `/api/v1/sessions/${id}`,
    REVOKE_ALL: '/api/v1/sessions/revoke-all',
    STATS: '/api/v1/sessions/stats',
    ACTIVE: '/api/v1/sessions/active',
    USER_SESSIONS: (userId: number) => `/api/v1/sessions/user/${userId}`,
    IP_SESSIONS: (ip: string) => `/api/v1/sessions/ip/${ip}`,
  },

  // ========================================
  // RBAC (Role-Based Access Control)
  // ========================================
  RBAC: {
    // Roles
    ROLES: {
      LIST: '/api/v1/roles',
      GET: (id: number) => `/api/v1/roles/${id}`,
      CREATE: '/api/v1/roles',
      UPDATE: (id: number) => `/api/v1/roles/${id}`,
      DELETE: (id: number) => `/api/v1/roles/${id}`,
      SYSTEM: '/api/v1/roles/system',
      GET_PERMISSIONS: (id: number) => `/api/v1/roles/${id}/permissions`,
      ADD_PERMISSIONS: (id: number) => `/api/v1/roles/${id}/permissions`,
      REMOVE_PERMISSIONS: (id: number) => `/api/v1/roles/${id}/permissions`,
      GET_USERS: (id: number) => `/api/v1/roles/${id}/users`,
      ASSIGN_USERS: (id: number) => `/api/v1/roles/${id}/users`,
      REMOVE_USERS: (id: number) => `/api/v1/roles/${id}/users`,
    },
    // Permissions
    PERMISSIONS: {
      LIST: '/api/v1/permissions',
      GET: (id: number) => `/api/v1/permissions/${id}`,
      CREATE: '/api/v1/permissions',
      UPDATE: (id: number) => `/api/v1/permissions/${id}`,
      DELETE: (id: number) => `/api/v1/permissions/${id}`,
      BY_RESOURCE: (resource: string) => `/api/v1/permissions/resource/${resource}`,
    },
    // User Permissions
    USER_PERMISSIONS: {
      GET: (userId: number) => `/api/v1/users/${userId}/permissions`,
      CHECK: (userId: number) => `/api/v1/users/${userId}/check-permission`,
      GET_ROLES: (userId: number) => `/api/v1/users/${userId}/roles`,
      ASSIGN_ROLE: (userId: number) => `/api/v1/users/${userId}/roles`,
      REMOVE_ROLE: (userId: number, roleId: number) => `/api/v1/users/${userId}/roles/${roleId}`,
    },
  },

  // ========================================
  // PMS (Property Management System)
  // ========================================
  PMS: {
    CONFIG: '/api/v1/pms/config',
    TEST_CONNECTION: '/api/v1/pms/test-connection',
    SYNC_STATUS: '/api/v1/pms/sync/status',
    TRIGGER_SYNC: '/api/v1/pms/sync/trigger',
    STATS: '/api/v1/pms/stats',

    // Guests
    GUESTS: '/api/v1/pms/guests',
    CURRENT_GUESTS: '/api/v1/pms/guests/current',
    GUEST: (id: number) => `/api/v1/pms/guests/${id}`,
    SYNC_GUESTS: '/api/v1/pms/sync/guests',

    // Rooms
    ROOMS: '/api/v1/pms/rooms',
    ROOM: (id: number) => `/api/v1/pms/rooms/${id}`,
    SYNC_ROOMS: '/api/v1/pms/sync/rooms',
    MAP_ROOM_DEVICE: '/api/v1/pms/rooms/map-device',
    UNMAP_ROOM_DEVICE: (roomId: number) => `/api/v1/pms/rooms/${roomId}/unmap-device`,
  },

  // ========================================
  // WEATHER
  // ========================================
  WEATHER: {
    CONFIG: '/api/v1/weather/config',
    TEST_API: '/api/v1/weather/test-api',
    LOCATIONS: '/api/v1/weather/locations',
    LOCATION: (id: number) => `/api/v1/weather/locations/${id}`,
    DATA: (locationId: number) => `/api/v1/weather/data/${locationId}`,
    BY_COORDS: '/api/v1/weather/data/coords',
    GEOCODING: '/api/v1/weather/geocoding',
  },
} as const;
