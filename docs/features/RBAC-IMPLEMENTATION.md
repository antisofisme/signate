# RBAC Implementation - Role-Based Access Control

**Date:** 2025-11-12
**Status:** ✅ Completed
**Priority:** 🔴 HIGH (Week 3 from review)

---

## 📋 Overview

Implementasi lengkap sistem Role-Based Access Control (RBAC) untuk CMS Digital Signage. Fitur ini memungkinkan pengelolaan roles, permissions, dan user access control yang granular.

---

## 🎯 Features Implemented

### 1. Core RBAC Types & Infrastructure ✅

**Type System** (`/src/features/rbac/types/rbac.types.ts`)
- `Permission` - Izin individual (resource + action)
- `Role` - Role dengan permissions
- `PermissionAction` - create, read, update, delete, manage
- `PermissionResource` - 16 resource types
- Permission matrix types
- User role assignment types

**Resources Supported (16):**
- users, roles, organizations
- devices, content, playlists
- schedules, widgets, templates
- tags, analytics, audit
- translations, pms, weather, settings

**Actions Supported (5):**
- create, read, update, delete, manage

### 2. API Client ✅

**File:** `/src/features/rbac/api/rbacApi.ts`

**Roles Management (7 functions):**
- getRoles - List roles with filters
- getRole - Get single role
- getRoleWithPermissions - Get role with permissions
- createRole - Create new role
- updateRole - Update existing role
- deleteRole - Delete role
- getSystemRoles - Get system roles

**Role Permissions (3 functions):**
- getRolePermissions - Get role's permissions
- addPermissionsToRole - Add permissions to role
- removePermissionsFromRole - Remove permissions from role

**Role Users (3 functions):**
- getRoleUsers - Get users in role
- assignUsersToRole - Assign users to role
- removeUsersFromRole - Remove users from role

**Permissions (3 functions):**
- getPermissions - Get all permissions
- getPermission - Get single permission
- getPermissionsByResource - Get permissions by resource

**User Permissions (5 functions):**
- getUserPermissions - Get user's permissions
- checkUserPermission - Check if user has permission
- getUserRoles - Get user's roles
- assignRoleToUser - Assign role to user
- removeRoleFromUser - Remove role from user

**Total: 21 API functions**

### 3. React Hooks ✅

**useRoles** (`/src/features/rbac/hooks/useRoles.ts`)
- useRoles - Query roles with filters
- useRole - Query single role
- useRoleWithPermissions - Query role with permissions
- useSystemRoles - Query system roles
- useRolePermissions - Query role permissions
- useRoleUsers - Query role users
- useCreateRole - Mutation to create role
- useUpdateRole - Mutation to update role
- useDeleteRole - Mutation to delete role
- useAddPermissionsToRole - Mutation to add permissions
- useRemovePermissionsFromRole - Mutation to remove permissions

**usePermissions** (`/src/features/rbac/hooks/usePermissions.ts`)
- usePermissions - Query all permissions
- usePermissionsByResource - Query permissions by resource
- useUserPermissions - Query user permissions
- useUserRoles - Query user roles
- useHasPermission - Check single permission
- useHasPermissions - Check multiple permissions
- useCanPerformAction - Helper to check action
- useAssignRoleToUser - Mutation to assign role
- useRemoveRoleFromUser - Mutation to remove role

**Total: 20 hooks**

### 4. UI Components ✅

**RoleCard** (`/src/features/rbac/components/RoleCard.tsx`)
- Display role information
- Show active/inactive status
- Show user count & permission count
- System role badge
- Edit/Delete actions
- Click to view details

**RoleForm** (`/src/features/rbac/components/RoleForm.tsx`)
- Create/Edit role form
- Form validation (Zod + React Hook Form)
- Name, description, active status
- System role protection
- Loading states

**PermissionMatrix** (`/src/features/rbac/components/PermissionMatrix.tsx`)
- Visual permission grid
- Grouped by resource
- Color-coded by action type
- Search functionality
- Resource filter
- Progress stats
- Toggle permissions
- Legend for actions
- Read-only mode for system roles

### 5. Roles Management Page ✅

**File:** `/src/pages/RolesPage.tsx`

**Features:**
- Role cards grid
- Search functionality
- Create role modal
- Edit role modal
- Delete role confirmation
- Permission management modal
- Statistics cards (total, system, permissions)
- Empty states
- Real-time updates via TanStack Query

