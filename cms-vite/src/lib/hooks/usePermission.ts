/**
 * usePermission Hook
 *
 * React hooks for checking user permissions in components.
 * Integrates with Zustand auth store and permission utilities.
 *
 * @example
 * // Single permission check
 * const canDelete = usePermission('devices', 'delete');
 *
 * // Multiple permission checks
 * const { can, canAny, canAll, isAdmin } = usePermissions();
 * if (can('devices', 'write')) { ... }
 */

import { useAuthStore } from '@/lib/stores/authStore';
import {
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  isAdmin as checkIsAdmin,
  canPerformAction,
  getResourcePermissions,
  getAccessibleResources,
  hasAnyPermissions,
} from '@/lib/utils/permissions';

/**
 * Hook for single permission check
 *
 * @param resource - Resource name (e.g., 'devices', 'content')
 * @param action - Action name (e.g., 'read', 'write', 'delete')
 * @returns true if user has permission, false otherwise
 *
 * @example
 * const canDeleteDevice = usePermission('devices', 'delete');
 *
 * return (
 *   <Button disabled={!canDeleteDevice}>Delete</Button>
 * );
 */
export function usePermission(resource: string, action: string): boolean {
  const { user } = useAuthStore();

  // Admin always has permission
  if (user?.role === 'admin') return true;

  return hasPermission(user?.permissions, resource, action);
}

/**
 * Hook for multiple permission checks and utilities
 *
 * @returns Object with permission check methods
 *
 * @example
 * const { can, canAny, canAll, isAdmin, permissions } = usePermissions();
 *
 * // Single check
 * if (can('devices', 'write')) { ... }
 *
 * // Check any
 * if (canAny([
 *   { resource: 'devices', action: 'write' },
 *   { resource: 'devices', action: 'delete' }
 * ])) { ... }
 *
 * // Check all
 * if (canAll([
 *   { resource: 'devices', action: 'read' },
 *   { resource: 'devices', action: 'write' }
 * ])) { ... }
 *
 * // Check if admin
 * if (isAdmin()) { ... }
 *
 * // Get all permissions
 * console.log(permissions);
 */
export function usePermissions() {
  const { user } = useAuthStore();

  return {
    /**
     * Check single permission
     * @param resource - Resource name
     * @param action - Action name
     * @returns true if user has permission
     */
    can: (resource: string, action: string): boolean => {
      if (user?.role === 'admin') return true;
      return hasPermission(user?.permissions, resource, action);
    },

    /**
     * Check multiple permissions (ANY)
     * Returns true if user has at least one permission
     * @param checks - Array of {resource, action}
     * @returns true if user has any permission
     */
    canAny: (checks: Array<{ resource: string; action: string }>): boolean => {
      if (user?.role === 'admin') return true;
      return hasAnyPermission(user?.permissions, checks);
    },

    /**
     * Check multiple permissions (ALL)
     * Returns true only if user has all permissions
     * @param checks - Array of {resource, action}
     * @returns true if user has all permissions
     */
    canAll: (checks: Array<{ resource: string; action: string }>): boolean => {
      if (user?.role === 'admin') return true;
      return hasAllPermissions(user?.permissions, checks);
    },

    /**
     * Check if current user is admin
     * @returns true if user is admin
     */
    isAdmin: (): boolean => {
      return checkIsAdmin(user?.role || '');
    },

    /**
     * Get all permissions for a resource
     * @param resource - Resource name
     * @returns Array of action strings
     */
    getResourcePerms: (resource: string): string[] => {
      if (user?.role === 'admin') {
        // Admin has all actions
        return ['read', 'write', 'delete', 'assign', 'activate'];
      }
      return getResourcePermissions(user?.permissions, resource);
    },

    /**
     * Get all accessible resources
     * @returns Array of resource names
     */
    getAccessibleResources: (): string[] => {
      if (user?.role === 'admin') {
        // Admin has access to all resources
        return [
          'devices',
          'content',
          'playlists',
          'users',
          'organizations',
          'widgets',
          'templates',
        ];
      }
      return getAccessibleResources(user?.permissions);
    },

    /**
     * Check if user has any permissions at all
     * @returns true if user has at least one permission
     */
    hasAnyPermissions: (): boolean => {
      if (user?.role === 'admin') return true;
      return hasAnyPermissions(user?.permissions);
    },

    /**
     * Get current user's permissions object
     * @returns User's permissions object or empty object
     */
    permissions: user?.permissions || {},

    /**
     * Get current user's role
     * @returns User's role string
     */
    role: user?.role || '',

    /**
     * Get current user object
     * @returns User object or null
     */
    user: user,
  };
}

/**
 * Hook for resource-based permission checks
 * Useful for components that work with a specific resource
 *
 * @param resource - Resource name
 * @returns Object with permission check methods for that resource
 *
 * @example
 * const devicePerms = useResourcePermissions('devices');
 *
 * return (
 *   <>
 *     <Button disabled={!devicePerms.canWrite}>Edit</Button>
 *     <Button disabled={!devicePerms.canDelete}>Delete</Button>
 *     {devicePerms.canRead && <DeviceDetails />}
 *   </>
 * );
 */
export function useResourcePermissions(resource: string) {
  const { user } = useAuthStore();
  const isUserAdmin = user?.role === 'admin';

  return {
    /**
     * Check if user can read resource
     */
    canRead: isUserAdmin || hasPermission(user?.permissions, resource, 'read'),

    /**
     * Check if user can write/edit resource
     */
    canWrite:
      isUserAdmin || hasPermission(user?.permissions, resource, 'write'),

    /**
     * Check if user can delete resource
     */
    canDelete:
      isUserAdmin || hasPermission(user?.permissions, resource, 'delete'),

    /**
     * Check if user can assign resource
     */
    canAssign:
      isUserAdmin || hasPermission(user?.permissions, resource, 'assign'),

    /**
     * Check if user can activate resource
     */
    canActivate:
      isUserAdmin || hasPermission(user?.permissions, resource, 'activate'),

    /**
     * Check custom action
     */
    can: (action: string): boolean => {
      return isUserAdmin || hasPermission(user?.permissions, resource, action);
    },

    /**
     * Get all actions for this resource
     */
    actions: isUserAdmin
      ? ['read', 'write', 'delete', 'assign', 'activate']
      : getResourcePermissions(user?.permissions, resource),

    /**
     * Resource name
     */
    resource,
  };
}
