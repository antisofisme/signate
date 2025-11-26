# Permission System Migration Guide

**Date**: 2025-11-21

## Overview

This document explains the **THREE** permission systems in the codebase and how they work together.

---

## 🔍 Understanding the Three Systems

### System 1: Old Role-Based Permissions (DEPRECATED)

**Location**: `/src/lib/auth/permissions.ts`

**Pattern**: Simple role checks

**Usage**:
```tsx
import { isAdmin, canPerformAction } from '@/lib/auth/permissions';

if (isAdmin(user)) {
  // Admin only
}

if (canPerformAction(user, 'device.delete')) {
  // Can delete device
}
```

**Status**: ⚠️ **DEPRECATED** - Should be replaced with new system

**Limitations**:
- Hardcoded permissions per role
- No granular control from backend
- Not synced with backend RBAC system

---

### System 2: RBAC API Hooks (For Management UI)

**Location**: `/src/features/rbac/hooks/usePermissions.ts`

**Pattern**: React Query hooks for RBAC management

**Usage**:
```tsx
import { useUserPermissions, useHasPermission } from '@/features/rbac/hooks/usePermissions';

// Get user's permissions from API
const { data: permissions } = useUserPermissions(userId);

// Check specific permission
const { hasPermission } = useHasPermission(userId, 'devices', 'delete');
```

**Purpose**:
- **RBAC management pages** (admin editing roles/permissions)
- Fetches permission data from backend API
- Used in Role Management UI

**When to Use**:
- Building RBAC admin interface
- Managing roles and permissions
- Viewing user permissions
- Assigning/removing roles

**NOT for**: Regular UI permission checks (too slow - requires API call)

---

### System 3: New Client-Side Permission Checks (RECOMMENDED)

**Location**:
- `/src/lib/hooks/usePermission.ts` (hooks)
- `/src/components/auth/PermissionGate.tsx` (components)
- `/src/lib/utils/permissions.ts` (utilities)

**Pattern**: Client-side permission checks using auth store

**Usage**:
```tsx
import { usePermission, usePermissions } from '@/lib/hooks';
import { PermissionGate } from '@/components/auth';

// Hook - single check
const canDelete = usePermission('devices', 'delete');

// Hook - multiple methods
const { can, canAny, isAdmin } = usePermissions();

// Component - conditional render
<PermissionGate resource="devices" action="delete">
  <DeleteButton />
</PermissionGate>
```

**Purpose**:
- **Regular UI permission checks** (fast, synchronous)
- Uses permissions from auth store (already loaded)
- No API calls needed
- Optimized for component rendering

**When to Use**:
- Hiding/showing UI elements
- Enabling/disabling buttons
- Conditional rendering
- Navigation filtering
- **ANY permission check in regular components**

---

## 📊 Comparison Matrix

| Feature | Old System (Deprecated) | RBAC API Hooks | New Client System |
|---------|------------------------|----------------|-------------------|
| **Location** | `/lib/auth/permissions.ts` | `/features/rbac/hooks` | `/lib/hooks/usePermission.ts` |
| **Data Source** | Hardcoded | Backend API | Auth Store |
| **Performance** | Fast | Slow (API call) | Fast (in-memory) |
| **Use Case** | ❌ Deprecated | RBAC Management UI | Regular UI checks |
| **Granularity** | Role-based only | Fine-grained | Fine-grained |
| **Synced with Backend** | ❌ No | ✅ Yes | ✅ Yes (via login) |
| **Admin Override** | ✅ Yes | ❌ Manual | ✅ Yes (automatic) |
| **TypeScript** | Partial | Full | Full |
| **Status** | ⚠️ Deprecated | ✅ Active | ⭐ Recommended |

---

## 🔄 Migration Path

### Phase 1: Update Login Response (Backend)

**Required**: Backend must include `permissions` in login response

