# Multi-Tenant User Management - Frontend Architecture Design

## Table of Contents
1. [Overview](#overview)
2. [State Management Strategy](#state-management-strategy)
3. [Component Architecture](#component-architecture)
4. [Routing & Navigation](#routing--navigation)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Integration](#api-integration)
7. [UI/UX Design Specifications](#uiux-design-specifications)
8. [Migration Strategy](#migration-strategy)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Current Stack
- **Framework**: React 18.3.1 + Vite 5.4.1
- **Styling**: TailwindCSS 3.4.11
- **Icons**: Lucide React 0.445.0
- **Routing**: React Router DOM 6.26.0
- **State Management**: React Query (TanStack Query) 5.56.2
- **HTTP Client**: Axios 1.7.7
- **Notifications**: React Hot Toast 2.6.0

### Architecture Principles
1. **Modular Design**: Separation of concerns with clear boundaries
2. **Type Safety**: Prepare for TypeScript migration with clear interfaces
3. **Performance**: Optimistic updates, caching, and lazy loading
4. **Accessibility**: WCAG 2.1 AA compliance
5. **Security**: Role-based access control (RBAC) at UI level
6. **Scalability**: Support for multiple organizations and roles

---

## State Management Strategy

### 1. Auth Context (NEW)
**Purpose**: Manage global authentication and user session state

**Location**: `/src/contexts/AuthContext.jsx`

**State Structure**:
```javascript
{
  user: {
    id: number,
    email: string,
    username: string,
    full_name: string,
    role: 'super_admin' | 'org_admin' | 'editor' | 'viewer',
    organization_id: number,
    organization: {
      id: number,
      name: string,
      slug: string,
      is_active: boolean
    },
    organizations: Array<{
      id: number,
      name: string,
      role: string
    }>,
    permissions: Array<string>,
    is_active: boolean,
    email_verified: boolean
  },
  currentOrganization: {
    id: number,
    name: string,
    slug: string
  },
  isAuthenticated: boolean,
  isLoading: boolean,
  token: string | null
}
```

**Methods**:
```javascript
{
  login: (credentials) => Promise<void>,
  logout: () => void,
  refreshToken: () => Promise<void>,
  switchOrganization: (orgId) => Promise<void>,
  updateUser: (userData) => void,
  checkPermission: (permission) => boolean,
  hasRole: (role) => boolean
}
```

### 2. Organization Context (NEW)
**Purpose**: Manage organization-specific settings and preferences

**Location**: `/src/contexts/OrganizationContext.jsx`

**State Structure**:
```javascript
{
  settings: {
    branding: {
      logo_url: string,
      primary_color: string,
      name: string
    },
    features: {
      content_management: boolean,
      device_management: boolean,
      analytics: boolean
    },
    limits: {
      max_devices: number,
      max_users: number,
      storage_gb: number
    }
  },
  stats: {
    device_count: number,
    user_count: number,
    storage_used_gb: number
  }
}
```

### 3. Existing Contexts
- **ThemeContext**: Keep as-is for dark mode
- **React Query**: Continue for server state management

### 4. State Management Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      App Component                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │              ThemeProvider (Existing)              │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │          QueryClientProvider (Existing)      │ │ │
│  │  │  ┌────────────────────────────────────────┐  │ │ │
│  │  │  │       AuthProvider (NEW)               │  │ │ │
│  │  │  │  ┌──────────────────────────────────┐  │  │ │ │
│  │  │  │  │   OrganizationProvider (NEW)    │  │  │ │ │
│  │  │  │  │  ┌────────────────────────────┐ │  │  │ │ │
│  │  │  │  │  │       Router & Routes      │ │  │  │ │ │
│  │  │  │  │  └────────────────────────────┘ │  │  │ │ │
│  │  │  │  └──────────────────────────────────┘  │  │ │ │
│  │  │  └────────────────────────────────────────┘  │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Directory Structure

```
src/
├── components/
│   ├── auth/                          # NEW - Authentication components
│   │   ├── LoginForm.jsx
│   │   ├── ForgotPasswordForm.jsx
│   │   ├── ResetPasswordForm.jsx
│   │   ├── VerifyEmailPrompt.jsx
│   │   └── OrganizationSelector.jsx
│   │
│   ├── users/                         # NEW - User management components
│   │   ├── UserTable.jsx
│   │   ├── UserTableRow.jsx
│   │   ├── UserFilters.jsx
│   │   ├── UserRoleBadge.jsx
│   │   ├── UserStatusBadge.jsx
│   │   ├── InviteUserButton.jsx
│   │   └── modals/
│   │       ├── UserDetailModal.jsx
│   │       ├── UserEditModal.jsx
│   │       ├── UserCreateModal.jsx
│   │       ├── InviteUserModal.jsx
│   │       ├── UserPermissionsModal.jsx
│   │       └── UserDeleteConfirmModal.jsx
│   │
│   ├── organizations/                 # NEW - Organization components
│   │   ├── OrganizationCard.jsx
│   │   ├── OrganizationSwitcher.jsx
│   │   ├── OrganizationStats.jsx
│   │   ├── OrganizationLimits.jsx
│   │   └── modals/
│   │       ├── OrganizationEditModal.jsx
│   │       ├── OrganizationCreateModal.jsx
│   │       └── OrganizationSettingsModal.jsx
│   │
│   ├── profile/                       # NEW - User profile components
│   │   ├── ProfileDropdown.jsx
│   │   ├── ProfileMenu.jsx
│   │   ├── ProfileAvatar.jsx
│   │   └── modals/
│   │       ├── ProfileEditModal.jsx
│   │       └── ChangePasswordModal.jsx
│   │
│   ├── permissions/                   # NEW - Permission management
│   │   ├── PermissionGate.jsx         # HOC for permission-based rendering
│   │   ├── RoleGate.jsx               # HOC for role-based rendering
│   │   ├── PermissionTag.jsx
│   │   └── RoleTag.jsx
│   │
│   ├── layout/                        # UPDATED - Enhanced layout
│   │   ├── Layout.jsx                 # Updated with org switcher
│   │   ├── Header.jsx                 # NEW - Extracted from Layout
│   │   ├── Sidebar.jsx                # NEW - Extracted from Layout
│   │   ├── Topbar.jsx                 # NEW - Org switcher + profile
│   │   └── Breadcrumbs.jsx            # NEW - Navigation breadcrumbs
│   │
│   ├── common/                        # Existing common components
│   │   ├── Badge.jsx
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Modal.jsx
│   │   ├── EmptyState.jsx
│   │   ├── LoadingSpinner.jsx
│   │   ├── DataTable.jsx              # NEW - Reusable table component
│   │   ├── SearchInput.jsx            # NEW - Reusable search
│   │   ├── FilterDropdown.jsx         # NEW - Reusable filter
│   │   └── Pagination.jsx             # NEW - Reusable pagination
│   │
│   └── ... (existing components)
│
├── contexts/
│   ├── AuthContext.jsx                # NEW
│   ├── OrganizationContext.jsx        # NEW
│   └── ThemeContext.jsx               # Existing
│
├── hooks/                             # NEW - Custom hooks
│   ├── useAuth.js
│   ├── useOrganization.js
│   ├── usePermission.js
│   ├── useUser.js
│   ├── useUsers.js
│   └── useDebounce.js
│
├── pages/
│   ├── Login.jsx                      # UPDATED
│   ├── ForgotPassword.jsx             # NEW
│   ├── ResetPassword.jsx              # NEW
│   ├── VerifyEmail.jsx                # NEW
│   ├── Users.jsx                      # NEW
│   ├── Profile.jsx                    # NEW
│   ├── Organizations.jsx              # NEW (super admin only)
│   ├── Settings.jsx                   # UPDATED
│   └── ... (existing pages)
│
├── services/
│   ├── api.js                         # UPDATED
│   ├── auth.service.js                # NEW - Auth-specific logic
│   ├── users.service.js               # NEW - User-specific logic
│   ├── organizations.service.js       # NEW - Org-specific logic
│   └── permissions.service.js         # NEW - Permission checks
│
├── utils/
│   ├── permissions.js                 # NEW - Permission constants
│   ├── roles.js                       # NEW - Role constants
│   ├── validators.js                  # NEW - Form validators
│   └── formatters.js                  # NEW - Data formatters
│
└── App.jsx                            # UPDATED
```

---

## Routing & Navigation

### Updated Route Structure

```javascript
// App.jsx
<Routes>
  {/* Public Routes */}
  <Route path="/login" element={<Login />} />
  <Route path="/forgot-password" element={<ForgotPassword />} />
  <Route path="/reset-password/:token" element={<ResetPassword />} />
  <Route path="/verify-email/:token" element={<VerifyEmail />} />

  {/* Protected Routes - Require Authentication */}
  <Route element={<ProtectedRoute />}>
    <Route element={<Layout />}>
      {/* Dashboard */}
      <Route path="/" element={<Dashboard />} />

      {/* Devices */}
      <Route path="/devices" element={<Devices />} />
      <Route path="/devices/:id/preview" element={<DevicePreview />} />

      {/* Content */}
      <Route path="/content" element={<Content />} />

      {/* Playlists */}
      <Route path="/playlists" element={<Playlists />} />

      {/* Tags */}
      <Route path="/tags" element={<Tags />} />

      {/* Activities */}
      <Route path="/activities" element={<Activities />} />

      {/* Widgets */}
      <Route path="/widgets" element={<Widgets />} />

      {/* Users - NEW */}
      <Route path="/users" element={
        <PermissionRoute permission="users.view">
          <Users />
        </PermissionRoute>
      } />

      {/* Profile - NEW */}
      <Route path="/profile" element={<Profile />} />

      {/* Organizations - NEW (Super Admin Only) */}
      <Route path="/organizations" element={
        <RoleRoute role="super_admin">
          <Organizations />
        </RoleRoute>
      } />

      {/* Settings */}
      <Route path="/settings" element={<Settings />} />
    </Route>
  </Route>

  {/* 404 */}
  <Route path="*" element={<NotFound />} />
</Routes>
```

### Route Protection Components

#### 1. ProtectedRoute Component
```javascript
// components/routing/ProtectedRoute.jsx
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import LoadingSpinner from '../common/LoadingSpinner'

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner fullScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
```

#### 2. PermissionRoute Component
```javascript
// components/routing/PermissionRoute.jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { Alert } from '../common/Alert'

export default function PermissionRoute({ permission, children, fallback }) {
  const { checkPermission } = useAuth()

  if (!checkPermission(permission)) {
    return fallback || (
      <div className="p-6">
        <Alert variant="error">
          You don't have permission to access this page.
        </Alert>
      </div>
    )
  }

  return children
}
```

#### 3. RoleRoute Component
```javascript
// components/routing/RoleRoute.jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export default function RoleRoute({ role, children }) {
  const { hasRole } = useAuth()

  if (!hasRole(role)) {
    return <Navigate to="/" replace />
  }

  return children
}
```

### Navigation Structure

```javascript
// Updated navigation items with permissions
const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    permission: null // Available to all
  },
  {
    name: 'Devices',
    href: '/devices',
    icon: Monitor,
    permission: 'devices.view'
  },
  {
    name: 'Content',
    href: '/content',
    icon: FileImage,
    permission: 'content.view'
  },
  {
    name: 'Playlists',
    href: '/playlists',
    icon: ListVideo,
    permission: 'playlists.view'
  },
  {
    name: 'Tags',
    href: '/tags',
    icon: Tag,
    permission: 'tags.view'
  },
  {
    name: 'Users',           // NEW
    href: '/users',
    icon: Users,
    permission: 'users.view',
    roles: ['super_admin', 'org_admin']
  },
  {
    name: 'Activity Logs',
    href: '/activities',
    icon: Clock,
    permission: 'activities.view'
  },
  {
    name: 'Widgets',
    href: '/widgets',
    icon: Puzzle,
    permission: 'widgets.view'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    permission: null // Available to all
  }
]
```

---

## Authentication & Authorization

### Permission System

#### Permission Constants
```javascript
// utils/permissions.js
export const PERMISSIONS = {
  // Device Permissions
  DEVICES_VIEW: 'devices.view',
  DEVICES_CREATE: 'devices.create',
  DEVICES_EDIT: 'devices.edit',
  DEVICES_DELETE: 'devices.delete',
  DEVICES_APPROVE: 'devices.approve',

  // Content Permissions
  CONTENT_VIEW: 'content.view',
  CONTENT_UPLOAD: 'content.upload',
  CONTENT_EDIT: 'content.edit',
  CONTENT_DELETE: 'content.delete',
  CONTENT_ASSIGN: 'content.assign',

  // Playlist Permissions
  PLAYLISTS_VIEW: 'playlists.view',
  PLAYLISTS_CREATE: 'playlists.create',
  PLAYLISTS_EDIT: 'playlists.edit',
  PLAYLISTS_DELETE: 'playlists.delete',

  // Tag Permissions
  TAGS_VIEW: 'tags.view',
  TAGS_CREATE: 'tags.create',
  TAGS_EDIT: 'tags.edit',
  TAGS_DELETE: 'tags.delete',

  // User Permissions
  USERS_VIEW: 'users.view',
  USERS_CREATE: 'users.create',
  USERS_EDIT: 'users.edit',
  USERS_DELETE: 'users.delete',
  USERS_INVITE: 'users.invite',

  // Organization Permissions
  ORGANIZATION_VIEW: 'organization.view',
  ORGANIZATION_EDIT: 'organization.edit',
  ORGANIZATION_DELETE: 'organization.delete',

  // Settings Permissions
  SETTINGS_VIEW: 'settings.view',
  SETTINGS_EDIT: 'settings.edit',

  // Activity Log Permissions
  ACTIVITIES_VIEW: 'activities.view',
  ACTIVITIES_DELETE: 'activities.delete',

  // Widget Permissions
  WIDGETS_VIEW: 'widgets.view',
  WIDGETS_CREATE: 'widgets.create',
  WIDGETS_EDIT: 'widgets.edit',
  WIDGETS_DELETE: 'widgets.delete'
}
```

#### Role Constants
```javascript
// utils/roles.js
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ORG_ADMIN: 'org_admin',
  EDITOR: 'editor',
  VIEWER: 'viewer'
}

export const ROLE_LABELS = {
  [ROLES.SUPER_ADMIN]: 'Super Admin',
  [ROLES.ORG_ADMIN]: 'Organization Admin',
  [ROLES.EDITOR]: 'Editor',
  [ROLES.VIEWER]: 'Viewer'
}

export const ROLE_DESCRIPTIONS = {
  [ROLES.SUPER_ADMIN]: 'Full system access across all organizations',
  [ROLES.ORG_ADMIN]: 'Manage organization, users, and all content',
  [ROLES.EDITOR]: 'Create and manage content, devices, and playlists',
  [ROLES.VIEWER]: 'View-only access to organization resources'
}

export const ROLE_COLORS = {
  [ROLES.SUPER_ADMIN]: 'purple',
  [ROLES.ORG_ADMIN]: 'blue',
  [ROLES.EDITOR]: 'green',
  [ROLES.VIEWER]: 'gray'
}

// Role hierarchy for permission inheritance
export const ROLE_HIERARCHY = {
  [ROLES.SUPER_ADMIN]: 100,
  [ROLES.ORG_ADMIN]: 75,
  [ROLES.EDITOR]: 50,
  [ROLES.VIEWER]: 25
}
```

#### Permission Gates (HOCs)

```javascript
// components/permissions/PermissionGate.jsx
import { useAuth } from '../../hooks/useAuth'

export default function PermissionGate({
  permission,
  children,
  fallback = null
}) {
  const { checkPermission } = useAuth()

  if (!checkPermission(permission)) {
    return fallback
  }

  return children
}

// Usage:
<PermissionGate permission={PERMISSIONS.USERS_CREATE}>
  <Button onClick={handleCreateUser}>Create User</Button>
</PermissionGate>
```

```javascript
// components/permissions/RoleGate.jsx
import { useAuth } from '../../hooks/useAuth'

export default function RoleGate({
  role,
  minRole,
  children,
  fallback = null
}) {
  const { hasRole, user } = useAuth()

  if (role && !hasRole(role)) {
    return fallback
  }

  if (minRole && ROLE_HIERARCHY[user.role] < ROLE_HIERARCHY[minRole]) {
    return fallback
  }

  return children
}

// Usage:
<RoleGate role={ROLES.ORG_ADMIN}>
  <OrganizationSettings />
</RoleGate>

<RoleGate minRole={ROLES.EDITOR}>
  <EditButton />
</RoleGate>
```

### Token Management

#### JWT Token Structure
```javascript
{
  access_token: string,      // Short-lived (15 mins)
  refresh_token: string,     // Long-lived (7 days)
  token_type: 'bearer',
  expires_in: number,        // Seconds until expiration
  user: {
    id: number,
    email: string,
    organization_id: number
  }
}
```

#### Token Refresh Strategy
```javascript
// services/auth.service.js
class AuthService {
  constructor() {
    this.refreshTimer = null
  }

  // Schedule token refresh before expiration
  scheduleTokenRefresh(expiresIn) {
    // Refresh 1 minute before expiration
    const refreshTime = (expiresIn - 60) * 1000

    this.refreshTimer = setTimeout(() => {
      this.refreshToken()
    }, refreshTime)
  }

  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      const response = await api.post('/api/auth/refresh', {
        refresh_token: refreshToken
      })

      const { access_token, refresh_token, expires_in } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)

      this.scheduleTokenRefresh(expires_in)

      return access_token
    } catch (error) {
      this.logout()
      throw error
    }
  }

  logout() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
    }
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  }
}
```

#### Axios Interceptor Updates
```javascript
// services/api.js - Updated interceptor
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const response = await api.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })

        const { access_token } = response.data
        localStorage.setItem('token', access_token)

        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        processQueue(null, access_token)

        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)
```

---

## API Integration

### Updated API Service Structure

```javascript
// services/api.js - Updated with organization support

// Add organization context to all requests
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    const orgId = localStorage.getItem('current_organization_id')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    if (orgId) {
      config.headers['X-Organization-Id'] = orgId
    }

    return config
  },
  error => Promise.reject(error)
)

// Enhanced Auth API
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
  refresh: (refreshToken) => api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  resetPassword: (token, password) => api.post('/api/auth/reset-password', { token, password }),
  verifyEmail: (token) => api.post('/api/auth/verify-email', { token }),
  resendVerification: (email) => api.post('/api/auth/resend-verification', { email }),
  changePassword: (data) => api.post('/api/auth/change-password', data)
}

// NEW - Users API
export const usersAPI = {
  list: (params) => api.get('/api/users', { params }),
  get: (id) => api.get(`/api/users/${id}`),
  create: (data) => api.post('/api/users', data),
  update: (id, data) => api.patch(`/api/users/${id}`, data),
  delete: (id) => api.delete(`/api/users/${id}`),
  invite: (data) => api.post('/api/users/invite', data),
  resendInvite: (id) => api.post(`/api/users/${id}/resend-invite`),
  updateRole: (id, role) => api.patch(`/api/users/${id}/role`, { role }),
  updateStatus: (id, isActive) => api.patch(`/api/users/${id}/status`, { is_active: isActive }),
  resetPassword: (id) => api.post(`/api/users/${id}/reset-password`),
  getPermissions: (id) => api.get(`/api/users/${id}/permissions`),
  updatePermissions: (id, permissions) => api.put(`/api/users/${id}/permissions`, { permissions }),
  getActivity: (id, params) => api.get(`/api/users/${id}/activity`, { params })
}

// NEW - Organizations API
export const organizationsAPI = {
  list: (params) => api.get('/api/organizations', { params }),
  get: (id) => api.get(`/api/organizations/${id}`),
  create: (data) => api.post('/api/organizations', data),
  update: (id, data) => api.patch(`/api/organizations/${id}`, data),
  delete: (id) => api.delete(`/api/organizations/${id}`),
  getStats: (id) => api.get(`/api/organizations/${id}/stats`),
  getUsers: (id, params) => api.get(`/api/organizations/${id}/users`, { params }),
  getSettings: (id) => api.get(`/api/organizations/${id}/settings`),
  updateSettings: (id, settings) => api.patch(`/api/organizations/${id}/settings`, settings),
  getLimits: (id) => api.get(`/api/organizations/${id}/limits`),
  switch: (id) => api.post(`/api/organizations/${id}/switch`)
}

// NEW - Profile API
export const profileAPI = {
  get: () => api.get('/api/profile'),
  update: (data) => api.patch('/api/profile', data),
  updateAvatar: (formData) => api.post('/api/profile/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteAvatar: () => api.delete('/api/profile/avatar'),
  changePassword: (data) => api.post('/api/profile/change-password', data),
  getOrganizations: () => api.get('/api/profile/organizations'),
  getActivity: (params) => api.get('/api/profile/activity', { params })
}

// Update existing APIs to be organization-aware (automatic via interceptor)
```

---

## UI/UX Design Specifications

### 1. Enhanced Layout with Organization Context

#### Topbar (NEW)
```
┌────────────────────────────────────────────────────────────────┐
│ [Signage Admin]    [Org: Acme Corp ▼]    [🔍Search]  [👤 John] │
└────────────────────────────────────────────────────────────────┘
```

**Features**:
- Organization switcher (dropdown)
- Global search (future enhancement)
- User profile dropdown
- Notifications icon (future)
- Dark mode toggle

#### Organization Switcher Component
```javascript
// components/organizations/OrganizationSwitcher.jsx
<Dropdown>
  <DropdownTrigger>
    <button className="flex items-center gap-2">
      <Building2 className="w-4 h-4" />
      <span className="font-medium">{currentOrg.name}</span>
      <ChevronDown className="w-4 h-4" />
    </button>
  </DropdownTrigger>

  <DropdownMenu>
    <DropdownItem>
      <span className="text-xs text-gray-500">Current Organization</span>
      <div className="font-medium">{currentOrg.name}</div>
    </DropdownItem>

    <DropdownDivider />

    {otherOrgs.map(org => (
      <DropdownItem key={org.id} onClick={() => switchOrg(org.id)}>
        <div className="flex items-center justify-between">
          <span>{org.name}</span>
          <Badge>{org.role}</Badge>
        </div>
      </DropdownItem>
    ))}

    <DropdownDivider />

    {hasRole('super_admin') && (
      <DropdownItem onClick={() => navigate('/organizations')}>
        <Settings className="w-4 h-4 mr-2" />
        Manage Organizations
      </DropdownItem>
    )}
  </DropdownMenu>
</Dropdown>
```

#### Profile Dropdown Component
```javascript
// components/profile/ProfileDropdown.jsx
<Dropdown align="right">
  <DropdownTrigger>
    <button className="flex items-center gap-2">
      <Avatar src={user.avatar} name={user.full_name} size="sm" />
      <div className="text-left">
        <div className="text-sm font-medium">{user.full_name}</div>
        <div className="text-xs text-gray-500">{roleLabel}</div>
      </div>
    </button>
  </DropdownTrigger>

  <DropdownMenu>
    <DropdownItem onClick={() => navigate('/profile')}>
      <User className="w-4 h-4 mr-2" />
      My Profile
    </DropdownItem>

    <DropdownItem onClick={() => navigate('/settings')}>
      <Settings className="w-4 h-4 mr-2" />
      Settings
    </DropdownItem>

    <DropdownDivider />

    <DropdownItem onClick={handleLogout} variant="danger">
      <LogOut className="w-4 h-4 mr-2" />
      Logout
    </DropdownItem>
  </DropdownMenu>
</Dropdown>
```

### 2. Users Management Page

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ Users                                            [+ Invite User] │
│ Manage team members and their permissions                       │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [🔍 Search users...]  [Role ▼] [Status ▼] [Clear Filters]      │
│                                                                  │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Name              Email            Role      Status  ⋮   │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ [JD] John Doe     john@ex.com     Admin     Active   ⋮   │  │
│ │ [JS] Jane Smith   jane@ex.com     Editor    Active   ⋮   │  │
│ │ [BJ] Bob Jones    bob@ex.com      Viewer    Pending  ⋮   │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│                          [← 1 2 3 →]                            │
└────────────────────────────────────────────────────────────────┘
```

#### User Table Row
```javascript
// components/users/UserTableRow.jsx
<tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
  <td className="px-6 py-4">
    <div className="flex items-center gap-3">
      <Avatar src={user.avatar} name={user.full_name} size="md" />
      <div>
        <div className="font-medium text-gray-900 dark:text-white">
          {user.full_name}
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {user.username}
        </div>
      </div>
    </div>
  </td>

  <td className="px-6 py-4">
    <div className="text-sm text-gray-900 dark:text-white">
      {user.email}
    </div>
    {!user.email_verified && (
      <Badge variant="warning" size="sm" className="mt-1">
        Not Verified
      </Badge>
    )}
  </td>

  <td className="px-6 py-4">
    <UserRoleBadge role={user.role} />
  </td>

  <td className="px-6 py-4">
    <UserStatusBadge status={user.status} />
  </td>

  <td className="px-6 py-4">
    <div className="text-sm text-gray-500 dark:text-gray-400">
      {formatDate(user.last_login)}
    </div>
  </td>

  <td className="px-6 py-4">
    <DropdownMenu>
      <DropdownItem onClick={() => handleView(user.id)}>
        <Eye className="w-4 h-4" />
        View Details
      </DropdownItem>

      <PermissionGate permission={PERMISSIONS.USERS_EDIT}>
        <DropdownItem onClick={() => handleEdit(user.id)}>
          <Edit className="w-4 h-4" />
          Edit User
        </DropdownItem>
      </PermissionGate>

      <PermissionGate permission={PERMISSIONS.USERS_EDIT}>
        <DropdownItem onClick={() => handleResetPassword(user.id)}>
          <Key className="w-4 h-4" />
          Reset Password
        </DropdownItem>
      </PermissionGate>

      <DropdownDivider />

      <PermissionGate permission={PERMISSIONS.USERS_DELETE}>
        <DropdownItem
          onClick={() => handleDelete(user.id)}
          variant="danger"
        >
          <Trash2 className="w-4 h-4" />
          Delete User
        </DropdownItem>
      </PermissionGate>
    </DropdownMenu>
  </td>
</tr>
```

#### Role Badge
```javascript
// components/users/UserRoleBadge.jsx
const roleConfig = {
  super_admin: {
    label: 'Super Admin',
    color: 'purple',
    icon: Shield
  },
  org_admin: {
    label: 'Admin',
    color: 'blue',
    icon: ShieldCheck
  },
  editor: {
    label: 'Editor',
    color: 'green',
    icon: Edit
  },
  viewer: {
    label: 'Viewer',
    color: 'gray',
    icon: Eye
  }
}

export default function UserRoleBadge({ role }) {
  const config = roleConfig[role] || roleConfig.viewer
  const Icon = config.icon

  return (
    <Badge variant={config.color} className="inline-flex items-center gap-1">
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  )
}
```

### 3. User Modals

#### Invite User Modal
```
┌───────────────────────────────────────────┐
│ Invite New User                      [✕]  │
├───────────────────────────────────────────┤
│                                            │
│ Email Address *                            │
│ [____________________________]             │
│                                            │
│ Full Name *                                │
│ [____________________________]             │
│                                            │
│ Role *                                     │
│ [Select role ▼                ]            │
│ ┌──────────────────────────────────────┐ │
│ │ • Super Admin                         │ │
│ │   Full system access                  │ │
│ │ ○ Organization Admin                  │ │
│ │   Manage org and users                │ │
│ │ ○ Editor                              │ │
│ │   Create and manage content           │ │
│ │ ○ Viewer                              │ │
│ │   View-only access                    │ │
│ └──────────────────────────────────────┘ │
│                                            │
│ Send invitation email                      │
│ [✓] Send welcome email with login link    │
│                                            │
├───────────────────────────────────────────┤
│              [Cancel]  [Send Invite]       │
└───────────────────────────────────────────┘
```

#### User Detail Modal
```
┌─────────────────────────────────────────────────────┐
│ User Details                                   [✕]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌──────────┐                                        │
│ │   [JD]   │  John Doe                              │
│ └──────────┘  john.doe@example.com                  │
│               [Admin]  [Active]                     │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Information                                   │   │
│ ├──────────────────────────────────────────────┤   │
│ │ Username         john.doe                     │   │
│ │ Email            john.doe@example.com         │   │
│ │ Full Name        John Doe                     │   │
│ │ Role             Organization Admin           │   │
│ │ Status           Active                       │   │
│ │ Email Verified   Yes                          │   │
│ │ Created At       Jan 15, 2025 10:30 AM        │   │
│ │ Last Login       Jan 27, 2025 2:45 PM         │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Permissions (12 total)                        │   │
│ ├──────────────────────────────────────────────┤   │
│ │ ✓ Devices    ✓ Content    ✓ Playlists        │   │
│ │ ✓ Tags       ✓ Users      ✓ Settings         │   │
│ │ ✓ Activities ✓ Widgets                        │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Recent Activity                               │   │
│ ├──────────────────────────────────────────────┤   │
│ │ • Updated device "Lobby Display"              │   │
│ │   2 hours ago                                 │   │
│ │ • Uploaded content "promo-video.mp4"          │   │
│ │   5 hours ago                                 │   │
│ │ • Created playlist "Weekly Promotions"        │   │
│ │   Yesterday at 3:30 PM                        │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
├─────────────────────────────────────────────────────┤
│         [Edit User]  [Reset Password]  [Close]      │
└─────────────────────────────────────────────────────┘
```

### 4. Enhanced Login Page

```
┌────────────────────────────────────────────┐
│                                             │
│              [Logo/Icon]                    │
│           Signage Admin                     │
│      Smart TV Digital Signage               │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Email or Username                   │    │
│  │ [____________________________]      │    │
│  │                                      │    │
│  │ Password                             │    │
│  │ [____________________________] [👁]  │    │
│  │                                      │    │
│  │ [✓] Remember me                      │    │
│  │                                      │    │
│  │        [Login]                       │    │
│  │                                      │    │
│  │      Forgot password?                │    │
│  └────────────────────────────────────┘    │
│                                             │
│  Multi-organization support • Secure login  │
└────────────────────────────────────────────┘
```

**Features**:
- Support for email or username login
- Password visibility toggle
- Remember me checkbox
- Forgot password link
- Loading state during login
- Clear error messages
- Organization context (if provided via URL param)

### 5. Settings Page Updates

#### New Organization Tab
```
┌────────────────────────────────────────────────────────────────┐
│ Settings                                                        │
│ [Users] [Organization] [System] [Profile]                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Organization Settings                                            │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ General Information                                       │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ Organization Name    [Acme Corporation          ]        │  │
│ │ Slug                 [acme-corp                 ]        │  │
│ │ Status               [●] Active                          │  │
│ │                                                           │  │
│ │ Branding                                                  │  │
│ │ Logo                 [Upload Logo] logo.png              │  │
│ │ Primary Color        [#3B82F6] ███                       │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Resource Limits                                           │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ Max Devices          25 / 50                              │  │
│ │ Max Users            8 / 25                               │  │
│ │ Storage              45 GB / 100 GB                       │  │
│ │ [███████████░░░░░░░░] 45%                                │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Features                                                  │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ [✓] Device Management                                     │  │
│ │ [✓] Content Management                                    │  │
│ │ [✓] Advanced Analytics                                    │  │
│ │ [✓] Multi-user Support                                    │  │
│ │ [✓] API Access                                            │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│                              [Save Changes]                     │
└────────────────────────────────────────────────────────────────┘
```

### 6. Color Palette & Design Tokens

```javascript
// Existing colors + new additions
const colors = {
  // Role colors
  role: {
    super_admin: '#9333EA',  // purple-600
    org_admin: '#3B82F6',    // blue-600
    editor: '#10B981',       // green-600
    viewer: '#6B7280'        // gray-600
  },

  // Status colors
  status: {
    active: '#10B981',       // green-600
    inactive: '#6B7280',     // gray-600
    pending: '#F59E0B',      // amber-600
    suspended: '#EF4444'     // red-600
  },

  // Permission colors
  permission: {
    granted: '#10B981',      // green-600
    denied: '#EF4444',       // red-600
    inherited: '#3B82F6'     // blue-600
  }
}
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1)
**Goal**: Set up authentication infrastructure without breaking existing functionality

#### Tasks:
1. **Create Auth Context**
   - Create `/src/contexts/AuthContext.jsx`
   - Implement basic auth state management
   - Create custom hooks (`useAuth`)

2. **Update API Service**
   - Add token refresh logic
   - Add organization header interceptor
   - Create auth service (`services/auth.service.js`)

3. **Create Route Protection**
   - Create `ProtectedRoute` component
   - Create `PermissionRoute` component
   - Create `RoleRoute` component

4. **Update App.jsx**
   - Wrap with new `AuthProvider`
   - Update route structure
   - Maintain backward compatibility

**Success Criteria**:
- Existing login still works
- All existing pages are accessible
- No breaking changes to current functionality

### Phase 2: User Management UI (Week 2)
**Goal**: Build user management interface

#### Tasks:
1. **Create Users Page**
   - User list table with pagination
   - Search and filter functionality
   - User statistics cards

2. **Create User Modals**
   - User detail modal
   - User edit modal
   - User create/invite modal
   - User delete confirmation

3. **Create User Components**
   - `UserTable.jsx`
   - `UserTableRow.jsx`
   - `UserRoleBadge.jsx`
   - `UserStatusBadge.jsx`
   - `UserFilters.jsx`

4. **Add Users Route**
   - Add `/users` route to App.jsx
   - Add "Users" to navigation (conditional based on permission)
   - Create API integration

**Success Criteria**:
- Users page displays list of users
- Can filter and search users
- Modals open and display data
- CRUD operations work (if backend ready)

### Phase 3: Organization Support (Week 3)
**Goal**: Add multi-organization functionality

#### Tasks:
1. **Create Organization Context**
   - Create `OrganizationContext.jsx`
   - Implement organization switching
   - Create custom hooks

2. **Update Layout**
   - Add organization switcher to topbar
   - Add profile dropdown
   - Extract header and sidebar components

3. **Create Organization Components**
   - `OrganizationSwitcher.jsx`
   - `OrganizationCard.jsx`
   - `OrganizationStats.jsx`

4. **Add Organization Settings**
   - Add organization tab to Settings page
   - Create organization edit modal
   - Add organization limits display

**Success Criteria**:
- Can switch between organizations
- Organization context persists
- All API calls include org header
- Settings page shows org info

### Phase 4: Enhanced Auth Flows (Week 4)
**Goal**: Complete authentication experience

#### Tasks:
1. **Create Auth Pages**
   - Forgot password page
   - Reset password page
   - Email verification page

2. **Update Login Page**
   - Add forgot password link
   - Add email verification prompt
   - Improve error handling
   - Add loading states

3. **Create Profile Management**
   - Profile page
   - Profile edit modal
   - Change password modal
   - Avatar upload

4. **Implement Token Refresh**
   - Add automatic token refresh
   - Handle refresh failures
   - Show session expiry warnings

**Success Criteria**:
- Complete auth flow works end-to-end
- Password reset works
- Email verification works
- Token refresh is automatic
- Session management is smooth

### Phase 5: Permissions & Authorization (Week 5)
**Goal**: Implement permission-based UI rendering

#### Tasks:
1. **Create Permission System**
   - Define permission constants
   - Define role constants
   - Create permission utilities

2. **Implement Permission Gates**
   - `PermissionGate` component
   - `RoleGate` component
   - Custom hooks for permission checks

3. **Update All Pages**
   - Add permission checks to buttons
   - Hide features based on permissions
   - Show appropriate empty states

4. **Update Navigation**
   - Filter nav items by permission
   - Show permission badges
   - Add role-based routing

**Success Criteria**:
- UI updates based on user permissions
- Unauthorized actions are hidden
- Navigation reflects available features
- Appropriate error messages shown

### Phase 6: Polish & Testing (Week 6)
**Goal**: Refinement and quality assurance

#### Tasks:
1. **UI Polish**
   - Consistent styling across all pages
   - Smooth animations and transitions
   - Loading states everywhere
   - Error boundary implementation

2. **Accessibility**
   - Keyboard navigation
   - Screen reader support
   - Focus management
   - ARIA labels

3. **Performance**
   - Code splitting
   - Lazy loading routes
   - Image optimization
   - Cache optimization

4. **Testing**
   - Test all auth flows
   - Test permission system
   - Test organization switching
   - Cross-browser testing

**Success Criteria**:
- All features work smoothly
- UI is consistent and polished
- Performance is optimized
- Accessibility requirements met

### Migration Checklist

```markdown
## Phase 1: Foundation
- [ ] Create AuthContext.jsx
- [ ] Create useAuth hook
- [ ] Update api.js with token refresh
- [ ] Create auth.service.js
- [ ] Create ProtectedRoute component
- [ ] Create PermissionRoute component
- [ ] Create RoleRoute component
- [ ] Update App.jsx with AuthProvider
- [ ] Test existing login flow
- [ ] Verify all existing pages work

## Phase 2: User Management
- [ ] Create Users page
- [ ] Create UserTable component
- [ ] Create UserTableRow component
- [ ] Create UserRoleBadge component
- [ ] Create UserStatusBadge component
- [ ] Create UserFilters component
- [ ] Create UserDetailModal
- [ ] Create UserEditModal
- [ ] Create InviteUserModal
- [ ] Create UserDeleteConfirmModal
- [ ] Add users route to App.jsx
- [ ] Add Users to navigation
- [ ] Integrate with users API
- [ ] Test CRUD operations

## Phase 3: Organization Support
- [ ] Create OrganizationContext.jsx
- [ ] Create useOrganization hook
- [ ] Create OrganizationSwitcher component
- [ ] Create ProfileDropdown component
- [ ] Update Layout with topbar
- [ ] Extract Header component
- [ ] Extract Sidebar component
- [ ] Create organization tab in Settings
- [ ] Create OrganizationEditModal
- [ ] Test organization switching
- [ ] Verify API calls include org header

## Phase 4: Enhanced Auth
- [ ] Create ForgotPassword page
- [ ] Create ResetPassword page
- [ ] Create VerifyEmail page
- [ ] Update Login page with enhancements
- [ ] Create Profile page
- [ ] Create ProfileEditModal
- [ ] Create ChangePasswordModal
- [ ] Implement token refresh logic
- [ ] Test forgot password flow
- [ ] Test email verification
- [ ] Test token refresh

## Phase 5: Permissions
- [ ] Create permissions.js constants
- [ ] Create roles.js constants
- [ ] Create PermissionGate component
- [ ] Create RoleGate component
- [ ] Create usePermission hook
- [ ] Update all pages with permission checks
- [ ] Update navigation with filtering
- [ ] Update buttons with permission gates
- [ ] Test permission system
- [ ] Test role-based access

## Phase 6: Polish
- [ ] Consistent styling review
- [ ] Add animations and transitions
- [ ] Add loading states everywhere
- [ ] Implement error boundaries
- [ ] Keyboard navigation testing
- [ ] Screen reader testing
- [ ] Focus management
- [ ] Code splitting implementation
- [ ] Lazy loading routes
- [ ] Performance testing
- [ ] Cross-browser testing
- [ ] Final QA pass
```

---

## Implementation Checklist

### Immediate Next Steps

1. **Install Additional Dependencies** (if needed)
   ```bash
   npm install zustand         # Optional: For lightweight state management
   npm install jwt-decode      # For JWT token parsing
   npm install react-hook-form # For form management
   npm install zod             # For validation
   ```

2. **Create Directory Structure**
   ```bash
   mkdir -p src/contexts
   mkdir -p src/hooks
   mkdir -p src/components/auth
   mkdir -p src/components/users
   mkdir -p src/components/organizations
   mkdir -p src/components/profile
   mkdir -p src/components/permissions
   mkdir -p src/components/routing
   mkdir -p src/components/layout
   mkdir -p src/services
   mkdir -p src/utils
   mkdir -p src/pages
   ```

3. **Start with Phase 1**
   - Create `AuthContext.jsx`
   - Create `useAuth.js` hook
   - Update `api.js` with enhanced interceptors
   - Create route protection components

4. **Backend Coordination**
   - Ensure backend API endpoints match frontend expectations
   - Coordinate on JWT token structure
   - Agree on permission naming conventions
   - Define organization switching mechanism

---

## Best Practices & Guidelines

### Code Organization
1. **Component Structure**:
   - One component per file
   - Co-locate related components in folders
   - Use index.js for public exports

2. **State Management**:
   - Use Context for global state (auth, org)
   - Use React Query for server state
   - Use local state for UI state

3. **Naming Conventions**:
   - Components: PascalCase (UserTable.jsx)
   - Hooks: camelCase with 'use' prefix (useAuth.js)
   - Utilities: camelCase (formatters.js)
   - Constants: UPPER_SNAKE_CASE (PERMISSIONS.USERS_VIEW)

### Performance Optimization
1. **Code Splitting**:
   ```javascript
   const Users = lazy(() => import('./pages/Users'))
   const Organizations = lazy(() => import('./pages/Organizations'))
   ```

2. **Memoization**:
   ```javascript
   const filteredUsers = useMemo(() =>
     users.filter(u => u.name.includes(search)),
     [users, search]
   )
   ```

3. **Query Optimization**:
   ```javascript
   const { data } = useQuery({
     queryKey: ['users', filters],
     queryFn: () => usersAPI.list(filters),
     staleTime: 5 * 60 * 1000,  // 5 minutes
     cacheTime: 10 * 60 * 1000   // 10 minutes
   })
   ```

### Security Considerations
1. **Never store sensitive data in localStorage**
2. **Always validate permissions server-side**
3. **UI permissions are for UX, not security**
4. **Clear tokens on logout**
5. **Handle token expiration gracefully**
6. **Validate all user inputs**
7. **Sanitize displayed data**

### Accessibility
1. **Keyboard Navigation**:
   - All interactive elements focusable
   - Logical tab order
   - Visible focus indicators

2. **ARIA Labels**:
   - Descriptive button labels
   - Form field labels
   - Dynamic content announcements

3. **Color Contrast**:
   - WCAG AA minimum (4.5:1 for text)
   - Don't rely solely on color
   - Test with color blindness simulators

---

## Conclusion

This architecture provides a solid foundation for multi-tenant user management with:

- **Scalability**: Support for multiple organizations and roles
- **Security**: JWT-based auth with token refresh and permission system
- **UX**: Smooth organization switching and clear permission boundaries
- **Maintainability**: Modular components and clear separation of concerns
- **Performance**: Optimized queries, code splitting, and caching

The phased migration approach ensures minimal disruption to existing functionality while progressively adding new features.

---

**Document Version**: 1.0
**Last Updated**: January 27, 2025
**Status**: Draft - Ready for Implementation
