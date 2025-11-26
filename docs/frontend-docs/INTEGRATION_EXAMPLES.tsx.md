/**
 * Permission System Integration Examples
 *
 * Copy-paste these examples into your components to add permission checks.
 * All examples are production-ready and follow best practices.
 */

// ============================================================================
// EXAMPLE 1: ContentTable with Permission Gates
// ============================================================================

/**
 * How to add permission gates to ContentTable component
 * Location: src/features/contents/components/ContentTable.tsx
 */

// Add these imports at the top
import { PermissionGate } from '@/components/auth';
import { useResourcePermissions } from '@/lib/hooks';

// In the ContentTable component, add permission checks:

export function ContentTableExample() {
  const contentPerms = useResourcePermissions('content');

  return (
    <div className="space-y-4">
      {/* HEADER - Upload button with permission gate */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Content Library</h2>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-gray-100 rounded-lg">
            Filters
          </button>

          {/* PERMISSION CHECK: Only show upload if user can write */}
          <PermissionGate resource="content" action="write">
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              Upload Content
            </button>
          </PermissionGate>
        </div>
      </div>

      {/* TABLE - Action buttons with permission gates */}
      <table>
        <tbody>
          {contentData?.data.map((content) => (
            <tr key={content.id}>
              {/* ... other columns ... */}

              {/* ACTIONS COLUMN with permission checks */}
              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  {/* Edit - requires write permission */}
                  <PermissionGate resource="content" action="write">
                    <button
                      onClick={() => handleEdit(content)}
                      className="text-green-600 hover:text-green-700"
                      title="Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </PermissionGate>

                  {/* Preview - available to everyone who can read */}
                  {contentPerms.canRead && (
                    <button
                      onClick={() => handlePreview(content)}
                      className="text-blue-600 hover:text-blue-700"
                      title="Preview"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  )}

                  {/* Download - available to everyone */}
                  <button
                    onClick={() => handleDownload(content)}
                    className="text-gray-600 hover:text-gray-700"
                    title="Download"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  {/* Delete - requires delete permission */}
                  <PermissionGate resource="content" action="delete">
                    <button
                      onClick={() => setContentToDelete(content)}
                      className="text-red-600 hover:text-red-700"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </PermissionGate>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// EXAMPLE 2: DeviceTable with Permission Checks
// ============================================================================

/**
 * How to add permission checks to DeviceTable component
 * Location: src/features/devices/components/DeviceTable.tsx
 */

import { usePermissions } from '@/lib/hooks';
import { PermissionGate, MultiPermissionGate } from '@/components/auth';

export function DeviceTableExample() {
  const { can, canAny } = usePermissions();

  // Check if user can manage devices at all
  const canManageDevices = canAny([
    { resource: 'devices', action: 'write' },
    { resource: 'devices', action: 'delete' },
    { resource: 'devices', action: 'activate' },
  ]);

  // Guard: No read permission = no access
  if (!can('devices', 'read')) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">
          You don't have permission to view devices.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* HEADER with conditional bulk actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Devices</h2>

        {/* Show bulk actions only if user can manage devices */}
        {canManageDevices && (
          <div className="flex gap-2">
            <PermissionGate resource="devices" action="activate">
              <button
                onClick={handleBulkActivate}
                className="px-4 py-2 bg-green-600 text-white rounded-lg"
              >
                Activate Selected
              </button>
            </PermissionGate>

            <PermissionGate resource="devices" action="delete">
              <button
                onClick={handleBulkDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg"
              >
                Delete Selected
              </button>
            </PermissionGate>
          </div>
        )}
      </div>

      {/* TABLE with action buttons */}
      <table>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              {/* ... other columns ... */}

              <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                  {/* Edit - write permission */}
                  <PermissionGate resource="devices" action="write">
                    <button onClick={() => handleEdit(device)}>
                      <Edit className="w-4 h-4" />
                    </button>
                  </PermissionGate>

                  {/* Activate - activate permission */}
                  <PermissionGate resource="devices" action="activate">
                    <button onClick={() => handleActivate(device)}>
                      <Power className="w-4 h-4" />
                    </button>
                  </PermissionGate>

                  {/* Delete - delete permission */}
                  <PermissionGate resource="devices" action="delete">
                    <button onClick={() => handleDelete(device)}>
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </PermissionGate>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// EXAMPLE 3: Upload Modal with Disabled State
// ============================================================================

/**
 * How to disable upload modal if user lacks permission
 * Location: src/features/contents/components/UploadModal.tsx
 */

import { usePermission } from '@/lib/hooks';

export function UploadModalExample() {
  const canUpload = usePermission('content', 'write');

  return (
    <div className="modal">
      <h2>Upload Content</h2>

      {!canUpload ? (
        // Show message if no permission
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-yellow-800">
            You don't have permission to upload content.
          </p>
          <p className="text-sm text-yellow-600 mt-1">
            Contact your administrator to request access.
          </p>
        </div>
      ) : (
        // Show upload form if has permission
        <form onSubmit={handleUpload}>
          <input type="file" />
          <button type="submit">Upload</button>
        </form>
      )}
    </div>
  );
}

// ============================================================================
// EXAMPLE 4: Playlist Builder with Multi-Permission
// ============================================================================

/**
 * How to use multi-permission gates in Playlist Builder
 * Location: src/features/playlists/components/PlaylistBuilder.tsx
 */

import { MultiPermissionGate, AdminGate } from '@/components/auth';
import { usePermissions } from '@/lib/hooks';

export function PlaylistBuilderExample() {
  const { can, isAdmin } = usePermissions();

  return (
    <div className="space-y-6">
      {/* CREATE PLAYLIST - write permission */}
      <PermissionGate resource="playlists" action="write">
        <button
          onClick={handleCreatePlaylist}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Create New Playlist
        </button>
      </PermissionGate>

      {/* PLAYLIST LIST */}
      <div className="space-y-4">
        {playlists.map((playlist) => (
          <div key={playlist.id} className="border rounded-lg p-4">
            <h3>{playlist.name}</h3>

            <div className="flex gap-2 mt-4">
              {/* Edit - write permission */}
              <PermissionGate resource="playlists" action="write">
                <button onClick={() => handleEdit(playlist)}>Edit</button>
              </PermissionGate>

              {/* Assign to devices - requires both playlist write AND device assign */}
              <MultiPermissionGate
                checks={[
                  { resource: 'playlists', action: 'write' },
                  { resource: 'devices', action: 'assign' },
                ]}
                mode="all"
                fallback={
                  <button disabled title="No permission to assign playlists">
                    Assign (No Permission)
                  </button>
                }
              >
                <button onClick={() => handleAssign(playlist)}>
                  Assign to Devices
                </button>
              </MultiPermissionGate>

              {/* Delete - delete permission */}
              <PermissionGate resource="playlists" action="delete">
                <button
                  onClick={() => handleDelete(playlist)}
                  className="text-red-600"
                >
                  Delete
                </button>
              </PermissionGate>
            </div>

            {/* Advanced settings - admin only */}
            <AdminGate>
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <h4>Advanced Settings (Admin Only)</h4>
                <button onClick={() => handleAdvancedSettings(playlist)}>
                  Configure Advanced Options
                </button>
              </div>
            </AdminGate>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 5: User Management with Admin Gate
// ============================================================================

/**
 * How to protect user management with admin-only gate
 * Location: src/features/users/components/UserManagement.tsx
 */

import { AdminGate, PermissionGate } from '@/components/auth';

export function UserManagementExample() {
  return (
    <div className="space-y-6">
      {/* USER LIST - requires users:read */}
      <PermissionGate
        resource="users"
        action="read"
        fallback={<p>No permission to view users</p>}
      >
        <div>
          <h2>Users</h2>
          <table>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>
                    {/* Edit user - requires users:write */}
                    <PermissionGate resource="users" action="write">
                      <button onClick={() => handleEditUser(user)}>
                        Edit
                      </button>
                    </PermissionGate>

                    {/* Delete user - admin only */}
                    <AdminGate>
                      <button onClick={() => handleDeleteUser(user)}>
                        Delete
                      </button>
                    </AdminGate>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PermissionGate>

      {/* ORGANIZATION SETTINGS - admin only */}
      <AdminGate fallback={<p>Admin access required</p>}>
        <div className="p-4 border rounded-lg">
          <h2>Organization Settings</h2>
          <p>Only administrators can access these settings.</p>
          <OrganizationSettingsForm />
        </div>
      </AdminGate>
    </div>
  );
}

// ============================================================================
// EXAMPLE 6: Render Props Pattern for Complex Logic
// ============================================================================

/**
 * How to use render props for complex permission-based UI
 */

import { PermissionRender } from '@/components/auth';

export function ComplexPermissionExample() {
  return (
    <div>
      {/* Button that changes based on permission */}
      <PermissionRender resource="content" action="delete">
        {(canDelete) => (
          <button
            onClick={handleDelete}
            disabled={!canDelete}
            className={`px-4 py-2 rounded ${
              canDelete
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
            title={
              canDelete
                ? 'Delete content'
                : 'You do not have permission to delete content'
            }
          >
            {canDelete ? 'Delete' : 'Delete (No Permission)'}
          </button>
        )}
      </PermissionRender>

      {/* Tooltip based on permission */}
      <PermissionRender resource="devices" action="activate">
        {(canActivate) => (
          <div className="relative group">
            <button
              onClick={canActivate ? handleActivate : undefined}
              disabled={!canActivate}
            >
              Activate Device
            </button>
            {!canActivate && (
              <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-800 text-white text-sm p-2 rounded">
                You need device activation permission
              </div>
            )}
          </div>
        )}
      </PermissionRender>
    </div>
  );
}

// ============================================================================
// EXAMPLE 7: Resource Gate for Simpler Code
// ============================================================================

/**
 * Using ResourceGate for cleaner code when checking multiple actions on same resource
 */

import { ResourceGate } from '@/components/auth';

export function ResourceGateExample() {
  return (
    <div>
      {/* Show content manager if user can read OR write */}
      <ResourceGate resource="content" actions={['read', 'write']} mode="any">
        <ContentManager />
      </ResourceGate>

      {/* Show advanced editor only if user can BOTH read AND write */}
      <ResourceGate
        resource="content"
        actions={['read', 'write']}
        mode="all"
        fallback={<p>You need full content access to use the advanced editor</p>}
      >
        <AdvancedContentEditor />
      </ResourceGate>

      {/* Show content uploader if user can write */}
      <ResourceGate resource="content" actions={['write']}>
        <ContentUploader />
      </ResourceGate>
    </div>
  );
}

// ============================================================================
// EXAMPLE 8: Navigation Menu with Permission Filtering
// ============================================================================

/**
 * How to filter navigation menu items based on permissions
 */

import { usePermissions } from '@/lib/hooks';

export function NavigationMenuExample() {
  const { can, isAdmin } = usePermissions();

  const menuItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      show: true, // Always show
    },
    {
      label: 'Devices',
      path: '/devices',
      show: can('devices', 'read'),
    },
    {
      label: 'Content',
      path: '/content',
      show: can('content', 'read'),
    },
    {
      label: 'Playlists',
      path: '/playlists',
      show: can('playlists', 'read'),
    },
    {
      label: 'Users',
      path: '/users',
      show: can('users', 'read'),
    },
    {
      label: 'Settings',
      path: '/settings',
      show: isAdmin(), // Admin only
    },
  ];

  return (
    <nav>
      <ul>
        {menuItems
          .filter((item) => item.show)
          .map((item) => (
            <li key={item.path}>
              <a href={item.path}>{item.label}</a>
            </li>
          ))}
      </ul>
    </nav>
  );
}
