# Multi-Tenant Frontend Implementation Guide

## Quick Start - Phase 1 Implementation

This guide provides ready-to-use code for implementing Phase 1 (Foundation) of the multi-tenant user management system.

---

## Step 1: Create Auth Context

### File: `/src/contexts/AuthContext.jsx`

```javascript
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI, profileAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [state, setState] = useState({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    token: null
  })

  const navigate = useNavigate()

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')

      if (token) {
        try {
          // Fetch current user data
          const response = await authAPI.me()
          setState({
            user: response.data,
            isAuthenticated: true,
            isLoading: false,
            token
          })
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            token: null
          })
        }
      } else {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          token: null
        })
      }
    }

    initAuth()
  }, [])

  // Login function
  const login = useCallback(async (credentials) => {
    try {
      const response = await authAPI.login(credentials)
      const { access_token, refresh_token, user } = response.data

      // Store tokens
      localStorage.setItem('token', access_token)
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token)
      }

      // Store current organization
      if (user.organization_id) {
        localStorage.setItem('current_organization_id', user.organization_id)
      }

      // Update state
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        token: access_token
      })

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }, [])

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout error:', error)
    } finally {
      // Clear storage
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_organization_id')

      // Reset state
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        token: null
      })

      // Redirect to login
      navigate('/login')
    }
  }, [navigate])

  // Refresh token function
  const refreshToken = useCallback(async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) {
        throw new Error('No refresh token')
      }

      const response = await authAPI.refresh(refresh)
      const { access_token, refresh_token } = response.data

      localStorage.setItem('token', access_token)
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token)
      }

      setState(prev => ({
        ...prev,
        token: access_token
      }))

      return access_token
    } catch (error) {
      logout()
      throw error
    }
  }, [logout])

  // Update user in state
  const updateUser = useCallback((userData) => {
    setState(prev => ({
      ...prev,
      user: { ...prev.user, ...userData }
    }))
  }, [])

  // Check if user has specific permission
  const checkPermission = useCallback((permission) => {
    if (!state.user) return false

    // Super admin has all permissions
    if (state.user.role === 'super_admin') return true

    // Check if permission exists in user's permissions array
    return state.user.permissions?.includes(permission) || false
  }, [state.user])

  // Check if user has specific role
  const hasRole = useCallback((role) => {
    if (!state.user) return false
    return state.user.role === role
  }, [state.user])

  // Check if user has minimum role level
  const hasMinRole = useCallback((minRole) => {
    if (!state.user) return false

    const roleHierarchy = {
      super_admin: 100,
      org_admin: 75,
      editor: 50,
      viewer: 25
    }

    return (roleHierarchy[state.user.role] || 0) >= (roleHierarchy[minRole] || 0)
  }, [state.user])

  const value = {
    ...state,
    login,
    logout,
    refreshToken,
    updateUser,
    checkPermission,
    hasRole,
    hasMinRole
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
```

---

## Step 2: Update App.jsx

### File: `/src/App.jsx`

```javascript
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Suspense, lazy } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'

// Components
import Layout from './components/Layout'
import LoadingSpinner from './components/common/LoadingSpinner'
import ProtectedRoute from './components/routing/ProtectedRoute'
import PermissionRoute from './components/routing/PermissionRoute'
import RoleRoute from './components/routing/RoleRoute'

// Pages - Immediate load
import Login from './pages/Login'

// Pages - Lazy load
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Devices = lazy(() => import('./pages/Devices'))
const DevicePreview = lazy(() => import('./pages/DevicePreview'))
const Content = lazy(() => import('./pages/Content'))
const Tags = lazy(() => import('./pages/Tags'))
const Playlists = lazy(() => import('./pages/Playlists'))
const Activities = lazy(() => import('./pages/Activities'))
const Widgets = lazy(() => import('./pages/Widgets'))
const Settings = lazy(() => import('./pages/Settings'))
const Users = lazy(() => import('./pages/Users'))
const Profile = lazy(() => import('./pages/Profile'))
const Organizations = lazy(() => import('./pages/Organizations'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AuthProvider>
            <Suspense fallback={<LoadingSpinner fullScreen />}>
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password/:token" element={<ResetPassword />} />
                <Route path="/verify-email/:token" element={<VerifyEmail />} />

                {/* Protected Routes */}
                <Route element={<ProtectedRoute />}>
                  <Route element={<Layout />}>
                    {/* Dashboard */}
                    <Route path="/" element={<Dashboard />} />

                    {/* Devices */}
                    <Route path="/devices" element={<Devices />} />

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

                    {/* Users - Requires permission */}
                    <Route
                      path="/users"
                      element={
                        <PermissionRoute permission="users.view">
                          <Users />
                        </PermissionRoute>
                      }
                    />

                    {/* Profile - Always accessible */}
                    <Route path="/profile" element={<Profile />} />

                    {/* Organizations - Super Admin only */}
                    <Route
                      path="/organizations"
                      element={
                        <RoleRoute role="super_admin">
                          <Organizations />
                        </RoleRoute>
                      }
                    />

                    {/* Settings */}
                    <Route path="/settings" element={<Settings />} />
                  </Route>

                  {/* Device Preview (without Layout) */}
                  <Route path="/devices/:id/preview" element={<DevicePreview />} />
                </Route>

                {/* 404 */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </AuthProvider>
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
```