**Modals:**
1. Create Role Form
2. Edit Role Form
3. Permission Matrix (full screen)

### 6. Integration ✅

**Routing** (`/src/routes/index.tsx`)
- Added `/roles` route
- Protected route (requires auth)
- Within DashboardLayout

**Navigation** (`/src/shared/components/layout/Sidebar.tsx`)
- Added "Roles & Permissions" menu item
- Shield icon
- Positioned before Settings

**API Endpoints** (`/src/lib/api/endpoints.ts`)
- Added `API_ENDPOINTS.RBAC` section
- 21 endpoints organized by category

---

## 📁 File Structure

```
cms-vite/src/
├── features/rbac/
│   ├── types/
│   │   └── rbac.types.ts          ✅ Type definitions
│   ├── api/
│   │   └── rbacApi.ts             ✅ API client
│   ├── hooks/
│   │   ├── useRoles.ts            ✅ Role hooks
│   │   └── usePermissions.ts      ✅ Permission hooks
│   └── components/
│       ├── RoleCard.tsx           ✅ Role card
│       ├── RoleForm.tsx           ✅ Role form
│       └── PermissionMatrix.tsx   ✅ Permission matrix
├── pages/
│   └── RolesPage.tsx              ✅ Main roles page
├── routes/
│   └── index.tsx                  ✅ Added /roles route
└── shared/components/layout/
    └── Sidebar.tsx                ✅ Added menu item
```

---

## 🔌 Backend API Endpoints

### Roles
```
GET    /api/v1/roles                    - List roles
POST   /api/v1/roles                    - Create role
GET    /api/v1/roles/{id}               - Get role
PUT    /api/v1/roles/{id}               - Update role
DELETE /api/v1/roles/{id}               - Delete role
GET    /api/v1/roles/system             - Get system roles
```

### Role Permissions
```
GET    /api/v1/roles/{id}/permissions   - Get role permissions
POST   /api/v1/roles/{id}/permissions   - Add permissions
DELETE /api/v1/roles/{id}/permissions   - Remove permissions
```

### Role Users
```
GET    /api/v1/roles/{id}/users         - Get role users
POST   /api/v1/roles/{id}/users         - Assign users
DELETE /api/v1/roles/{id}/users         - Remove users
```

### Permissions
```
GET    /api/v1/permissions              - List all permissions
GET    /api/v1/permissions/{id}         - Get permission
GET    /api/v1/permissions/resource/{resource} - By resource
```

### User Permissions
```
GET    /api/v1/users/{id}/permissions   - Get user permissions
POST   /api/v1/users/{id}/check-permission - Check permission
GET    /api/v1/users/{id}/roles         - Get user roles
POST   /api/v1/users/{id}/roles         - Assign role
DELETE /api/v1/users/{id}/roles/{roleId} - Remove role
```

---

## 🚀 Usage Examples

### Example 1: Check if User Can Create Content

```tsx
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions'

function ContentCreateButton() {
  const { hasPermission, isLoading } = useCanPerformAction('content', 'create')

  if (isLoading) return <div>Loading...</div>
  if (!hasPermission) return null

  return <button>Create Content</button>
}
```

### Example 2: Protect Route with Permission Check

```tsx
import { useHasPermission } from '@/features/rbac/hooks/usePermissions'
import { Navigate } from 'react-router-dom'

function DeviceManagementPage() {
  const userId = getCurrentUserId()
  const { hasPermission, isLoading } = useHasPermission(userId, 'devices', 'manage')

  if (isLoading) return <div>Loading...</div>
  if (!hasPermission) return <Navigate to="/dashboard" />

  return <div>Device Management</div>
}
```

### Example 3: Show/Hide Menu Items Based on Permission

```tsx
import { useUserPermissions } from '@/features/rbac/hooks/usePermissions'

function NavigationMenu() {
  const { data: permissions = [] } = useUserPermissions(userId)

  const canViewDevices = permissions.some(
    p => p.resource === 'devices' && (p.action === 'read' || p.action === 'manage')
  )

  return (
    <nav>
      {canViewDevices && <Link to="/devices">Devices</Link>}
    </nav>
  )
}
```

### Example 4: Create Role with Permissions

