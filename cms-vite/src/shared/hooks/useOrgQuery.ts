/**
 * Organization-Scoped Query Utilities
 *
 * Provides utilities for creating organization-aware React Query hooks.
 * Ensures proper cache isolation between organizations and automatic
 * cache invalidation on organization switch.
 *
 * CRITICAL: All multi-tenant data MUST use these utilities to prevent
 * data leakage between organizations.
 */

import { useAuthStore } from '@/lib/stores/authStore';

/**
 * Get the current selected organization ID
 *
 * @returns The selected organization ID or undefined if not selected
 *
 * @example
 * ```tsx
 * const orgId = useSelectedOrgId();
 * // Use in query key: ['devices', orgId, filters]
 * ```
 */
export function useSelectedOrgId(): number | undefined {
  return useAuthStore((state) => state.selectedOrgId ?? undefined);
}

/**
 * Create organization-scoped query key factory
 *
 * This utility creates query keys that include the organization ID,
 * ensuring proper cache isolation between organizations.
 *
 * @param baseKey - The base key for the entity (e.g., 'devices', 'content')
 * @returns Query key factory functions
 *
 * @example
 * ```tsx
 * // Define keys for a feature
 * export const deviceKeys = createOrgScopedKeys('devices');
 *
 * // Usage in hooks
 * const orgId = useSelectedOrgId();
 * useQuery({
 *   queryKey: deviceKeys.list(orgId, filters),
 *   queryFn: () => fetchDevices(filters),
 *   enabled: !!orgId,
 * });
 * ```
 */
export function createOrgScopedKeys<T extends string>(baseKey: T) {
  return {
    // Base key for all queries of this type
    all: [baseKey] as const,

    // List queries - scoped by organization
    lists: (orgId?: number) => [...[baseKey], 'list', orgId] as const,
    list: (orgId?: number, filters?: unknown) =>
      [...[baseKey], 'list', orgId, filters] as const,

    // Detail queries - not org-scoped (ID is unique across orgs)
    details: () => [...[baseKey], 'detail'] as const,
    detail: (id: number) => [...[baseKey], 'detail', id] as const,

    // Stats/aggregates - scoped by organization
    stats: (orgId?: number) => [...[baseKey], 'stats', orgId] as const,

    // Custom sub-keys
    sub: (subKey: string, orgId?: number) =>
      [...[baseKey], subKey, orgId] as const,
    subWithId: (subKey: string, id: number) =>
      [...[baseKey], subKey, id] as const,
  };
}

/**
 * Query key factories for all multi-tenant entities
 *
 * These are standardized query keys that include organization ID
 * for proper cache isolation.
 */