---

## Step 3: Create Route Protection Components

### File: `/src/components/routing/ProtectedRoute.jsx`

```javascript
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
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

### File: `/src/components/routing/PermissionRoute.jsx`

```javascript
import { useAuth } from '../../contexts/AuthContext'

export default function PermissionRoute({ permission, children, fallback }) {
  const { checkPermission } = useAuth()

  if (!checkPermission(permission)) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen p-6">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              You don't have permission to access this page. Contact your administrator if you
              believe this is a mistake.
            </p>
          </div>
        </div>
      )
    )
  }

  return children
}
```

### File: `/src/components/routing/RoleRoute.jsx`

```javascript
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function RoleRoute({ role, minRole, children }) {
  const { hasRole, hasMinRole } = useAuth()

  if (role && !hasRole(role)) {
    return <Navigate to="/" replace />
  }

  if (minRole && !hasMinRole(minRole)) {
    return <Navigate to="/" replace />
  }

  return children
}
```

---

## Step 4: Create Permission Constants

### File: `/src/utils/permissions.js`

```javascript
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

### File: `/src/utils/roles.js`

```javascript
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

export const ROLE_HIERARCHY = {
  [ROLES.SUPER_ADMIN]: 100,
  [ROLES.ORG_ADMIN]: 75,
  [ROLES.EDITOR]: 50,
  [ROLES.VIEWER]: 25
}

export function getRoleLabel(role) {
  return ROLE_LABELS[role] || role
}

export function getRoleColor(role) {
  return ROLE_COLORS[role] || 'gray'
}

export function getRoleDescription(role) {
  return ROLE_DESCRIPTIONS[role] || ''
}

export function compareRoles(role1, role2) {
  return (ROLE_HIERARCHY[role1] || 0) - (ROLE_HIERARCHY[role2] || 0)
}
```

---

## Step 5: Update API Service

### File: `/src/services/api.js` (Updated)

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add auth token and org context
api.interceptors.request.use(
  (config) => {
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
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle token refresh
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request until token is refreshed
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')

        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        // Try to refresh the token
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: new_refresh } = response.data

        // Update stored tokens
        localStorage.setItem('token', access_token)
        if (new_refresh) {
          localStorage.setItem('refresh_token', new_refresh)
        }

        // Update default header
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        // Process queued requests
        processQueue(null, access_token)

        // Retry original request
        return api(originalRequest)
      } catch (refreshError) {
        // Token refresh failed - logout user
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_organization_id')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
  refresh: (refreshToken) => api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  resetPassword: (token, password) =>
    api.post('/api/auth/reset-password', { token, password }),
  verifyEmail: (token) => api.post('/api/auth/verify-email', { token }),
  resendVerification: (email) => api.post('/api/auth/resend-verification', { email }),
  changePassword: (data) => api.post('/api/auth/change-password', data),
}

// Users API
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
  updatePermissions: (id, permissions) =>
    api.put(`/api/users/${id}/permissions`, { permissions }),
  getActivity: (id, params) => api.get(`/api/users/${id}/activity`, { params }),
}

// Organizations API
export const organizationsAPI = {
  list: (params) => api.get('/api/organizations', { params }),
  get: (id) => api.get(`/api/organizations/${id}`),
  create: (data) => api.post('/api/organizations', data),
  update: (id, data) => api.patch(`/api/organizations/${id}`, data),
  delete: (id) => api.delete(`/api/organizations/${id}`),
  getStats: (id) => api.get(`/api/organizations/${id}/stats`),
  getUsers: (id, params) => api.get(`/api/organizations/${id}/users`, { params }),
  getSettings: (id) => api.get(`/api/organizations/${id}/settings`),
  updateSettings: (id, settings) =>
    api.patch(`/api/organizations/${id}/settings`, settings),
  getLimits: (id) => api.get(`/api/organizations/${id}/limits`),
  switch: (id) => api.post(`/api/organizations/${id}/switch`),
}

