/**
 * Permission Utilities
 *
 * Check user permissions against RBAC rules from backend.
 * Used by hooks and components for access control.
 *
 * Permission structure from backend:
 * {
 *   "devices": ["read", "write", "delete"],
 *   "content": ["read", "write"],
 *   "playlists": ["read", "write", "delete"],
 *   "users": ["read"],
 *   "organizations": ["read"]
 * }
 */

export type Resource = string;
export type Action = string;
export type Permissions = Record<Resource, Action[]>;

/**
 * Check if user has permission for resource + action
 *
 * @param permissions - User's permissions object
 * @param resource - Resource name (e.g., 'devices', 'content')
 * @param action - Action name (e.g., 'read', 'write', 'delete')
 * @returns true if user has permission, false otherwise
 *
 * @example
 * hasPermission(user.permissions, 'devices', 'delete')
 */
export function hasPermission(
  permissions: Permissions | undefined,
  resource: Resource,
  action: Action
): boolean {
  if (!permissions) return false;

  const resourcePerms = permissions[resource];
  if (!resourcePerms || !Array.isArray(resourcePerms)) return false;

  return resourcePerms.includes(action);
}

/**
 * Check if user has ANY of the specified permissions
 *
 * @param permissions - User's permissions object
 * @param checks - Array of {resource, action} to check
 * @returns true if user has at least one permission
 *
 * @example
 * hasAnyPermission(user.permissions, [
 *   { resource: 'devices', action: 'write' },
 *   { resource: 'devices', action: 'delete' }
 * ])
 */
export function hasAnyPermission(
  permissions: Permissions | undefined,
  checks: Array<{ resource: Resource; action: Action }>
): boolean {
  return checks.some(({ resource, action }) =>
    hasPermission(permissions, resource, action)
  );
}

/**
 * Check if user has ALL of the specified permissions
 *
 * @param permissions - User's permissions object
 * @param checks - Array of {resource, action} to check
 * @returns true if user has all permissions
 *
 * @example
 * hasAllPermissions(user.permissions, [
 *   { resource: 'devices', action: 'read' },
 *   { resource: 'devices', action: 'write' }
 * ])
 */
export function hasAllPermissions(
  permissions: Permissions | undefined,
  checks: Array<{ resource: Resource; action: Action }>
): boolean {
  return checks.every(({ resource, action }) =>
    hasPermission(permissions, resource, action)
  );
}

/**
 * Get all permissions for a resource
 *
 * @param permissions - User's permissions object
 * @param resource - Resource name
 * @returns Array of action strings
 *
 * @example
 * getResourcePermissions(user.permissions, 'devices')
 * // Returns: ['read', 'write', 'delete']
 */
export function getResourcePermissions(
  permissions: Permissions | undefined,
  resource: Resource
): Action[] {
  if (!permissions) return [];
  return permissions[resource] || [];
}

/**
 * Check if user is admin (has all permissions)
 *
 * @param role - User's role string
 * @returns true if user is admin
 *
 * @example
 * isAdmin(user.role)
 */
export function isAdmin(role: string): boolean {
  return role === 'admin';
}

/**
 * Check if user can perform action on resource
 * Convenience wrapper that handles admin override
 *
 * @param role - User's role
 * @param permissions - User's permissions object
 * @param resource - Resource name
 * @param action - Action name
 * @returns true if user can perform action
 *
 * @example
 * canPerformAction(user.role, user.permissions, 'devices', 'delete')
 */
export function canPerformAction(
  role: string,
  permissions: Permissions | undefined,
  resource: Resource,
  action: Action
): boolean {
  // Admin override - always has permission
  if (isAdmin(role)) return true;

  return hasPermission(permissions, resource, action);
}

/**
 * Get all resources user has access to
 *
 * @param permissions - User's permissions object
 * @returns Array of resource names
 *
 * @example
 * getAccessibleResources(user.permissions)
 * // Returns: ['devices', 'content', 'playlists']
 */
export function getAccessibleResources(
  permissions: Permissions | undefined
): Resource[] {
  if (!permissions) return [];
  return Object.keys(permissions);
}

/**
 * Check if user has any permissions at all
 *
 * @param permissions - User's permissions object
 * @returns true if user has at least one permission
 */
export function hasAnyPermissions(
  permissions: Permissions | undefined
): boolean {
  if (!permissions) return false;
  return Object.keys(permissions).length > 0;
}