// Devices
export const deviceKeys = {
  all: ['devices'] as const,
  lists: (orgId?: number) => ['devices', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['devices', 'list', orgId, filters] as const,
  details: () => ['devices', 'detail'] as const,
  detail: (id: number) => ['devices', 'detail', id] as const,
  logs: (id: number) => ['devices', 'logs', id] as const,
  commands: (id: number) => ['devices', 'commands', id] as const,
  tags: (deviceId: number) => ['devices', 'tags', deviceId] as const,
  contents: (deviceId: number) => ['devices', 'contents', deviceId] as const,
  playlists: (deviceId: number) => ['devices', 'playlists', deviceId] as const,
};

// Content
export const contentKeys = {
  all: ['content'] as const,
  lists: (orgId?: number) => ['content', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['content', 'list', orgId, filters] as const,
  details: () => ['content', 'detail'] as const,
  detail: (id: number) => ['content', 'detail', id] as const,
  stats: (orgId?: number) => ['content', 'stats', orgId] as const,
  tags: (contentId: number) => ['content', 'tags', contentId] as const,
  // Deleted content (Recycle Bin)
  deletedLists: (orgId?: number) => ['content', 'deleted', orgId] as const,
  deleted: (orgId?: number, filters?: unknown) =>
    ['content', 'deleted', orgId, filters] as const,
  // Duplicate content detection
  duplicates: (orgId?: number) => ['content', 'duplicates', orgId] as const,
};

// Playlists
export const playlistKeys = {
  all: ['playlists'] as const,
  lists: (orgId?: number) => ['playlists', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['playlists', 'list', orgId, filters] as const,
  details: () => ['playlists', 'detail'] as const,
  detail: (id: number) => ['playlists', 'detail', id] as const,
  content: (id: number) => ['playlists', 'content', id] as const,
  assignments: (id: number) => ['playlists', 'assignments', id] as const,
};

// Schedules
export const scheduleKeys = {
  all: ['schedules'] as const,
  lists: (orgId?: number) => ['schedules', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['schedules', 'list', orgId, filters] as const,
  details: () => ['schedules', 'detail'] as const,
  detail: (id: number) => ['schedules', 'detail', id] as const,
  occurrences: (orgId?: number, params?: unknown) =>
    ['schedules', 'occurrences', orgId, params] as const,
  deviceSchedules: (deviceId: number) =>
    ['schedules', 'device', deviceId] as const,
  playlistSchedules: (playlistId: number) =>
    ['schedules', 'playlist', playlistId] as const,
};

// Tags
export const tagKeys = {
  all: ['tags'] as const,
  lists: (orgId?: number) => ['tags', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['tags', 'list', orgId, filters] as const,
  details: () => ['tags', 'detail'] as const,
  detail: (id: number) => ['tags', 'detail', id] as const,
  usage: (id: number) => ['tags', 'usage', id] as const,
};

// Users
export const userKeys = {
  all: ['users'] as const,
  lists: (orgId?: number) => ['users', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['users', 'list', orgId, filters] as const,
  details: () => ['users', 'detail'] as const,
  detail: (id: number) => ['users', 'detail', id] as const,
  me: () => ['users', 'me'] as const,
};

// Roles
export const roleKeys = {
  all: ['roles'] as const,
  lists: (orgId?: number) => ['roles', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['roles', 'list', orgId, filters] as const,
  details: () => ['roles', 'detail'] as const,
  detail: (id: number) => ['roles', 'detail', id] as const,
  permissions: (id: number) => ['roles', 'permissions', id] as const,
  users: (id: number) => ['roles', 'users', id] as const,
  system: () => ['roles', 'system'] as const,
};

// Audit Logs
export const auditKeys = {
  all: ['audit'] as const,
  lists: (orgId?: number) => ['audit', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['audit', 'list', orgId, filters] as const,
  stats: (orgId?: number) => ['audit', 'stats', orgId] as const,
};

// Dashboard
export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: (orgId?: number) => ['dashboard', 'stats', orgId] as const,
  devices: (orgId?: number) => ['dashboard', 'devices', orgId] as const,
  content: (orgId?: number) => ['dashboard', 'content', orgId] as const,
  playlists: (orgId?: number) => ['dashboard', 'playlists', orgId] as const,
};

// Analytics
export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: (orgId?: number) => ['analytics', 'overview', orgId] as const,
  playback: (orgId?: number, params?: unknown) =>
    ['analytics', 'playback', orgId, params] as const,
  devices: (orgId?: number, params?: unknown) =>
    ['analytics', 'devices', orgId, params] as const,
};

// Templates
export const templateKeys = {
  all: ['templates'] as const,
  lists: (orgId?: number) => ['templates', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['templates', 'list', orgId, filters] as const,
  details: () => ['templates', 'detail'] as const,
  detail: (id: number) => ['templates', 'detail', id] as const,
};

// Widgets
export const widgetKeys = {
  all: ['widgets'] as const,
  lists: (orgId?: number) => ['widgets', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['widgets', 'list', orgId, filters] as const,
  details: () => ['widgets', 'detail'] as const,
  detail: (id: number) => ['widgets', 'detail', id] as const,
};

// Sessions
export const sessionKeys = {
  all: ['sessions'] as const,
  lists: (orgId?: number) => ['sessions', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['sessions', 'list', orgId, filters] as const,
  current: () => ['sessions', 'current'] as const,
};

// Menus
export const menuKeys = {
  all: ['menus'] as const,
  lists: (orgId?: number) => ['menus', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['menus', 'list', orgId, filters] as const,
  details: () => ['menus', 'detail'] as const,
  detail: (id: number) => ['menus', 'detail', id] as const,
  items: (menuId: number) => ['menus', 'items', menuId] as const,
};

// Translations
export const translationKeys = {
  all: ['translations'] as const,
  lists: (orgId?: number) => ['translations', 'list', orgId] as const,
  list: (orgId?: number, filters?: unknown) =>
    ['translations', 'list', orgId, filters] as const,
  details: () => ['translations', 'detail'] as const,
  detail: (id: number) => ['translations', 'detail', id] as const,
};

// Organizations (not org-scoped - system-level)
export const organizationKeys = {
  all: ['organizations'] as const,
  lists: () => ['organizations', 'list'] as const,
  list: (filters?: unknown) => ['organizations', 'list', filters] as const,
  details: () => ['organizations', 'detail'] as const,
  detail: (id: number) => ['organizations', 'detail', id] as const,
  quota: (id: number) => ['organizations', 'quota', id] as const,
};

// Weather
export const weatherKeys = {
  all: ['weather'] as const,
  config: (orgId?: number) => ['weather', 'config', orgId] as const,
  locations: (orgId?: number) => ['weather', 'locations', orgId] as const,
  current: (locationId: number) => ['weather', 'current', locationId] as const,
};

// PMS (Property Management System)
export const pmsKeys = {
  all: ['pms'] as const,
  config: (orgId?: number) => ['pms', 'config', orgId] as const,
  rooms: (orgId?: number) => ['pms', 'rooms', orgId] as const,
  guests: (roomId: number) => ['pms', 'guests', roomId] as const,
};
