# Permission System Usage Examples

This directory contains the RBAC permission checking system for the CMS.

## Quick Start

### 1. Single Permission Check (Hook)

```tsx
import { usePermission } from '@/lib/hooks';

function DeviceActions() {
  const canDelete = usePermission('devices', 'delete');

  return (
    <Button
      onClick={handleDelete}
      disabled={!canDelete}
      title={!canDelete ? 'You do not have permission to delete devices' : ''}
    >
      Delete Device
    </Button>
  );
}
```

### 2. Hide Component if No Permission (Gate)

```tsx
import { PermissionGate } from '@/components/auth';

function DeviceTable() {
  return (
    <>
      {/* Show upload button only if user can write content */}
      <PermissionGate resource="content" action="write">
        <Button onClick={() => setShowUploadModal(true)}>
          Upload Content
        </Button>
      </PermissionGate>

      {/* Show delete button only if user can delete */}
      <PermissionGate resource="devices" action="delete">
        <Button onClick={handleDelete}>Delete Device</Button>
      </PermissionGate>
    </>
  );
}
```

### 3. Multiple Permission Checks

```tsx
import { usePermissions } from '@/lib/hooks';

function ContentManager() {
  const { can, canAny, canAll, isAdmin } = usePermissions();

  // Single check
  if (can('content', 'write')) {
    // Show upload form
  }

  // Check if user has ANY permission (OR logic)
  const canManageContent = canAny([
    { resource: 'content', action: 'write' },
    { resource: 'content', action: 'delete' }
  ]);

  // Check if user has ALL permissions (AND logic)
  const canFullyManage = canAll([
    { resource: 'content', action: 'read' },
    { resource: 'content', action: 'write' },
    { resource: 'content', action: 'delete' }
  ]);

  // Admin check
  if (isAdmin()) {
    // Show admin-only features
  }
}
```

### 4. Resource-Specific Permissions

```tsx
import { useResourcePermissions } from '@/lib/hooks';

function DeviceDetails() {
  const devicePerms = useResourcePermissions('devices');

  return (
    <div>
      {devicePerms.canRead && <DeviceInfo />}

      <Button disabled={!devicePerms.canWrite}>Edit</Button>
      <Button disabled={!devicePerms.canDelete}>Delete</Button>

      {devicePerms.can('activate') && (
        <Button>Activate Device</Button>
      )}
    </div>
  );
}
```

### 5. Multi-Permission Gate

```tsx
import { MultiPermissionGate } from '@/components/auth';

function AdminPanel() {
  return (
    {/* Show if user can EITHER write OR delete organizations */}
    <MultiPermissionGate
      checks={[
        { resource: 'organizations', action: 'write' },
        { resource: 'organizations', action: 'delete' }
      ]}
      mode="any"
      fallback={<p>You need organization management permissions</p>}
    >
      <OrganizationSettings />
    </MultiPermissionGate>
  );
}
```

### 6. Admin-Only Gate

```tsx
import { AdminGate } from '@/components/auth';

function Settings() {
  return (
    <>
      <UserSettings /> {/* Everyone can see */}

      <AdminGate fallback={<p>Admin access required</p>}>
        <SystemSettings /> {/* Only admins */}
      </AdminGate>
    </>
  );
}
```

### 7. Resource Gate (Multiple Actions on Same Resource)

```tsx
import { ResourceGate } from '@/components/auth';

function ContentUpload() {
  return (
    {/* Show if user can read OR write content */}
    <ResourceGate resource="content" actions={['read', 'write']} mode="any">
      <ContentList />
    </ResourceGate>

    {/* Show only if user can both read AND write */}
    <ResourceGate resource="content" actions={['read', 'write']} mode="all">
      <ContentUploadForm />
    </ResourceGate>
  );
}
```

### 8. Render Props Pattern