// Profile API
export const profileAPI = {
  get: () => api.get('/api/profile'),
  update: (data) => api.patch('/api/profile', data),
  updateAvatar: (formData) =>
    api.post('/api/profile/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deleteAvatar: () => api.delete('/api/profile/avatar'),
  changePassword: (data) => api.post('/api/profile/change-password', data),
  getOrganizations: () => api.get('/api/profile/organizations'),
  getActivity: (params) => api.get('/api/profile/activity', { params }),
}

// ... (rest of existing APIs - devices, content, tags, etc.)

export default api
```

---

## Step 6: Update Layout Component

### File: `/src/components/Layout.jsx` (Updated)

```javascript
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  Monitor,
  FileImage,
  LayoutDashboard,
  Tag,
  ListVideo,
  Puzzle,
  Settings,
  Menu,
  X,
  Sun,
  Moon,
  Clock,
  Users,
} from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { devicesAPI } from '../services/api'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { PERMISSIONS } from '../utils/permissions'
import ProfileDropdown from './profile/ProfileDropdown'

export default function Layout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { theme, toggleTheme, isDark } = useTheme()
  const { checkPermission, user } = useAuth()

  // Fetch devices to count pending approvals
  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesAPI.list().then((res) => res.data),
    staleTime: 30000,
    refetchInterval: 60000,
  })

  const pendingCount = devices?.devices?.filter((d) => d.status === 'pending').length || 0

  // Navigation items with permission checks
  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard, permission: null },
    { name: 'Devices', href: '/devices', icon: Monitor, permission: PERMISSIONS.DEVICES_VIEW },
    { name: 'Content', href: '/content', icon: FileImage, permission: PERMISSIONS.CONTENT_VIEW },
    {
      name: 'Playlists',
      href: '/playlists',
      icon: ListVideo,
      permission: PERMISSIONS.PLAYLISTS_VIEW,
    },
    { name: 'Tags', href: '/tags', icon: Tag, permission: PERMISSIONS.TAGS_VIEW },
    { name: 'Users', href: '/users', icon: Users, permission: PERMISSIONS.USERS_VIEW },
    {
      name: 'Activity Logs',
      href: '/activities',
      icon: Clock,
      permission: PERMISSIONS.ACTIVITIES_VIEW,
    },
    { name: 'Widgets', href: '/widgets', icon: Puzzle, permission: PERMISSIONS.WIDGETS_VIEW },
    { name: 'Settings', href: '/settings', icon: Settings, permission: null },
  ].filter((item) => !item.permission || checkPermission(item.permission))

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      {/* Mobile Burger Menu Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-[60] lg:hidden p-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg shadow-lg"
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 shadow-xl border-r border-gray-400 dark:border-gray-700 z-50 transform transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 bg-blue-600 dark:bg-blue-700">
            <h1 className="text-xl font-bold text-white">Signage Admin</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              const showBadge = item.name === 'Devices' && pendingCount > 0

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center">
                    <Icon className="w-5 h-5 mr-3" />
                    <span className="font-medium">{item.name}</span>
                  </div>
                  {showBadge && (
                    <span className="ml-auto bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5 animate-pulse">
                      {pendingCount}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Theme Toggle */}
          <div className="p-4 border-t dark:border-gray-700 space-y-2">
            <button
              onClick={toggleTheme}
              className="flex items-center w-full px-4 py-3 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <>
                  <Sun className="w-5 h-5 mr-3" />
                  <span className="font-medium">Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-5 h-5 mr-3" />
                  <span className="font-medium">Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Top Bar with Profile */}
        <div className="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex-1" />
            <ProfileDropdown />
          </div>
        </div>

        {/* Page Content */}
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

---

## Step 7: Create Profile Dropdown Component

### File: `/src/components/profile/ProfileDropdown.jsx`