```python
# backend-python/services/auth/routes.py

@router.post("/login")
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)

    # Get user's role and permissions
    role = get_user_role(user.id)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,  # Keep for backward compatibility
            "role_id": role.id,
            "role_name": role.name,
            "permissions": role.permissions  # NEW - Add this!
        },
        "token": generate_token(user)
    }
```

**Example Response**:
```json
{
  "user": {
    "id": 1,
    "username": "john",
    "role": "manager",
    "role_id": 2,
    "role_name": "Content Manager",
    "permissions": {
      "devices": ["read", "write"],
      "content": ["read", "write", "delete"],
      "playlists": ["read"]
    }
  },
  "token": "eyJ..."
}
```

---

### Phase 2: Replace Old Permission Checks (Frontend)

**Find and Replace**: Gradually migrate from old system to new

#### Example 1: isAdmin() Migration

**Before** (Old System):
```tsx
import { isAdmin } from '@/lib/auth/permissions';

if (isAdmin(user)) {
  return <AdminPanel />;
}
```

**After** (New System):
```tsx
import { AdminGate } from '@/components/auth';

<AdminGate>
  <AdminPanel />
</AdminGate>

// Or with hook:
import { usePermissions } from '@/lib/hooks';
const { isAdmin } = usePermissions();

if (isAdmin()) {
  return <AdminPanel />;
}
```

---

#### Example 2: canPerformAction() Migration

**Before** (Old System):
```tsx
import { canPerformAction, PERMISSIONS } from '@/lib/auth/permissions';

if (canPerformAction(user, PERMISSIONS.DEVICE.DELETE)) {
  return <DeleteButton />;
}
```

**After** (New System):
```tsx
import { PermissionGate } from '@/components/auth';

<PermissionGate resource="devices" action="delete">
  <DeleteButton />
</PermissionGate>

// Or with hook:
import { usePermission } from '@/lib/hooks';
const canDelete = usePermission('devices', 'delete');

if (canDelete) {
  return <DeleteButton />;
}
```

---

#### Example 3: hasRole() Migration

**Before** (Old System):
```tsx
import { hasRole, USER_ROLES } from '@/lib/auth/permissions';

if (hasRole(user, USER_ROLES.MANAGER)) {
  // Manager features
}
```

**After** (New System):
```tsx
import { usePermissions } from '@/lib/hooks';

const { role } = usePermissions();

if (role === 'manager') {
  // Manager features
}

// Better: Check specific permission instead of role
const { can } = usePermissions();

if (can('content', 'write')) {
  // Features that require content write
}
```

---

### Phase 3: Keep RBAC API Hooks for Management UI

**DO NOT REPLACE** these hooks - they're for different use case!

**Keep Using** for RBAC Management Pages:
```tsx
// src/features/rbac/pages/RoleManagement.tsx
import { useUserPermissions, useAssignRoleToUser } from '@/features/rbac/hooks/usePermissions';

function RoleManagementPage() {
  // This is correct - we need to fetch from API to manage roles
  const { data: userPermissions } = useUserPermissions(selectedUserId);
  const assignRoleMutation = useAssignRoleToUser();

  // Render role management UI
}
```

**Use New System** for UI Permission Checks:
```tsx
// src/features/rbac/pages/RoleManagement.tsx
import { PermissionGate } from '@/components/auth';

function RoleManagementPage() {
  // Check if current user can manage roles
  return (
    <PermissionGate resource="users" action="write">
      <RoleManagementUI />
    </PermissionGate>
  );
}
```

---

## 📝 Detailed Migration Examples

### Example 1: ContentTable Component

**Before** (Old System):
```tsx
import { canPerformAction, PERMISSIONS } from '@/lib/auth/permissions';
import { useAuthStore } from '@/lib/stores/authStore';

function ContentTable() {
  const user = useAuthStore(state => state.user);
  const canUpload = canPerformAction(user, PERMISSIONS.CONTENT.CREATE);
  const canDelete = canPerformAction(user, PERMISSIONS.CONTENT.DELETE);

  return (
    <div>
      {canUpload && (
        <Button onClick={handleUpload}>Upload</Button>
      )}

      {canDelete && (
        <Button onClick={handleDelete}>Delete</Button>
      )}
    </div>
  );
}
```

