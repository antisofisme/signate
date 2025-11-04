# TODO: Phase 3 - User & Organization Management

**Status:** 🔴 PLANNING ONLY (DO NOT IMPLEMENT YET)
**Priority:** ⭐⭐⭐ HIGH (After refactoring Phase 2)
**Estimated Time:** 3-5 days
**Dependencies:** Must complete `TODO_REFACTORING.md` first

---

## 📋 Overview

Implement User & Organization Management as foundation for multi-tenant system.

**Why Priority 1?**
- ✅ Blocks all other features (Content, Playlist need org context)
- ✅ Database schema already 80% ready
- ✅ RBAC utilities already created (`lib/auth/permissions.ts`)
- ✅ Foundation for proper multi-tenancy

---

## 🎯 Backend Tasks (FastAPI)

### 1. Organization CRUD API

**File:** `backend-python/services/organization/routes.py` (NEW)

**Endpoints:**
- [ ] `GET /api/v1/organizations` - List all orgs (admin only)
  - Filters: search, status
  - Pagination
  - Returns: id, name, pin, created_at, user_count, device_count

- [ ] `GET /api/v1/organizations/{id}` - Get org details
  - Permission: admin or manager of that org
  - Returns: full org info + stats

- [ ] `POST /api/v1/organizations` - Create new organization
  - Permission: admin only
  - Body: { name, pin (optional - auto-generate if empty) }
  - Validation: name unique, pin 4-6 digits
  - Returns: created org with pin

- [ ] `PUT /api/v1/organizations/{id}` - Update organization
  - Permission: admin only
  - Body: { name }
  - Returns: updated org

- [ ] `DELETE /api/v1/organizations/{id}` - Delete organization
  - Permission: admin only
  - Soft delete (set deleted_at)
  - Check: prevent delete if has users/devices
  - Returns: success message

**Use centralized utilities:**
```python
from shared.errors import ValidationError, NotFoundError, PermissionDenied
from shared.responses import success_response, error_response, paginated_response
from shared.validators import validate_pin, sanitize_string
from shared.logging import AuditLogger
```

---

### 2. User Management API

**File:** `backend-python/services/user/routes.py` (NEW)

**Endpoints:**
- [ ] `GET /api/v1/users` - List users
  - Permission: admin (all orgs) or manager (own org only)
  - Filters: organization_id, role, search, status
  - Pagination
  - Returns: id, username, email, full_name, role, organization_name, last_login, is_active

- [ ] `GET /api/v1/users/{id}` - Get user details
  - Permission: admin or manager (same org)
  - Returns: full user info

- [ ] `POST /api/v1/users` - Create/invite user
  - Permission: admin (any org) or manager (own org only)
  - Body: { username, email, full_name, password, role, organization_id }
  - Validation: username unique, email format, password strength, role valid
  - Auto-send: invitation email (future)
  - Returns: created user (without password)

- [ ] `PUT /api/v1/users/{id}` - Update user
  - Permission: admin or manager (same org)
  - Body: { email, full_name, role, is_active }
  - Validation: cannot change own role, cannot demote last admin
  - Returns: updated user

- [ ] `PUT /api/v1/users/{id}/change-password` - Change user password
  - Permission: self or admin
  - Body: { old_password (if self), new_password }
  - Validation: password strength
  - Returns: success message

- [ ] `PUT /api/v1/users/{id}/change-organization` - Move user to another org
  - Permission: admin only
  - Body: { organization_id }
  - Returns: updated user

- [ ] `DELETE /api/v1/users/{id}` - Deactivate user
  - Permission: admin or manager (same org)
  - Soft delete (set is_active = false)
  - Prevent: cannot deactivate self, cannot deactivate last admin
  - Returns: success message

**Audit logging:**
```python
# Log all user management actions
audit_logger.log_action(
    user_id=current_user.id,
    action="user.created",
    resource_type="user",
    resource_id=new_user.id,
    details={"username": new_user.username, "role": new_user.role}
)
```

---

### 3. Permission Middleware

**File:** `backend-python/shared/permissions.py` (NEW)