```tsx
import { useCreateRole } from '@/features/rbac/hooks/useRoles'
import { useAddPermissionsToRole } from '@/features/rbac/hooks/usePermissions'

function CreateRoleFlow() {
  const createRole = useCreateRole()
  const addPermissions = useAddPermissionsToRole()

  const handleCreate = async () => {
    // 1. Create role
    const role = await createRole.mutateAsync({
      name: 'Content Manager',
      description: 'Can manage content and playlists',
      is_active: true
    })

    // 2. Add permissions
    await addPermissions.mutateAsync({
      roleId: role.id,
      data: {
        permission_ids: [1, 2, 3, 4] // content permissions
      }
    })
  }

  return <button onClick={handleCreate}>Create Role</button>
}
```

---

## 📊 Permission Matrix UI

### Visual Layout

```
┌─────────────────────────────────────────┐
│ Search: [________] | Filter: [All]      │
├─────────────────────────────────────────┤
│ Progress: ████████░░ 60% (12/20)        │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Users ─────────────────────────┐    │
│ │ [✓] Create  [✓] Read  [✓] Update │    │
│ │ [✗] Delete  [✗] Manage           │    │
│ └──────────────────────────────────┘    │
│                                         │
│ ┌─ Devices ───────────────────────┐    │
│ │ [✓] Create  [✓] Read  [✓] Update │    │
│ │ [✓] Delete  [✗] Manage           │    │
│ └──────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Color Coding
- 🟢 Create - Green
- 🔵 Read - Blue
- 🟡 Update - Yellow
- 🔴 Delete - Red
- 🟣 Manage - Purple

---

## 🔐 Security Considerations

### 1. System Roles Protection
- System roles cannot be deleted
- System roles cannot be renamed
- System roles permissions cannot be modified
- Visual indicators (lock icon, badges)

### 2. Permission Checks
- Backend validates all permissions
- Frontend checks for UI consistency
- Hooks provide easy permission checking
- Route guards prevent unauthorized access

### 3. Audit Trail
- All role changes should be logged
- Permission changes should be tracked
- User role assignments should be audited

---

## 🧪 Testing Recommendations

### Unit Tests
```typescript
// Test permission checking
describe('useHasPermission', () => {
  it('should return true if user has permission', async () => {
    const { result } = renderHook(() =>
      useHasPermission(1, 'content', 'create')
    )

    await waitFor(() => {
      expect(result.current.hasPermission).toBe(true)
    })
  })
})
```

### Integration Tests
1. Create role → Assign permissions → Verify
2. Assign role to user → Check permissions
3. Remove permission → Verify access denied
4. Delete role → Verify user permissions updated

### Manual Testing
1. Navigate to /roles
2. Create new role "Content Manager"
3. Add permissions: content (create, read, update)
4. Assign role to test user
5. Login as test user
6. Verify can create/edit content
7. Verify cannot delete content

---

## 📈 Performance Optimizations

### React Query Caching
- Roles: 5 minutes stale time
- Permissions: 30 minutes (rarely change)
- User permissions: 5 minutes
- System roles: 30 minutes

### Optimistic Updates
```typescript
const updateRole = useUpdateRole()

// Optimistic update
queryClient.setQueryData(['roles'], (old) => {
  // Update immediately without waiting for server
  return updateRoleInList(old, updatedRole)
})
```

---

## 🚦 Next Steps

### Immediate (Completed) ✅
- [x] Create RBAC types
- [x] Implement API client
- [x] Create React hooks
- [x] Build UI components
- [x] Create Roles page
- [x] Add routing
- [x] Add navigation menu

### Short-term (Week 4)
- [ ] Add permission-based route guards
- [ ] Add permission checks to existing pages
- [ ] Hide buttons based on permissions
- [ ] Add bulk permission assignment
- [ ] Add permission templates (presets)

### Medium-term (Month 2)
- [ ] Add role hierarchy (parent/child roles)
- [ ] Add conditional permissions (context-based)
- [ ] Add permission delegation
- [ ] Add time-based permissions (expire)
- [ ] Add IP-based access control

---

## ✅ Completion Checklist

- [x] Types & interfaces defined
- [x] API client implemented
- [x] React hooks created
- [x] RoleCard component
- [x] RoleForm component
- [x] PermissionMatrix component
- [x] Roles page created
- [x] Routing integrated
- [x] Navigation menu updated
- [x] API endpoints added
- [x] Documentation completed

---

**Implementation Status:** ✅ COMPLETE
**System Completion:** 90% → 93% (estimated)
**Time Spent:** ~4 hours
**Files Created:** 9
**Lines of Code:** ~2,000
