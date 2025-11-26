# Permission System Quick Reference Card

**Last Updated**: 2025-11-21

## 🚀 Quick Import Paths

```tsx
// Hooks
import { usePermission, usePermissions, useResourcePermissions } from '@/lib/hooks';

// Components
import { PermissionGate, MultiPermissionGate, AdminGate, ResourceGate, PermissionRender } from '@/components/auth';

// Utils (rarely needed directly)
import { hasPermission, isAdmin } from '@/lib/utils/permissions';
```

---

## 📝 Common Patterns

### Pattern 1: Hide Button if No Permission

```tsx
<PermissionGate resource="devices" action="delete">
  <Button onClick={handleDelete}>Delete</Button>
</PermissionGate>
```

### Pattern 2: Disable Button if No Permission

```tsx
const canDelete = usePermission('devices', 'delete');

<Button disabled={!canDelete}>Delete</Button>
```

### Pattern 3: Check Multiple Permissions (OR)

```tsx
const { canAny } = usePermissions();

if (canAny([
  { resource: 'devices', action: 'write' },
  { resource: 'devices', action: 'delete' }
])) {
  // Show management UI
}
```

### Pattern 4: Check Multiple Permissions (AND)

```tsx
<MultiPermissionGate
  checks={[
    { resource: 'playlists', action: 'write' },
    { resource: 'devices', action: 'assign' }
  ]}
  mode="all"
>
  <AssignPlaylistButton />
</MultiPermissionGate>
```

### Pattern 5: Admin-Only Content

```tsx
<AdminGate>
  <OrganizationSettings />
</AdminGate>
```

### Pattern 6: Resource-Specific Checks

```tsx
const devicePerms = useResourcePermissions('devices');

<Button disabled={!devicePerms.canWrite}>Edit</Button>
<Button disabled={!devicePerms.canDelete}>Delete</Button>
```

---

## 🎯 Resources & Actions

| Resource | Actions |
|----------|---------|
| `devices` | `read`, `write`, `delete`, `activate` |
| `content` | `read`, `write`, `delete` |
| `playlists` | `read`, `write`, `delete`, `assign` |
| `users` | `read`, `write`, `delete` |
| `organizations` | `read`, `write` |
| `widgets` | `read`, `write`, `delete` |
| `templates` | `read`, `write`, `delete` |

---

## 🔧 Hook Reference

### usePermission(resource, action)

**Returns**: `boolean`

```tsx
const canDelete = usePermission('devices', 'delete');
```

### usePermissions()

**Returns**: Object with methods

```tsx
const {
  can,                    // (resource, action) => boolean
  canAny,                 // (checks[]) => boolean
  canAll,                 // (checks[]) => boolean
  isAdmin,                // () => boolean
  getResourcePerms,       // (resource) => string[]
  getAccessibleResources, // () => string[]
  hasAnyPermissions,      // () => boolean
  permissions,            // Record<string, string[]>
  role,                   // string
  user                    // User | null
} = usePermissions();
```

### useResourcePermissions(resource)

**Returns**: Object with boolean flags

```tsx
const {
  canRead,      // boolean
  canWrite,     // boolean
  canDelete,    // boolean
  canAssign,    // boolean
  canActivate,  // boolean
  can,          // (action) => boolean
  actions,      // string[]
  resource      // string
} = useResourcePermissions('devices');
```

---

## 🎨 Component Reference

### PermissionGate

```tsx
<PermissionGate
  resource="devices"
  action="delete"
  fallback={<p>No permission</p>}
>
  <Button>Delete</Button>
</PermissionGate>
```

### MultiPermissionGate

```tsx
<MultiPermissionGate
  checks={[
    { resource: 'devices', action: 'write' },
    { resource: 'devices', action: 'delete' }
  ]}
  mode="any" // or "all"
  fallback={<p>No permission</p>}
>
  <DeviceActions />
</MultiPermissionGate>
```

### AdminGate

```tsx
<AdminGate fallback={<p>Admin only</p>}>
  <AdminPanel />
</AdminGate>
```

### ResourceGate