**Decorators:**
- [ ] `@require_permission("user.view")` - Check if user has permission
- [ ] `@require_role("admin")` - Check if user has role
- [ ] `@require_same_org()` - Check if resource belongs to user's org
- [ ] `@admin_only()` - Shortcut for admin check

**Example:**
```python
@router.get("/users")
@require_permission("user.view")
async def list_users(current_user: User = Depends(get_current_user)):
    # Only users with "user.view" permission can access
    ...
```

---

### 4. Database Migrations (if needed)

**Check if schema needs updates:**
- [ ] Review `users` table - ensure organization_id FK exists
- [ ] Review `organizations` table - ensure all fields exist
- [ ] Add index on `users.organization_id` for performance
- [ ] Add index on `organizations.pin` for lookup

---

## 🎯 Frontend Tasks (React + Vite)

### 1. Organization Management Feature

**Files to create:**
```
features/organizations/
├── components/
│   ├── OrganizationTable.tsx       - List orgs with search/filter
│   ├── OrganizationModal.tsx       - Create/Edit org form
│   ├── OrganizationCard.tsx        - Org info card (stats)
│   └── DeleteOrgConfirmDialog.tsx  - Confirmation dialog
├── hooks/
│   ├── useOrganizations.ts         - React Query for list
│   ├── useOrganization.ts          - React Query for single org
│   └── useOrganizationActions.ts   - Mutations (create/update/delete)
├── services/
│   └── organizationApi.ts          - API calls
└── types/
    └── organization.ts              - TypeScript types
```

**OrganizationTable.tsx:**
- [ ] Table with columns: Name, PIN, Users, Devices, Created At, Actions
- [ ] Search by name
- [ ] Actions: Edit, Delete (admin only)
- [ ] Click row → view details

**OrganizationModal.tsx:**
- [ ] Form fields: Name (required), PIN (optional, auto-generate button)
- [ ] Validation: name required, PIN 4-6 digits if provided
- [ ] Use `validators.required()` and custom PIN validator
- [ ] Show toast on success/error
- [ ] Close modal after success

---

### 2. User Management Feature

**Files to create:**
```
features/users/
├── components/
│   ├── UserTable.tsx               - List users with filters
│   ├── UserModal.tsx               - Create/Edit user form
│   ├── InviteUserModal.tsx         - Simplified invite form
│   ├── ChangePasswordModal.tsx     - Password change form
│   ├── UserRoleBadge.tsx           - Badge showing role
│   └── UserStatusBadge.tsx         - Badge showing active/inactive
├── hooks/
│   ├── useUsers.ts                 - React Query for list
│   ├── useUser.ts                  - React Query for single user
│   └── useUserActions.ts           - Mutations (create/update/delete)
├── services/
│   └── userApi.ts                  - API calls
└── types/
    └── user.ts                      - TypeScript types
```

**UserTable.tsx:**
- [ ] Table columns: Name, Username, Email, Role, Organization, Last Login, Status, Actions
- [ ] Filters: Organization (dropdown), Role (dropdown), Search (name/email)
- [ ] Filter by own org only if not admin
- [ ] Actions: Edit, Change Password, Deactivate
- [ ] Use `UserRoleBadge` and `UserStatusBadge` components

**UserModal.tsx:**
- [ ] Form fields: Username, Email, Full Name, Password, Role, Organization (if admin)
- [ ] Validation:
  - Use `validators.username()`
  - Use `validators.email()`
  - Use `validators.password()`
  - Use `validators.required()`
- [ ] Show validation errors in real-time
- [ ] Toast on success/error
- [ ] Permission check: disable role/org fields based on user role

---

### 3. Pages

**Files to create:**
- [ ] `pages/organizations/OrganizationsPage.tsx` - Organization list page
- [ ] `pages/organizations/OrganizationDetailPage.tsx` - Single org details + stats
- [ ] `pages/users/UsersPage.tsx` - User list page
- [ ] `pages/users/UserDetailPage.tsx` - Single user details + activity log (future)

---

### 4. Navigation & Routes