```tsx
import { PermissionRender } from '@/components/auth';

function ContentActions() {
  return (
    <PermissionRender resource="content" action="delete">
      {(canDelete) => (
        <Button
          onClick={handleDelete}
          disabled={!canDelete}
          className={!canDelete ? 'opacity-50 cursor-not-allowed' : ''}
          title={!canDelete ? 'No permission to delete content' : 'Delete content'}
        >
          {canDelete ? 'Delete' : 'Delete (No Permission)'}
        </Button>
      )}
    </PermissionRender>
  );
}
```

## Real-World Integration Examples

### Example 1: ContentTable with Permission Gates

```tsx
// src/features/contents/components/ContentTable.tsx
import { PermissionGate } from '@/components/auth';
import { useResourcePermissions } from '@/lib/hooks';

export function ContentTable() {
  const contentPerms = useResourcePermissions('content');

  return (
    <div>
      {/* Header with Upload button */}
      <div className="flex justify-between">
        <h2>Content Library</h2>

        {/* Only show upload if user can write */}
        <PermissionGate resource="content" action="write">
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload /> Upload Content
          </Button>
        </PermissionGate>
      </div>

      {/* Table Actions */}
      <table>
        {/* ... table rows ... */}
        <td>
          <div className="flex gap-2">
            {/* Edit - requires write permission */}
            <PermissionGate resource="content" action="write">
              <button onClick={() => handleEdit(content)}>
                <Edit />
              </button>
            </PermissionGate>

            {/* Delete - requires delete permission */}
            <PermissionGate resource="content" action="delete">
              <button onClick={() => handleDelete(content)}>
                <Trash2 />
              </button>
            </PermissionGate>

            {/* Preview - always available if user can read */}
            {contentPerms.canRead && (
              <button onClick={() => handlePreview(content)}>
                <Eye />
              </button>
            )}
          </div>
        </td>
      </table>
    </div>
  );
}
```

### Example 2: DeviceTable with Permission Checks

```tsx
// src/features/devices/components/DeviceTable.tsx
import { usePermissions } from '@/lib/hooks';
import { PermissionGate } from '@/components/auth';

export function DeviceTable() {
  const { can, canAny } = usePermissions();

  // Check if user can manage devices at all
  const canManageDevices = canAny([
    { resource: 'devices', action: 'write' },
    { resource: 'devices', action: 'delete' },
    { resource: 'devices', action: 'activate' }
  ]);

  if (!can('devices', 'read')) {
    return <p>You don't have permission to view devices</p>;
  }

  return (
    <div>
      {/* Bulk Actions - only if user can manage */}
      {canManageDevices && (
        <div className="flex gap-2">
          <PermissionGate resource="devices" action="activate">
            <Button onClick={handleBulkActivate}>Activate Selected</Button>
          </PermissionGate>

          <PermissionGate resource="devices" action="delete">
            <Button onClick={handleBulkDelete}>Delete Selected</Button>
          </PermissionGate>
        </div>
      )}

      {/* Device rows with action buttons */}
      <table>
        {/* ... */}
        <td>
          <PermissionGate resource="devices" action="write">
            <button onClick={() => handleEdit(device)}>Edit</button>
          </PermissionGate>

          <PermissionGate resource="devices" action="delete">
            <button onClick={() => handleDelete(device)}>Delete</button>
          </PermissionGate>
        </td>
      </table>
    </div>
  );
}
```

### Example 3: Playlist Builder

```tsx
// src/features/playlists/components/PlaylistBuilder.tsx
import { AdminGate, ResourceGate } from '@/components/auth';
import { usePermissions } from '@/lib/hooks';

export function PlaylistBuilder() {
  const { can, isAdmin } = usePermissions();

  return (
    <div>
      {/* Create Playlist - requires write permission */}
      <ResourceGate resource="playlists" actions={['write']}>
        <Button onClick={handleCreatePlaylist}>
          Create New Playlist
        </Button>
      </ResourceGate>

      {/* Advanced Features - admin only */}
      <AdminGate>
        <div>
          <h3>Advanced Playlist Settings</h3>
          <PlaylistTemplates />
          <GlobalScheduling />
        </div>
      </AdminGate>

      {/* Delete Playlist - requires delete permission */}
      {can('playlists', 'delete') && (
        <Button onClick={handleDelete} variant="destructive">
          Delete Playlist
        </Button>
      )}
    </div>
  );
}
```