**After** (New System):
```tsx
import { PermissionGate } from '@/components/auth';

function ContentTable() {
  return (
    <div>
      <PermissionGate resource="content" action="write">
        <Button onClick={handleUpload}>Upload</Button>
      </PermissionGate>

      <PermissionGate resource="content" action="delete">
        <Button onClick={handleDelete}>Delete</Button>
      </PermissionGate>
    </div>
  );
}
```

---

### Example 2: Navigation Menu

**Before** (Old System):
```tsx
import { isAdminOrAbove, isManagerOrAbove } from '@/lib/auth/permissions';

function Navigation() {
  const user = useAuthStore(state => state.user);

  return (
    <nav>
      <Link to="/dashboard">Dashboard</Link>

      {isManagerOrAbove(user) && (
        <Link to="/content">Content</Link>
      )}

      {isAdminOrAbove(user) && (
        <Link to="/users">Users</Link>
      )}
    </nav>
  );
}
```

**After** (New System):
```tsx
import { usePermissions } from '@/lib/hooks';

function Navigation() {
  const { can, isAdmin } = usePermissions();

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard', show: true },
    { label: 'Content', path: '/content', show: can('content', 'read') },
    { label: 'Users', path: '/users', show: isAdmin() },
  ];

  return (
    <nav>
      {menuItems
        .filter(item => item.show)
        .map(item => (
          <Link key={item.path} to={item.path}>
            {item.label}
          </Link>
        ))}
    </nav>
  );
}
```

---

## 🎯 Decision Tree: Which System to Use?

```
Are you building RBAC management UI? (Role/Permission CRUD)
├─ YES → Use RBAC API Hooks (System 2)
│         import { useUserPermissions } from '@/features/rbac/hooks/usePermissions'
│
└─ NO → Are you checking permissions in regular components?
    ├─ YES → Use New Client System (System 3) ⭐ RECOMMENDED
    │         import { usePermission, PermissionGate } from '@/lib/hooks'
    │
    └─ NO → Are you using old role-based checks?
        └─ YES → Migrate to New Client System (System 3)
                  Old system is DEPRECATED
```

---

## ⚠️ Common Mistakes

### Mistake 1: Using API Hooks for UI Checks

❌ **DON'T**:
```tsx
import { useHasPermission } from '@/features/rbac/hooks/usePermissions';

function DeleteButton() {
  // This makes an API call every render - TOO SLOW!
  const { hasPermission } = useHasPermission(userId, 'devices', 'delete');

  return <Button disabled={!hasPermission}>Delete</Button>;
}
```

✅ **DO**:
```tsx
import { usePermission } from '@/lib/hooks';

function DeleteButton() {
  // This uses auth store - FAST!
  const canDelete = usePermission('devices', 'delete');

  return <Button disabled={!canDelete}>Delete</Button>;
}
```

---

### Mistake 2: Mixing Old and New Systems

❌ **DON'T**:
```tsx
import { isAdmin } from '@/lib/auth/permissions'; // Old
import { usePermission } from '@/lib/hooks'; // New

if (isAdmin(user) || usePermission('devices', 'delete')) {
  // Mixing systems - confusing!
}
```

✅ **DO**:
```tsx
import { usePermissions } from '@/lib/hooks'; // New only

const { isAdmin, can } = usePermissions();

if (isAdmin() || can('devices', 'delete')) {
  // Consistent system
}
```

---

### Mistake 3: Not Checking Backend Permissions

❌ **DON'T** (Frontend only):
```tsx
// Frontend
<PermissionGate resource="users" action="delete">
  <DeleteUserButton />
</PermissionGate>

// Backend - NO PERMISSION CHECK!
@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    # Anyone can call this endpoint! 🚨 SECURITY RISK
    delete_user_from_db(user_id)
```

