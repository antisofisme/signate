# Multi-Tenant Frontend - Visual Guide

This document provides ASCII art diagrams and visual representations to help understand the architecture.

---

## Table of Contents
1. [Application Structure](#application-structure)
2. [Authentication Flow](#authentication-flow)
3. [Permission System](#permission-system)
4. [Organization Switching](#organization-switching)
5. [Component Relationships](#component-relationships)
6. [Data Flow Patterns](#data-flow-patterns)

---

## Application Structure

### Overall Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Browser Window                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        App Component                          │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │              ThemeProvider (Dark Mode)                 │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐  │  │   │
│  │  │  │         QueryClientProvider (React Query)        │  │  │   │
│  │  │  │  ┌────────────────────────────────────────────┐  │  │  │   │
│  │  │  │  │              Router                        │  │  │  │   │
│  │  │  │  │  ┌──────────────────────────────────────┐  │  │  │  │   │
│  │  │  │  │  │      AuthProvider (NEW)              │  │  │  │  │   │
│  │  │  │  │  │  ┌────────────────────────────────┐  │  │  │  │  │   │
│  │  │  │  │  │  │  OrganizationProvider (NEW)   │  │  │  │  │  │   │
│  │  │  │  │  │  │  ┌──────────────────────────┐  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │      Routes              │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │                          │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  Public:                 │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /login                │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /forgot-password      │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │                          │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  Protected:              │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - / (Dashboard)         │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /devices              │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /content              │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /users (NEW)          │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - /profile (NEW)        │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  │  - ...                   │  │  │  │  │  │  │   │
│  │  │  │  │  │  │  └──────────────────────────┘  │  │  │  │  │  │   │
│  │  │  │  │  │  └────────────────────────────────┘  │  │  │  │  │   │
│  │  │  │  │  └──────────────────────────────────────┘  │  │  │  │   │
│  │  │  │  └────────────────────────────────────────────┘  │  │  │   │
│  │  │  └──────────────────────────────────────────────────┘  │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

### Login Sequence

```
┌────────┐                ┌─────────┐              ┌─────────┐              ┌──────────┐
│ User   │                │ Login   │              │  Auth   │              │ Backend  │
│        │                │  Page   │              │ Context │              │   API    │
└───┬────┘                └────┬────┘              └────┬────┘              └────┬─────┘
    │                          │                        │                        │
    │  Enter credentials       │                        │                        │
    ├─────────────────────────>│                        │                        │
    │                          │                        │                        │
    │  Click Login             │                        │                        │
    ├─────────────────────────>│                        │                        │
    │                          │                        │                        │
    │                          │  login(credentials)    │                        │
    │                          ├───────────────────────>│                        │
    │                          │                        │                        │
    │                          │                        │  POST /api/auth/login  │
    │                          │                        ├───────────────────────>│
    │                          │                        │                        │
    │                          │                        │  { access_token,       │
    │                          │                        │    refresh_token,      │
    │                          │                        │    user }              │
    │                          │                        │<───────────────────────┤
    │                          │                        │                        │
    │                          │                        │  Store tokens          │
    │                          │                        │  Update state          │
    │                          │                        │  ─────────             │
    │                          │                        │          │             │
    │                          │                        │<─────────              │
    │                          │                        │                        │
    │                          │  { success: true }     │                        │
    │                          │<───────────────────────┤                        │
    │                          │                        │                        │
    │  Redirect to Dashboard   │                        │                        │
    │<─────────────────────────┤                        │                        │
    │                          │                        │                        │
    │                          │                        │                        │
┌───┴────┐                ┌────┴────┐              ┌────┴────┐              ┌────┴─────┐
│ User   │                │ Login   │              │  Auth   │              │ Backend  │
│        │                │  Page   │              │ Context │              │   API    │
└────────┘                └─────────┘              └─────────┘              └──────────┘
```

### Token Refresh Flow

```
┌────────────┐           ┌───────────┐          ┌────────────┐         ┌──────────┐
│ Component  │           │    API    │          │   Auth     │         │ Backend  │
│            │           │ Interceptor│         │  Context   │         │   API    │
└─────┬──────┘           └─────┬─────┘          └─────┬──────┘         └────┬─────┘
      │                        │                      │                     │
      │  API Request           │                      │                     │
      ├───────────────────────>│                      │                     │
      │                        │                      │                     │
      │                        │  Add Bearer token    │                     │
      │                        │  ─────────           │                     │
      │                        │          │           │                     │
      │                        │<─────────            │                     │
      │                        │                      │                     │
      │                        │  Request with token  │                     │
      │                        ├─────────────────────────────────────────>│
      │                        │                      │                     │
      │                        │  401 Unauthorized    │                     │
      │                        │<─────────────────────────────────────────┤
      │                        │                      │                     │
      │                        │  refreshToken()      │                     │
      │                        ├─────────────────────>│                     │
      │                        │                      │                     │
      │                        │                      │  POST /api/auth/   │
      │                        │                      │       refresh      │
      │                        │                      ├────────────────────>│
      │                        │                      │                     │
      │                        │                      │  { new_token }      │
      │                        │                      │<────────────────────┤
      │                        │                      │                     │
      │                        │                      │  Update storage     │
      │                        │                      │  ─────────          │
      │                        │                      │          │          │
      │                        │                      │<─────────           │
      │                        │                      │                     │
      │                        │  new_token           │                     │
      │                        │<─────────────────────┤                     │
      │                        │                      │                     │
      │                        │  Retry with new token│                     │
      │                        ├─────────────────────────────────────────>│
      │                        │                      │                     │
      │                        │  200 OK + Data       │                     │
      │                        │<─────────────────────────────────────────┤
      │                        │                      │                     │
      │  Response data         │                      │                     │
      │<───────────────────────┤                      │                     │
      │                        │                      │                     │
┌─────┴──────┐           ┌─────┴─────┐          ┌─────┴──────┐         ┌────┴─────┐
│ Component  │           │    API    │          │   Auth     │         │ Backend  │
│            │           │ Interceptor│         │  Context   │         │   API    │
└────────────┘           └───────────┘          └────────────┘         └──────────┘
```

---

## Permission System

### Permission Check Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Component Renders                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────┐
         │  Need to check permission?               │
         │  (e.g., PERMISSIONS.USERS_CREATE)        │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │  useAuth().checkPermission(permission)   │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │  Is user.role === 'super_admin'?         │
         └──────────────┬────────────────┬──────────┘
                        │                │
                   YES  │                │  NO
                        │                │
                        ▼                ▼
         ┌──────────────────┐  ┌─────────────────────────────────┐
         │  Return TRUE      │  │  Check user.permissions array   │
         │  (Super admin     │  │  permissions.includes(          │
         │   has all perms)  │  │    'users.create'               │
         └──────────────────┘  │  )                               │
                               └─────────────┬───────────────────┘
                                             │
                                             ▼
                          ┌──────────────────────────────────────┐
                          │  Permission in array?                │
                          └────────────┬────────────────┬────────┘
                                       │                │
                                  YES  │                │  NO
                                       │                │
                                       ▼                ▼
                          ┌─────────────────┐  ┌────────────────┐
                          │  Return TRUE    │  │  Return FALSE  │
                          │  (Show content) │  │  (Hide content)│
                          └─────────────────┘  └────────────────┘
```

### Permission Gate Component

```
┌──────────────────────────────────────────────────────────────────┐
│              <PermissionGate permission="users.create">          │
│                <CreateUserButton />                              │
│              </PermissionGate>                                   │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │  checkPermission()           │
                 └──────────┬───────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
         HAS PERMISSION            NO PERMISSION
              │                           │
              ▼                           ▼
┌──────────────────────────┐   ┌─────────────────────────┐
│  Render Children         │   │  Render Fallback        │
│                          │   │  (or null)              │
│  ┌────────────────────┐  │   │                         │
│  │ CreateUserButton   │  │   │  ┌───────────────────┐  │
│  │    [+ Create]      │  │   │  │   (nothing shown) │  │
│  └────────────────────┘  │   │  └───────────────────┘  │
└──────────────────────────┘   └─────────────────────────┘
```

### Role-Based UI Rendering

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Navigation Menu                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ALL USERS:                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  [Dashboard] [Devices] [Content] [Settings]                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  + IF has 'users.view' permission:                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  [Users]                                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  + IF role === 'super_admin':                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  [Organizations]                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Examples:

┌──────────────────────────────────────┐
│  VIEWER sees:                        │
│  [Dashboard] [Devices] [Content]     │
│  [Settings]                          │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  EDITOR sees:                        │
│  [Dashboard] [Devices] [Content]     │
│  [Playlists] [Tags] [Settings]       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  ORG ADMIN sees:                     │
│  [Dashboard] [Devices] [Content]     │
│  [Playlists] [Tags] [Users]          │
│  [Settings]                          │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  SUPER ADMIN sees:                   │
│  [Dashboard] [Devices] [Content]     │
│  [Playlists] [Tags] [Users]          │
│  [Organizations] [Settings]          │
└──────────────────────────────────────┘
```

---

## Organization Switching

### Organization Switcher UI

```
┌─────────────────────────────────────────────────────────────────┐
│  Topbar                                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [Logo]    [Org: Acme Corp ▼]         [Search]    [Profile ▼]   │
│                    │                                             │
│                    └──> Dropdown Opens                           │
│                         ┌────────────────────────────────────┐  │
│                         │  Current Organization              │  │
│                         │  ┌──────────────────────────────┐  │  │
│                         │  │  Acme Corporation            │  │  │
│                         │  │  [Admin]                     │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         │  ─────────────────────────────────  │  │
│                         │  Switch to:                        │  │
│                         │  ┌──────────────────────────────┐  │  │
│                         │  │  ○ Tech Startup Inc          │  │  │
│                         │  │     [Editor]                 │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         │  ┌──────────────────────────────┐  │  │
│                         │  │  ○ Design Agency LLC         │  │  │
│                         │  │     [Viewer]                 │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         │  ─────────────────────────────────  │  │
│                         │  [⚙ Manage Organizations]         │  │
│                         │  (Super Admin only)                │  │
│                         └────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Organization Switch Flow

```
User clicks "Tech Startup Inc"
         │
         ▼
┌─────────────────────────────────────┐
│  OrganizationContext                 │
│  .switchOrganization(orgId: 2)       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  1. Call API                         │
│     POST /api/organizations/2/switch │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Backend validates:                  │
│  - User has access to Org 2          │
│  - User's role in Org 2              │
│  Returns new JWT with org context    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Update localStorage              │
│     - token (new)                    │
│     - current_organization_id (2)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Update AuthContext               │
│     - currentOrganization            │
│     - user.organization_id           │
│     - user.permissions (org-specific)│
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Update API Interceptors          │
│     All future requests include:     │
│     X-Organization-Id: 2             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Invalidate React Query Cache     │
│     queryClient.invalidateQueries()  │
│     (Clear all cached data)          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  6. Re-render Application            │
│     - Topbar shows new org name      │
│     - Dashboard loads new org data   │
│     - All pages show new org data    │
│     - Navigation updates (if needed) │
└─────────────────────────────────────┘
```

---

## Component Relationships

### Users Page Component Tree

```
UsersPage
│
├─── PageHeader
│    ├─── Title: "Users"
│    └─── InviteUserButton (if has USERS_INVITE permission)
│         └─── Opens: InviteUserModal
│
├─── UserStats (Statistics Cards)
│    ├─── TotalUsers
│    ├─── ActiveUsers
│    ├─── PendingInvites
│    └─── AdminCount
│
├─── UserFilters
│    ├─── SearchInput (debounced)
│    ├─── RoleFilter (dropdown)
│    ├─── StatusFilter (dropdown)
│    └─── ClearFiltersButton
│
├─── UserTable
│    ├─── TableHeader
│    │    ├─── Column: Avatar + Name
│    │    ├─── Column: Email
│    │    ├─── Column: Role
│    │    ├─── Column: Status
│    │    ├─── Column: Last Login
│    │    └─── Column: Actions
│    │
│    ├─── UserTableRow (for each user)
│    │    ├─── UserAvatar
│    │    ├─── UserInfo
│    │    │    ├─── Name
│    │    │    └─── Username
│    │    ├─── Email
│    │    │    └─── EmailVerifiedBadge (if not verified)
│    │    ├─── UserRoleBadge
│    │    ├─── UserStatusBadge
│    │    ├─── LastLogin (formatted date)
│    │    └─── ActionsDropdown
│    │         ├─── View Details
│    │         ├─── Edit (if has USERS_EDIT)
│    │         ├─── Reset Password (if has USERS_EDIT)
│    │         └─── Delete (if has USERS_DELETE)
│    │
│    └─── TableFooter
│         └─── Shows result count
│
├─── Pagination
│    ├─── Previous button
│    ├─── Page numbers
│    └─── Next button
│
└─── Modals (rendered conditionally)
     ├─── UserDetailModal
     ├─── UserEditModal
     ├─── InviteUserModal
     ├─── UserPermissionsModal
     └─── UserDeleteConfirmModal
```

### Layout Component Structure

```
Layout
│
├─── MobileMenuButton (visible on mobile only)
│
├─── MobileOverlay (visible when menu open)
│
├─── Sidebar
│    │
│    ├─── Logo
│    │
│    ├─── Navigation
│    │    └─── NavItem (for each nav item)
│    │         ├─── Icon
│    │         ├─── Label
│    │         └─── Badge (for notifications)
│    │
│    └─── Footer
│         ├─── ThemeToggle
│         └─── (Logout moved to profile dropdown)
│
├─── MainContent
│    │
│    ├─── Topbar
│    │    ├─── Spacer
│    │    ├─── OrganizationSwitcher (Phase 3)
│    │    │    └─── OrganizationDropdown
│    │    └─── ProfileDropdown
│    │         ├─── Trigger (avatar + name + role)
│    │         └─── Menu
│    │              ├─── User Info Header
│    │              ├─── My Profile link
│    │              ├─── Settings link
│    │              └─── Logout button
│    │
│    └─── ContentArea
│         └─── <Outlet /> (React Router renders page here)
```

---

## Data Flow Patterns

### React Query + Context Pattern

```
┌───────────────────────────────────────────────────────────────────┐
│                         Component                                  │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  // Get global auth state                                          │
│  const { user, checkPermission } = useAuth()                       │
│                                                                     │
│  // Get server data with caching                                   │
│  const { data: users, isLoading } = useQuery({                     │
│    queryKey: ['users', filters],                                   │
│    queryFn: () => usersAPI.list(filters)                           │
│  })                                                                 │
│                                                                     │
│  // Mutation with cache invalidation                               │
│  const createUser = useMutation({                                  │
│    mutationFn: usersAPI.create,                                    │
│    onSuccess: () => {                                              │
│      queryClient.invalidateQueries(['users'])                      │
│    }                                                                │
│  })                                                                 │
│                                                                     │
└───────────────────────────────────────────────────────────────────┘

         │                          │                        │
         │ Read                     │ Fetch                  │ Mutate
         │ Global State             │ Server State           │ & Invalidate
         ▼                          ▼                        ▼

┌──────────────┐         ┌──────────────────┐      ┌─────────────────┐
│ AuthContext  │         │  React Query     │      │  React Query    │
│              │         │  Cache           │      │  Mutations      │
│ - user       │         │                  │      │                 │
│ - permissions│         │ ['users'] → []   │      │ POST /users     │
│ - org        │         │ ['devices'] → [] │      │ invalidate      │
│              │         │ ['content'] → [] │      │ ['users']       │
└──────────────┘         └──────────────────┘      └─────────────────┘
```

### Optimistic Update Pattern

```
User clicks "Delete User"
         │
         ▼
┌─────────────────────────────────────┐
│  1. Optimistic Update                │
│     Remove user from UI immediately  │
│     (before API response)            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Call API                         │
│     DELETE /api/users/123            │
└──────────────┬──────────────────────┘
               │
         ┌─────┴─────┐
         │           │
    SUCCESS       ERROR
         │           │
         ▼           ▼
┌─────────────┐  ┌──────────────────┐
│ 3a. Keep     │  │ 3b. Rollback     │
│     changes  │  │     Restore user │
│     Show     │  │     Show error   │
│     success  │  │     toast        │
└─────────────┘  └──────────────────┘
```

---

## User Flows

### Complete User Journey: Create New User

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ADMIN USER                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ 1. Navigate to Users page
                                ▼
                    ┌────────────────────────┐
                    │  Users Page            │
                    │  ─────────────────     │
                    │  [+ Invite User]       │
                    │                        │
                    │  John Doe  john@...    │
                    │  Jane Smith jane@...   │
                    └────────────┬───────────┘
                                 │
                                 │ 2. Click "Invite User"
                                 ▼
                    ┌────────────────────────────────────┐
                    │  Invite User Modal                 │
                    │  ────────────────────────────      │
                    │  Email: [________________]         │
                    │  Name:  [________________]         │
                    │  Role:  [Select role ▼  ]         │
                    │         - Super Admin              │
                    │         - Org Admin                │
                    │         - Editor                   │
                    │         - Viewer                   │
                    │  ☑ Send invitation email           │
                    │                                    │
                    │  [Cancel] [Send Invite]            │
                    └──────────────┬─────────────────────┘
                                   │
                                   │ 3. Fill form and submit
                                   ▼
                    ┌──────────────────────────────────┐
                    │  Loading...                      │
                    │  Creating user and sending       │
                    │  invitation email                │
                    └──────────────┬───────────────────┘
                                   │
                                   │ 4. API creates user
                                   ▼
                    ┌──────────────────────────────────┐
                    │  ✓ Success!                      │
                    │  Invitation sent to              │
                    │  newuser@example.com             │
                    └──────────────┬───────────────────┘
                                   │
                                   │ 5. User added to table
                                   ▼
                    ┌────────────────────────────────────┐
                    │  Users Page (Updated)              │
                    │  ─────────────────────             │
                    │  [+ Invite User]                   │
                    │                                    │
                    │  New User     new@...  [Pending]   │
                    │  John Doe     john@... [Active]    │
                    │  Jane Smith   jane@... [Active]    │
                    └────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          NEW USER                                    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ 6. Receives email
                                ▼
                    ┌────────────────────────────────────┐
                    │  📧 Email Inbox                    │
                    │  ──────────────                    │
                    │  From: Signage Admin               │
                    │  Subject: You've been invited!     │
                    │                                    │
                    │  Click here to set your password   │
                    │  [Set Password] (link)             │
                    └──────────────┬─────────────────────┘
                                   │
                                   │ 7. Click link
                                   ▼
                    ┌────────────────────────────────────┐
                    │  Set Password Page                 │
                    │  ────────────────────              │
                    │  Welcome, New User!                │
                    │                                    │
                    │  Password: [________________]      │
                    │  Confirm:  [________________]      │
                    │                                    │
                    │  [Set Password & Login]            │
                    └──────────────┬─────────────────────┘
                                   │
                                   │ 8. Set password
                                   ▼
                    ┌────────────────────────────────────┐
                    │  Dashboard                         │
                    │  ────────────                      │
                    │  Welcome to Signage Admin!         │
                    │  (Limited access based on role)    │
                    └────────────────────────────────────┘
```

---

## State Synchronization

### Multi-Tab Synchronization

```
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   Tab 1      │              │ localStorage │              │   Tab 2      │
│              │              │              │              │              │
└──────┬───────┘              └──────┬───────┘              └──────┬───────┘
       │                             │                             │
       │ User logs out               │                             │
       ├────────────────────────────>│                             │
       │                             │                             │
       │ Remove 'token'              │                             │
       │ Remove 'refresh_token'      │                             │
       │                             │                             │
       │                             │ 'storage' event fired       │
       │                             ├────────────────────────────>│
       │                             │                             │
       │                             │                             │ Detect
       │                             │                             │ token
       │                             │                             │ removed
       │                             │                             │
       │                             │                             │ Logout
       │                             │                             │ automatically
       │                             │                             │
       │                             │                             ▼
       │                             │              ┌──────────────────────┐
       │                             │              │  Redirect to Login   │
       │                             │              └──────────────────────┘
       │                             │
       ▼                             ▼                             ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│ Login Page   │              │ (Storage)    │              │ Login Page   │
└──────────────┘              └──────────────┘              └──────────────┘
```

---

## Performance Optimization

### Code Splitting Strategy

```
Initial Bundle
├── App.jsx
├── AuthContext
├── ThemeContext
├── Layout
└── Login (immediate)

Lazy Loaded:
├── /dashboard      → Dashboard.jsx
├── /devices        → Devices.jsx
├── /content        → Content.jsx
├── /users          → Users.jsx (NEW)
├── /profile        → Profile.jsx (NEW)
└── /organizations  → Organizations.jsx (NEW)

Benefits:
┌────────────────────────────────────────┐
│  Initial load: ~200KB                  │
│  After login: Load only needed pages   │
│  Faster Time to Interactive            │
└────────────────────────────────────────┘
```

### Query Caching Strategy

```
Time: 0s                  5min                10min               15min
      │                    │                    │                    │
      │                    │                    │                    │
      ├─> Fetch /users     │                    │                    │
      │   (network)        │                    │                    │
      │                    │                    │                    │
      │   [Cache: Fresh]   │                    │                    │
      │                    │                    │                    │
      ├─> Request /users   │                    │                    │
      │   (cache)          │                    │                    │
      │   ✓ Fast!          │                    │                    │
      │                    │                    │                    │
      │                    ├─> [Cache: Stale]   │                    │
      │                    │   Next request     │                    │
      │                    │   will refetch     │                    │
      │                    │                    │                    │
      │                    ├─> Request /users   │                    │
      │                    │   (network +       │                    │
      │                    │    show old data)  │                    │
      │                    │                    │                    │
      │                    │                    ├─> [Cache: Removed] │
      │                    │                    │   Memory freed     │
      │                    │                    │                    │
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼

staleTime: 5 * 60 * 1000       cacheTime: 10 * 60 * 1000
(data fresh for 5 min)         (keep in memory for 10 min)
```

---

## Summary Diagram

### Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SIGNAGE ADMIN SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐        │
│  │   FRONTEND      │  │   API LAYER     │  │   BACKEND        │        │
│  │   (React)       │  │   (Axios)       │  │   (FastAPI)      │        │
│  │                 │  │                 │  │                  │        │
│  │  Components     │◄─┤  Interceptors   │◄─┤  JWT Auth        │        │
│  │  Contexts       │  │  - Add token    │  │  - Validate      │        │
│  │  React Query    │  │  - Add org ID   │  │  - Check perms   │        │
│  │                 │  │  - Handle 401   │  │  - Filter by org │        │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘        │
│         │                      │                      │                  │
│         │                      │                      │                  │
│         ▼                      ▼                      ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    LOCAL STORAGE                             │       │
│  │  - token           - refresh_token    - current_org_id       │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    STATE MANAGEMENT                          │       │
│  │                                                               │       │
│  │  Context API:           React Query:                         │       │
│  │  - AuthContext          - Users cache                        │       │
│  │  - OrgContext           - Devices cache                      │       │
│  │  - ThemeContext         - Content cache                      │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    PERMISSION SYSTEM                         │       │
│  │                                                               │       │
│  │  Route Protection → Component Gates → API Validation         │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

**End of Visual Guide**

These diagrams should help visualize the architecture and understand how different parts of the system interact with each other.