## Permission Resources & Actions

### Available Resources
- `devices` - Device management
- `content` - Media content (images, videos, audio)
- `playlists` - Playlist management
- `users` - User management
- `organizations` - Organization settings
- `widgets` - Widget/template management
- `templates` - Template management

### Available Actions
- `read` - View/list resources
- `write` - Create/edit resources
- `delete` - Delete resources
- `assign` - Assign resources (e.g., assign playlist to device)
- `activate` - Activate resources (e.g., activate device)

## Best Practices

1. **Always use permission checks for destructive actions** (delete, edit)
2. **Admin users have all permissions automatically** (no need to check)
3. **Fail-safe by default** - If permissions undefined, deny access
4. **Use PermissionGate for hiding UI elements**
5. **Use hooks for disabling buttons** (better UX than hiding)
6. **Server-side validation is still required** - This is UI enforcement only
7. **Use ResourceGate for resource-specific components** (cleaner code)
8. **Combine multiple checks with canAny/canAll** for complex logic

## TypeScript Support

All permission functions and components are fully typed:

```tsx
// Type-safe resource and action strings
const canDelete: boolean = usePermission('devices', 'delete');

// Type-safe permission checks array
const checks: Array<{ resource: string; action: string }> = [
  { resource: 'devices', action: 'read' },
  { resource: 'devices', action: 'write' }
];

// Fully typed hook return
const {
  can,      // (resource: string, action: string) => boolean
  canAny,   // (checks: Array<{resource, action}>) => boolean
  canAll,   // (checks: Array<{resource, action}>) => boolean
  isAdmin,  // () => boolean
  permissions, // Record<string, string[]>
} = usePermissions();
```

## Testing Permissions

### 1. Mock User with Permissions

```tsx
// Test setup
const mockUser = {
  id: 1,
  username: 'test-user',
  role: 'user',
  permissions: {
    devices: ['read', 'write'],
    content: ['read']
  }
};

// In tests
import { useAuthStore } from '@/lib/stores/authStore';

beforeEach(() => {
  useAuthStore.setState({ user: mockUser });
});
```

### 2. Test Permission Gates

```tsx
import { render, screen } from '@testing-library/react';
import { PermissionGate } from '@/components/auth';

test('shows content when user has permission', () => {
  render(
    <PermissionGate resource="devices" action="read">
      <div>Device List</div>
    </PermissionGate>
  );

  expect(screen.getByText('Device List')).toBeInTheDocument();
});

test('hides content when user lacks permission', () => {
  render(
    <PermissionGate resource="devices" action="delete">
      <div>Delete Button</div>
    </PermissionGate>
  );

  expect(screen.queryByText('Delete Button')).not.toBeInTheDocument();
});
```

## Troubleshooting

**Q: Permission gate not working?**
- Check if user object in auth store has `permissions` field
- Check if backend is sending permissions in login response
- Check browser console for permission check errors

**Q: Admin user shows no access?**
- Ensure `user.role === 'admin'` (lowercase)
- Admin override is built into all permission checks

**Q: How to update permissions without re-login?**
```tsx
import { useAuthStore } from '@/lib/stores/authStore';

// Update user permissions
useAuthStore.getState().updateUser({
  permissions: newPermissionsObject
});
```

**Q: How to check permissions in API calls?**
```tsx
// Permission checks are UI-only
// Backend MUST validate permissions on every endpoint
// Don't rely on frontend permission checks for security
```
