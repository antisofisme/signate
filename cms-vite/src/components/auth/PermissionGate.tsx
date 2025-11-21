/**
 * PermissionGate Component
 *
 * Conditionally render children based on permissions.
 * Integrates with RBAC system from backend.
 *
 * @example
 * // Hide button if no permission
 * <PermissionGate resource="devices" action="delete">
 *   <Button>Delete Device</Button>
 * </PermissionGate>
 *
 * // Show fallback if no permission
 * <PermissionGate
 *   resource="devices"
 *   action="write"
 *   fallback={<p>You don't have permission to edit devices</p>}
 * >
 *   <EditDeviceForm />
 * </PermissionGate>
 */

import { ReactNode } from 'react';
import { usePermission, usePermissions } from '@/lib/hooks/usePermission';

// =============================================================================
// SINGLE PERMISSION GATE
// =============================================================================

interface PermissionGateProps {
  children: ReactNode;
  resource: string;
  action: string;
  fallback?: ReactNode;
}

/**
 * Gate that checks a single permission
 *
 * @param children - Content to render if permission is granted
 * @param resource - Resource name (e.g., 'devices', 'content')
 * @param action - Action name (e.g., 'read', 'write', 'delete')
 * @param fallback - Content to render if permission is denied (default: null)
 *
 * @example
 * <PermissionGate resource="devices" action="delete">
 *   <Button onClick={handleDelete}>Delete Device</Button>
 * </PermissionGate>
 */
export function PermissionGate({
  children,
  resource,
  action,
  fallback = null,
}: PermissionGateProps) {
  const hasAccess = usePermission(resource, action);

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

// =============================================================================
// MULTI-PERMISSION GATE
// =============================================================================

interface MultiPermissionGateProps {
  children: ReactNode;
  checks: Array<{ resource: string; action: string }>;
  mode?: 'any' | 'all';
  fallback?: ReactNode;
}

/**
 * Gate that checks multiple permissions
 *
 * @param children - Content to render if permission check passes
 * @param checks - Array of {resource, action} to check
 * @param mode - 'any' (at least one permission) or 'all' (all permissions required)
 * @param fallback - Content to render if permission check fails (default: null)
 *
 * @example
 * // Show if user can EITHER write OR delete devices
 * <MultiPermissionGate
 *   checks={[
 *     { resource: 'devices', action: 'write' },
 *     { resource: 'devices', action: 'delete' }
 *   ]}
 *   mode="any"
 * >
 *   <DeviceActions />
 * </MultiPermissionGate>
 *
 * // Show only if user can BOTH read AND write content
 * <MultiPermissionGate
 *   checks={[
 *     { resource: 'content', action: 'read' },
 *     { resource: 'content', action: 'write' }
 *   ]}
 *   mode="all"
 * >
 *   <ContentEditor />
 * </MultiPermissionGate>
 */
export function MultiPermissionGate({
  children,
  checks,
  mode = 'all',
  fallback = null,
}: MultiPermissionGateProps) {
  const { canAny, canAll } = usePermissions();
  const hasAccess = mode === 'any' ? canAny(checks) : canAll(checks);

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

// =============================================================================
// ADMIN GATE
// =============================================================================

interface AdminGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Gate that only shows content to admin users
 *
 * @param children - Content to render if user is admin
 * @param fallback - Content to render if user is not admin (default: null)
 *
 * @example
 * <AdminGate fallback={<p>Admin access required</p>}>
 *   <OrganizationSettings />
 * </AdminGate>
 */
export function AdminGate({ children, fallback = null }: AdminGateProps) {
  const { isAdmin } = usePermissions();

  return isAdmin() ? <>{children}</> : <>{fallback}</>;
}

// =============================================================================
// RESOURCE GATE
// =============================================================================

interface ResourceGateProps {
  children: ReactNode;
  resource: string;
  actions?: string[];
  mode?: 'any' | 'all';
  fallback?: ReactNode;
}

/**
 * Gate that checks multiple actions for a single resource
 *
 * @param children - Content to render if permission check passes
 * @param resource - Resource name
 * @param actions - Array of actions to check (default: ['read'])
 * @param mode - 'any' (at least one action) or 'all' (all actions required)
 * @param fallback - Content to render if permission check fails (default: null)
 *
 * @example
 * // Show if user can read OR write devices
 * <ResourceGate resource="devices" actions={['read', 'write']} mode="any">
 *   <DeviceList />
 * </ResourceGate>
 *
 * // Show only if user can both read AND write content
 * <ResourceGate resource="content" actions={['read', 'write']} mode="all">
 *   <ContentUpload />
 * </ResourceGate>
 */
export function ResourceGate({
  children,
  resource,
  actions = ['read'],
  mode = 'all',
  fallback = null,
}: ResourceGateProps) {
  const { canAny, canAll } = usePermissions();

  const checks = actions.map((action) => ({ resource, action }));
  const hasAccess = mode === 'any' ? canAny(checks) : canAll(checks);

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}

// =============================================================================
// RENDER PROPS PATTERN
// =============================================================================

interface PermissionRenderProps {
  children: (hasPermission: boolean) => ReactNode;
  resource: string;
  action: string;
}

/**
 * Render props pattern for more complex permission logic
 *
 * @param children - Render function that receives hasPermission boolean
 * @param resource - Resource name
 * @param action - Action name
 *
 * @example
 * <PermissionRender resource="devices" action="delete">
 *   {(canDelete) => (
 *     <Button
 *       onClick={handleDelete}
 *       disabled={!canDelete}
 *       title={!canDelete ? 'No permission to delete' : ''}
 *     >
 *       Delete Device
 *     </Button>
 *   )}
 * </PermissionRender>
 */
export function PermissionRender({
  children,
  resource,
  action,
}: PermissionRenderProps) {
  const hasPermission = usePermission(resource, action);

  return <>{children(hasPermission)}</>;
}