**Update files:**
- [ ] `routes/index.tsx` - Add organization and user routes
- [ ] `shared/components/layout/Sidebar.tsx` - Add menu items with permission checks

**Example:**
```typescript
// Sidebar.tsx
import { canPerformAction } from '@/lib/auth/permissions';

{canPerformAction(user, PERMISSIONS.USER.VIEW) && (
  <SidebarItem icon={Users} label="Users" to="/users" />
)}

{canPerformAction(user, PERMISSIONS.ORGANIZATION.VIEW) && (
  <SidebarItem icon={Building} label="Organizations" to="/organizations" />
)}
```

---

### 5. Organization Switcher (Topbar)

**Update file:** `shared/components/layout/Topbar.tsx`

**Features:**
- [ ] Dropdown showing current organization
- [ ] List all user's organizations
- [ ] Click to switch organization
- [ ] Use `useSelectOrganization()` hook
- [ ] Show toast on switch success
- [ ] Refresh page data after switch

---

## 🎯 Permission Matrix

| Action | Admin | Manager | Viewer |
|--------|-------|---------|--------|
| View orgs (all) | ✅ | ❌ | ❌ |
| View own org | ✅ | ✅ | ✅ |
| Create org | ✅ | ❌ | ❌ |
| Update org | ✅ | ❌ | ❌ |
| Delete org | ✅ | ❌ | ❌ |
| View users (all orgs) | ✅ | ❌ | ❌ |
| View users (own org) | ✅ | ✅ | ❌ |
| Create user | ✅ | ✅ (own org) | ❌ |
| Update user | ✅ | ✅ (own org) | ❌ |
| Change own password | ✅ | ✅ | ✅ |
| Deactivate user | ✅ | ✅ (own org, not self) | ❌ |
| Switch organization | ✅ | ✅ | ✅ |

---

## ✅ Acceptance Criteria

- [ ] Admin can create/edit/delete organizations
- [ ] Admin can see all organizations
- [ ] Manager can only see own organization
- [ ] Admin can create/edit users in any organization
- [ ] Manager can create/edit users in own organization only
- [ ] Manager cannot change user roles to admin
- [ ] Users can change own password
- [ ] Users can switch between their organizations
- [ ] All actions show appropriate toast notifications
- [ ] All forms use centralized validation
- [ ] All errors show Indonesian messages
- [ ] All API calls use centralized error handling
- [ ] Permission checks on all actions (frontend + backend)
- [ ] Audit log entries for all user/org changes (backend)

---

## 📝 Testing Checklist

### Organizations:
- [ ] Admin creates new org → Success + PIN generated
- [ ] Admin edits org → Success toast
- [ ] Admin deletes org with users → Error (cannot delete)
- [ ] Manager tries to create org → 403 Forbidden
- [ ] Search organization by name → Filtered results

### Users:
- [ ] Admin creates user → Success + user can login
- [ ] Manager creates user in own org → Success
- [ ] Manager tries to create user in other org → 403 Forbidden
- [ ] Manager tries to set role to admin → Validation error
- [ ] User changes own password → Success + can login with new password
- [ ] Admin deactivates user → User cannot login
- [ ] Try to deactivate self → Error message
- [ ] Try to deactivate last admin → Error message

### Permissions:
- [ ] Viewer cannot see Users menu → Menu hidden
- [ ] Manager sees Users menu → Only own org users
- [ ] Admin sees Organizations menu → All orgs visible
- [ ] Manager cannot see Organizations menu → Menu hidden

---

## 🚫 DO NOT IMPLEMENT YET

This is planning only. Wait for:
1. ✅ Approval of this plan
2. ✅ Completion of `TODO_REFACTORING.md`
3. ✅ Green light to start implementation

---

## 📅 Estimated Timeline

**After refactoring is complete:**
- Day 1: Backend Organization API + Permission middleware
- Day 2: Backend User API + Audit logging
- Day 3: Frontend Organization feature (components + pages)
- Day 4: Frontend User feature (components + pages)
- Day 5: Integration testing + Bug fixes