```tsx
<ResourceGate
  resource="content"
  actions={['read', 'write']}
  mode="all" // or "any"
  fallback={<p>No permission</p>}
>
  <ContentEditor />
</ResourceGate>
```

### PermissionRender

```tsx
<PermissionRender resource="devices" action="delete">
  {(canDelete) => (
    <Button
      disabled={!canDelete}
      title={!canDelete ? 'No permission' : ''}
    >
      Delete
    </Button>
  )}
</PermissionRender>
```

---

## ⚡ Cheat Sheet

| Use Case | Pattern | Code |
|----------|---------|------|
| Hide element | Gate | `<PermissionGate resource="X" action="Y"><Btn /></PermissionGate>` |
| Disable element | Hook | `const can = usePermission('X', 'Y'); <Btn disabled={!can} />` |
| Admin only | AdminGate | `<AdminGate><Component /></AdminGate>` |
| Multiple checks (OR) | canAny | `canAny([{resource: 'X', action: 'Y'}, ...])` |
| Multiple checks (AND) | canAll | `canAll([{resource: 'X', action: 'Y'}, ...])` |
| Resource checks | useResourcePerms | `const perms = useResourcePermissions('devices')` |
| Check if admin | isAdmin | `const { isAdmin } = usePermissions(); if (isAdmin()) { ... }` |
| Navigation filter | can | `menuItems.filter(item => can(item.resource, 'read'))` |

---

## ⚠️ Common Mistakes

### ❌ DON'T: Manually check role
```tsx
if (user.role === 'admin') {
  // Bad - admin check is automatic
}
```

### ✅ DO: Use isAdmin()
```tsx
const { isAdmin } = usePermissions();
if (isAdmin()) {
  // Good - uses built-in admin check
}
```

---

### ❌ DON'T: Assume permission if undefined
```tsx
if (user.permissions?.devices?.includes('delete')) {
  // Bad - fails silently if permissions undefined
}
```

### ✅ DO: Use permission utilities
```tsx
const canDelete = usePermission('devices', 'delete');
// Good - fail-safe by default
```

---

### ❌ DON'T: Nest multiple PermissionGates
```tsx
<PermissionGate resource="content" action="read">
  <PermissionGate resource="content" action="write">
    <Editor />
  </PermissionGate>
</PermissionGate>
```

### ✅ DO: Use ResourceGate or canAll
```tsx
<ResourceGate resource="content" actions={['read', 'write']} mode="all">
  <Editor />
</ResourceGate>
```

---

### ❌ DON'T: Rely on frontend for security
```tsx
// Frontend only - NOT SECURE!
<PermissionGate resource="users" action="delete">
  <DeleteUserButton />
</PermissionGate>
```

### ✅ DO: Validate on backend too
```tsx
// Frontend (UI enforcement)
<PermissionGate resource="users" action="delete">
  <DeleteUserButton />
</PermissionGate>

// Backend (Security enforcement)
@require_permission('users', 'delete')
def delete_user(user_id):
    # Secure deletion
```

---

## 🧪 Testing Snippet

```tsx
import { useAuthStore } from '@/lib/stores/authStore';

// Mock user with permissions
const mockUser = {
  id: 1,
  username: 'test',
  role: 'manager',
  permissions: {
    devices: ['read', 'write'],
    content: ['read']
  }
};

// In test setup
beforeEach(() => {
  useAuthStore.setState({ user: mockUser });
});

// Test permission gate
test('shows delete button for authorized user', () => {
  render(<PermissionGate resource="devices" action="write">
    <button>Delete</button>
  </PermissionGate>);

  expect(screen.getByText('Delete')).toBeInTheDocument();
});
```

---

## 📚 Full Documentation

- **Complete Guide**: `/mnt/g/khoirul/signate/cms-vite/PERMISSION_SYSTEM_IMPLEMENTATION.md`
- **Usage Examples**: `/mnt/g/khoirul/signate/cms-vite/src/components/auth/README.md`
- **Integration Examples**: `/mnt/g/khoirul/signate/cms-vite/src/components/auth/INTEGRATION_EXAMPLES.tsx`

---

**Print this page and keep it handy!** 🎯
