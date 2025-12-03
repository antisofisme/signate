/**
 * Permission Constants
 * Centralized definitions for RBAC permissions
 */

// ============================================================================
// Resource Definitions
// ============================================================================

export const PERMISSION_RESOURCES = [
  'dashboard',
  'devices',
  'contents',
  'playlists',
  'schedules',
  'tags',
  'menus',
  'analytics',
  'audit_logs',
  'users',
  'organizations',
  'roles',
  'sessions',
  'settings',
  'system',
] as const;

export type PermissionResource = (typeof PERMISSION_RESOURCES)[number];

// ============================================================================
// Action Definitions
// ============================================================================

export const PERMISSION_ACTIONS = [
  'read',    // Read access
  'create',  // Create new items
  'edit',    // Update existing items
  'delete',  // Remove items
  'manage',  // Full control (implies all above)
] as const;

export type PermissionAction = (typeof PERMISSION_ACTIONS)[number];

// ============================================================================
// Permission Type
// ============================================================================

export type Permissions = Record<string, string[]>;

// ============================================================================
// Resource Labels (for UI)
// ============================================================================

export const RESOURCE_LABELS: Record<PermissionResource, string> = {
  dashboard: 'Dashboard',
  devices: 'Devices',
  contents: 'Content',
  playlists: 'Playlists',
  schedules: 'Schedules',
  tags: 'Tags',
  menus: 'Digital Menus',
  analytics: 'Analytics',
  audit_logs: 'Audit Logs',
  users: 'Users',
  organizations: 'Organizations',
  roles: 'Roles & Permissions',
  sessions: 'Active Sessions',
  settings: 'Settings',
  system: 'System Administration',
};

export const RESOURCE_I18N_KEYS: Record<PermissionResource, string> = {
  dashboard: 'rbac.resources.dashboard',
  devices: 'rbac.resources.devices',
  contents: 'rbac.resources.contents',
  playlists: 'rbac.resources.playlists',
  schedules: 'rbac.resources.schedules',
  tags: 'rbac.resources.tags',
  menus: 'rbac.resources.menus',
  analytics: 'rbac.resources.analytics',
  audit_logs: 'rbac.resources.auditLogs',
  users: 'rbac.resources.users',
  organizations: 'rbac.resources.organizations',
  roles: 'rbac.resources.roles',
  sessions: 'rbac.resources.sessions',
  settings: 'rbac.resources.settings',
  system: 'rbac.resources.system',
};

// ============================================================================
// Action Labels (for UI)
// ============================================================================

export const ACTION_LABELS: Record<PermissionAction, string> = {
  read: 'View',
  create: 'Create',
  edit: 'Edit',
  delete: 'Delete',
  manage: 'Manage',
};

export const ACTION_I18N_KEYS: Record<PermissionAction, string> = {
  read: 'rbac.actions.read',
  create: 'rbac.actions.create',
  edit: 'rbac.actions.edit',
  delete: 'rbac.actions.delete',
  manage: 'rbac.actions.manage',
};

// ============================================================================
// Action Colors (for UI)
// ============================================================================

export const ACTION_COLORS: Record<PermissionAction, string> = {
  read: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
  create: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
  edit: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
  delete: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
  manage: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Count total permissions in a permission object
 */
export function countPermissions(permissions: Permissions): number {
  return Object.values(permissions).reduce((total, actions) => total + actions.length, 0);
}

/**
 * Get total possible permissions
 */
export function getTotalPossiblePermissions(): number {
  return PERMISSION_RESOURCES.length * PERMISSION_ACTIONS.length;
}

/**
 * Check if a resource has a specific action
 */
export function hasPermission(
  permissions: Permissions,
  resource: string,
  action: string
): boolean {
  return permissions[resource]?.includes(action) ?? false;
}

/**
 * Check if resource has 'manage' action (implies all permissions)
 */
export function hasManagePermission(permissions: Permissions, resource: string): boolean {
  return hasPermission(permissions, resource, 'manage');
}

/**
 * Check if all actions are selected for a resource
 */
export function hasAllActionsForResource(permissions: Permissions, resource: string): boolean {
  const actions = permissions[resource] || [];
  return PERMISSION_ACTIONS.every((action) => actions.includes(action));
}

/**
 * Check if all resources have a specific action
 */
export function hasActionForAllResources(permissions: Permissions, action: string): boolean {
  return PERMISSION_RESOURCES.every((resource) => {
    const actions = permissions[resource] || [];
    return actions.includes(action);
  });
}

/**
 * Create empty permissions object
 */
export function createEmptyPermissions(): Permissions {
  return {};
}

/**
 * Create full permissions object (all permissions)
 */
export function createFullPermissions(): Permissions {
  const permissions: Permissions = {};
  PERMISSION_RESOURCES.forEach((resource) => {
    permissions[resource] = [...PERMISSION_ACTIONS];
  });
  return permissions;
}

// ============================================================================
// Default System Role Permissions
// ============================================================================

export const SYSTEM_ROLE_PERMISSIONS: Record<string, Permissions> = {
  SUPER_ADMIN: {
    dashboard: ['read', 'manage'],
    devices: ['read', 'create', 'edit', 'delete', 'manage'],
    contents: ['read', 'create', 'edit', 'delete', 'manage'],
    playlists: ['read', 'create', 'edit', 'delete', 'manage'],
    schedules: ['read', 'create', 'edit', 'delete', 'manage'],
    tags: ['read', 'create', 'edit', 'delete', 'manage'],
    menus: ['read', 'create', 'edit', 'delete', 'manage'],
    analytics: ['read', 'manage'],
    audit_logs: ['read', 'manage'],
    users: ['read', 'create', 'edit', 'delete', 'manage'],
    organizations: ['read', 'create', 'edit', 'delete', 'manage'],
    roles: ['read', 'create', 'edit', 'delete', 'manage'],
    sessions: ['read', 'manage'],
    settings: ['read', 'edit', 'manage'],
    system: ['read', 'manage'],
  },
  ADMIN: {
    dashboard: ['read'],
    devices: ['read', 'create', 'edit', 'delete'],
    contents: ['read', 'create', 'edit', 'delete'],
    playlists: ['read', 'create', 'edit', 'delete'],
    schedules: ['read', 'create', 'edit', 'delete'],
    tags: ['read', 'create', 'edit', 'delete'],
    menus: ['read', 'create', 'edit', 'delete'],
    analytics: ['read'],
    audit_logs: ['read'],
    users: ['read', 'create', 'edit', 'delete'],
    organizations: ['read', 'edit'],
    roles: ['read', 'create', 'edit', 'delete'],
    sessions: ['read'],
    settings: ['read', 'edit'],
  },
  CONTENT_MANAGER: {
    dashboard: ['read'],
    devices: ['read'],
    contents: ['read', 'create', 'edit', 'delete'],
    playlists: ['read', 'create', 'edit', 'delete'],
    schedules: ['read', 'create', 'edit'],
    tags: ['read', 'create', 'edit'],
    menus: ['read', 'create', 'edit'],
  },
  VIEWER: {
    dashboard: ['read'],
    devices: ['read'],
    contents: ['read'],
    playlists: ['read'],
    schedules: ['read'],
    analytics: ['read'],
  },
};