✅ **DO** (Frontend + Backend):
```tsx
// Frontend
<PermissionGate resource="users" action="delete">
  <DeleteUserButton />
</PermissionGate>

// Backend - WITH PERMISSION CHECK
@router.delete("/users/{user_id}")
@require_permission('users', 'delete')  # Backend validation!
def delete_user(user_id: int):
    delete_user_from_db(user_id)
```

---

## 🧪 Testing During Migration

### 1. Test Both Systems Work (Transition Period)

```tsx
import { canPerformAction, PERMISSIONS } from '@/lib/auth/permissions'; // Old
import { usePermission } from '@/lib/hooks'; // New

function ComponentUnderMigration() {
  const user = useAuthStore(state => state.user);

  // Old way
  const canDeleteOld = canPerformAction(user, PERMISSIONS.DEVICE.DELETE);

  // New way
  const canDeleteNew = usePermission('devices', 'delete');

  // Verify they match during transition
  if (canDeleteOld !== canDeleteNew) {
    console.warn('Permission mismatch detected!', {
      old: canDeleteOld,
      new: canDeleteNew,
    });
  }

  // Use new system
  return (
    <Button disabled={!canDeleteNew}>Delete</Button>
  );
}
```

### 2. Test Admin Override

```tsx
test('admin users have all permissions', () => {
  useAuthStore.setState({
    user: {
      id: 1,
      role: 'admin',
      permissions: {} // Empty - but admin should still have access
    }
  });

  const { result } = renderHook(() => usePermission('devices', 'delete'));

  expect(result.current).toBe(true); // Admin override works
});
```

---

## 📋 Migration Checklist

### Backend Tasks
- [ ] Update login endpoint to include `permissions` field
- [ ] Ensure role.permissions is correctly populated from database
- [ ] Test login response includes permissions object
- [ ] Verify admin role has all permissions

### Frontend Tasks
- [ ] Install new permission system (already done ✅)
- [ ] Update auth types to include `permissions` field (already done ✅)
- [ ] Test login stores permissions in auth store
- [ ] Migrate high-priority components (ContentTable, DeviceTable)
- [ ] Migrate navigation menu
- [ ] Migrate admin-only sections
- [ ] Remove old permission imports from migrated files
- [ ] Update tests for migrated components

### Testing Tasks
- [ ] Test as admin user - verify all features visible
- [ ] Test as manager - verify restricted access
- [ ] Test as viewer - verify read-only access
- [ ] Test permission gates hide/show correctly
- [ ] Test disabled states show tooltips
- [ ] Verify backend still validates permissions
- [ ] Check browser console for errors

### Documentation Tasks
- [ ] Document new permission system for team
- [ ] Update component examples in Storybook
- [ ] Add migration guide to team wiki
- [ ] Schedule team training session

---

## 🚀 Summary

**Three Systems, Three Purposes:**

1. **Old System** (`/lib/auth/permissions.ts`) → ⚠️ DEPRECATED, migrate away
2. **RBAC API Hooks** (`/features/rbac/hooks`) → ✅ Keep for RBAC management UI
3. **New Client System** (`/lib/hooks/usePermission.ts`) → ⭐ Use for all UI permission checks

**Migration Priority:**
1. Backend adds `permissions` to login response
2. Replace old role checks with new permission checks
3. Test thoroughly
4. Keep RBAC API hooks for management pages

**Result:**
- Faster UI permission checks (no API calls)
- Fine-grained access control from backend
- Consistent permission system across app
- Better UX with proper disabled states and tooltips

---

**Questions?** See:
- Full implementation: `/PERMISSION_SYSTEM_IMPLEMENTATION.md`
- Quick reference: `/PERMISSION_QUICK_REFERENCE.md`
- Examples: `/src/components/auth/README.md`
