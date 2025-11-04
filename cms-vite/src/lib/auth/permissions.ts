/**
 * Permission and Authorization Utilities
 * Role-based access control helpers
 */

import { USER_ROLES } from '../constants/app';

export type UserRole = typeof USER_ROLES[keyof typeof USER_ROLES];

export interface User {
  id: number;
  username: string;
  role: UserRole;
  organization_id: number;
}

/**
 * Check if user has specific role
 */
export function hasRole(user: User | null, role: UserRole): boolean {
  return user?.role === role;
}

/**
 * Check if user is admin
 */
export function isAdmin(user: User | null): boolean {
  return hasRole(user, USER_ROLES.ADMIN);
}

/**
 * Check if user is manager or admin
 */
export function isManagerOrAbove(user: User | null): boolean {
  return user?.role === USER_ROLES.ADMIN || user?.role === USER_ROLES.MANAGER;
}

/**
 * Check if user can perform action
 */
export function canPerformAction(user: User | null, action: string): boolean {
  if (!user) return false;

  const permissions: Record<UserRole, string[]> = {
    [USER_ROLES.ADMIN]: ['*'], // All permissions
    [USER_ROLES.MANAGER]: [
      'device.view',
      'device.create',
      'device.update',
      'device.delete',
      'content.view',
      'content.create',
      'content.update',
      'content.delete',
      'playlist.view',
      'playlist.create',
      'playlist.update',
      'playlist.delete',
    ],
    [USER_ROLES.VIEWER]: ['device.view', 'content.view', 'playlist.view'],
  };

  const userPermissions = permissions[user.role] || [];

  // Admin has all permissions
  if (userPermissions.includes('*')) return true;

  return userPermissions.includes(action);
}

/**
 * Permission constants
 */
export const PERMISSIONS = {
  DEVICE: {
    VIEW: 'device.view',
    CREATE: 'device.create',
    UPDATE: 'device.update',
    DELETE: 'device.delete',
  },
  CONTENT: {
    VIEW: 'content.view',
    CREATE: 'content.create',
    UPDATE: 'content.update',
    DELETE: 'content.delete',
  },
  PLAYLIST: {
    VIEW: 'playlist.view',
    CREATE: 'playlist.create',
    UPDATE: 'playlist.update',
    DELETE: 'playlist.delete',
  },
  USER: {
    VIEW: 'user.view',
    CREATE: 'user.create',
    UPDATE: 'user.update',
    DELETE: 'user.delete',
  },
} as const;