```javascript
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Settings, LogOut, ChevronDown } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { getRoleLabel, getRoleColor } from '../../utils/roles'

export default function ProfileDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    setIsOpen(false)
    await logout()
  }

  const roleColor = getRoleColor(user?.role)
  const roleColorClasses = {
    purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    gray: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        {/* Avatar */}
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-medium">
          {user?.full_name?.charAt(0).toUpperCase() || 'U'}
        </div>

        {/* User Info */}
        <div className="text-left hidden md:block">
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {user?.full_name || 'User'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {getRoleLabel(user?.role)}
          </div>
        </div>

        {/* Chevron */}
        <ChevronDown
          className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-2 z-50">
          {/* User Info Header */}
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div className="font-medium text-gray-900 dark:text-white">
              {user?.full_name}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {user?.email}
            </div>
            <span
              className={`inline-block mt-2 px-2 py-1 text-xs font-medium rounded ${
                roleColorClasses[roleColor]
              }`}
            >
              {getRoleLabel(user?.role)}
            </span>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <button
              onClick={() => {
                setIsOpen(false)
                navigate('/profile')
              }}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <User className="w-4 h-4" />
              My Profile
            </button>

            <button
              onClick={() => {
                setIsOpen(false)
                navigate('/settings')
              }}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>

          {/* Logout */}
          <div className="border-t border-gray-200 dark:border-gray-700 py-1">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## Step 8: Update Login Page

### File: `/src/pages/Login.jsx` (Updated)

```javascript
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Monitor, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import Button from '../components/shared/Button'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await login(credentials)

      if (result.success) {
        navigate('/')
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700 p-4">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Monitor className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
            Signage Admin
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Smart TV Digital Signage
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email or Username
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) =>
                setCredentials({ ...credentials, username: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              placeholder="Enter your email or username"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={credentials.password}
                onChange={(e) =>
                  setCredentials({ ...credentials, password: e.target.value })
                }
                className="w-full px-4 py-2 pr-12 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter your password"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={loading}
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Remember me
              </span>
            </label>

            <Link
              to="/forgot-password"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={loading}
            loading={loading}
            fullWidth
          >
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Multi-tenant • Secure • Scalable
          </p>
        </div>
      </div>
    </div>
  )
}
```

---

## Testing Phase 1 Implementation

### Checklist

```markdown
## Phase 1 Implementation Testing

### 1. Auth Context
- [ ] Auth context initializes correctly
- [ ] User state loads from token on app start
- [ ] Login updates auth state
- [ ] Logout clears state and redirects
- [ ] checkPermission works correctly
- [ ] hasRole works correctly

### 2. Route Protection
- [ ] Unauthenticated users redirect to /login
- [ ] Authenticated users can access protected routes
- [ ] PermissionRoute blocks unauthorized access
- [ ] RoleRoute blocks users without required role
- [ ] Proper error messages shown

### 3. API Integration
- [ ] Token added to requests automatically
- [ ] Organization header added when available
- [ ] 401 errors trigger token refresh
- [ ] Failed refresh logs out user
- [ ] All existing API calls still work

### 4. Layout Updates
- [ ] Navigation filters by permissions
- [ ] Users with no permission don't see link
- [ ] Profile dropdown displays correctly
- [ ] Profile dropdown menu works
- [ ] Logout from dropdown works

### 5. Login Updates
- [ ] Login form submits correctly
- [ ] Error messages display
- [ ] Loading state works
- [ ] Password visibility toggle works
- [ ] Remember me checkbox present
- [ ] Forgot password link present
```

---

## Next Steps

After Phase 1 is complete and tested:

1. **Phase 2**: Build Users page with table, filters, and modals
2. **Phase 3**: Add Organization support with context and switcher
3. **Phase 4**: Implement auth flows (forgot password, reset, verify email)
4. **Phase 5**: Add permission gates throughout the application
5. **Phase 6**: Polish, accessibility, and performance optimization

---

## Common Issues & Solutions

### Issue: "useAuth must be used within AuthProvider"
**Solution**: Ensure AuthProvider wraps your component tree in App.jsx

### Issue: Token refresh causes infinite loop
**Solution**: Check that originalRequest._retry flag is set correctly

### Issue: Navigation doesn't filter by permissions
**Solution**: Ensure user.permissions array is populated from backend

### Issue: Profile dropdown doesn't show user data
**Solution**: Verify authAPI.me() returns correct user structure

### Issue: Routes still accessible without permission
**Solution**: Remember that frontend permissions are for UX only - backend must enforce

---

## Additional Resources

- **React Router v6 Docs**: https://reactrouter.com/
- **React Query Docs**: https://tanstack.com/query/latest
- **Axios Interceptors**: https://axios-http.com/docs/interceptors
- **Context API**: https://react.dev/reference/react/useContext

---

**Document Version**: 1.0
**Phase**: 1 - Foundation
**Status**: Ready for Implementation
