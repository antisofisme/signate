# Component Hierarchy & Data Flow

## Application Component Tree

```
App
├── ThemeProvider
│   └── QueryClientProvider
│       └── AuthProvider ⭐ NEW
│           └── OrganizationProvider ⭐ NEW
│               └── Router
│                   ├── Public Routes
│                   │   ├── /login → Login
│                   │   ├── /forgot-password → ForgotPassword
│                   │   ├── /reset-password/:token → ResetPassword
│                   │   └── /verify-email/:token → VerifyEmail
│                   │
│                   └── Protected Routes (ProtectedRoute wrapper)
│                       └── Layout
│                           ├── Header ⭐ NEW
│                           │   ├── Logo
│                           │   ├── OrganizationSwitcher ⭐ NEW
│                           │   │   └── OrganizationDropdown
│                           │   ├── GlobalSearch (future)
│                           │   └── ProfileDropdown ⭐ NEW
│                           │       ├── UserAvatar
│                           │       ├── UserInfo
│                           │       └── MenuItems
│                           │
│                           ├── Sidebar ⭐ UPDATED
│                           │   ├── Navigation
│                           │   │   └── NavItem (with permission filtering)
│                           │   ├── ThemeToggle
│                           │   └── LogoutButton
│                           │
│                           └── Main Content Area
│                               ├── / → Dashboard
│                               │   ├── StatsCards
│                               │   ├── DeviceStatus
│                               │   ├── RecentActivity
│                               │   └── TopTags
│                               │
│                               ├── /devices → Devices
│                               │   ├── DeviceFilters
│                               │   ├── DeviceTable
│                               │   └── DeviceModals
│                               │
│                               ├── /content → Content
│                               │   ├── ContentToolbar
│                               │   ├── ContentGrid
│                               │   └── ContentModals
│                               │
│                               ├── /playlists → Playlists
│                               │   ├── PlaylistList
│                               │   └── PlaylistModals
│                               │
│                               ├── /tags → Tags
│                               │   ├── TagList
│                               │   └── TagModals
│                               │
│                               ├── /users → Users ⭐ NEW
│                               │   ├── UserStats ⭐ NEW
│                               │   ├── UserFilters ⭐ NEW
│                               │   │   ├── SearchInput
│                               │   │   ├── RoleFilter
│                               │   │   ├── StatusFilter
│                               │   │   └── ClearButton
│                               │   ├── UserTable ⭐ NEW
│                               │   │   ├── TableHeader
│                               │   │   ├── UserTableRow (multiple)
│                               │   │   │   ├── UserAvatar
│                               │   │   │   ├── UserInfo
│                               │   │   │   ├── UserRoleBadge
│                               │   │   │   ├── UserStatusBadge
│                               │   │   │   └── ActionMenu
│                               │   │   └── TableFooter
│                               │   ├── Pagination ⭐ NEW
│                               │   ├── InviteUserButton ⭐ NEW
│                               │   └── Modals ⭐ NEW
│                               │       ├── UserDetailModal
│                               │       ├── UserEditModal
│                               │       ├── InviteUserModal
│                               │       ├── UserPermissionsModal
│                               │       └── UserDeleteConfirmModal
│                               │
│                               ├── /profile → Profile ⭐ NEW
│                               │   ├── ProfileHeader ⭐ NEW
│                               │   ├── ProfileInfo ⭐ NEW
│                               │   ├── OrganizationsList ⭐ NEW
│                               │   ├── ActivityTimeline ⭐ NEW
│                               │   └── Modals ⭐ NEW
│                               │       ├── ProfileEditModal
│                               │       ├── ChangePasswordModal
│                               │       └── AvatarUploadModal
│                               │
│                               ├── /organizations → Organizations ⭐ NEW (Super Admin)
│                               │   ├── OrganizationGrid ⭐ NEW
│                               │   ├── OrganizationCard ⭐ NEW
│                               │   │   ├── OrgLogo
│                               │   │   ├── OrgStats
│                               │   │   ├── OrgLimits
│                               │   │   └── ActionButtons
│                               │   └── Modals ⭐ NEW
│                               │       ├── OrganizationCreateModal
│                               │       ├── OrganizationEditModal
│                               │       └── OrganizationSettingsModal
│                               │
│                               ├── /activities → Activities
│                               │   ├── ActivityFilters
│                               │   ├── ActivityTimeline
│                               │   └── ActivityStats
│                               │
│                               ├── /widgets → Widgets
│                               │   ├── WidgetTabs
│                               │   └── WidgetForms
│                               │
│                               └── /settings → Settings ⭐ UPDATED
│                                   ├── SettingsTabs
│                                   ├── UsersTab (existing)
│                                   ├── OrganizationTab ⭐ NEW
│                                   │   ├── OrgGeneralInfo
│                                   │   ├── OrgBranding
│                                   │   ├── OrgLimits
│                                   │   └── OrgFeatures
│                                   ├── SystemTab (existing)
│                                   └── ProfileTab ⭐ NEW
```

---

## Data Flow Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Actions                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Login Component                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. User enters credentials                                │  │
│  │ 2. Submits form                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Auth Service                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ authAPI.login(credentials)                                │  │
│  │   → POST /api/auth/login                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Backend API                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Returns:                                                  │  │
│  │ {                                                         │  │
│  │   access_token: "jwt...",                                │  │
│  │   refresh_token: "jwt...",                               │  │
│  │   expires_in: 900,                                       │  │
│  │   user: { id, email, role, organization, ... }           │  │
│  │ }                                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Auth Context                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Store tokens in localStorage                          │  │
│  │ 2. Update auth state:                                    │  │
│  │    - user                                                │  │
│  │    - isAuthenticated: true                               │  │
│  │    - currentOrganization                                 │  │
│  │ 3. Schedule token refresh                                │  │
│  │ 4. Fetch user permissions                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Re-render                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - ProtectedRoute allows access                           │  │
│  │ - Layout renders with user info                          │  │
│  │ - Navigation filtered by permissions                     │  │
│  │ - Redirect to Dashboard                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Organization Switching Flow

```
User clicks Organization Switcher
        │
        ▼
Organization Dropdown opens
        │
        ▼
User selects different organization
        │
        ▼
OrganizationContext.switchOrganization(orgId)
        │
        ├─→ 1. Call API: organizationsAPI.switch(orgId)
        │       │
        │       ▼
        │   Backend validates user access to org
        │       │
        │       ▼
        │   Returns new access token with org context
        │
        ├─→ 2. Update localStorage:
        │       - token (new)
        │       - current_organization_id
        │
        ├─→ 3. Update Auth Context:
        │       - currentOrganization
        │       - user.organization_id
        │       - permissions (org-specific)
        │
        ├─→ 4. Update API interceptors:
        │       - X-Organization-Id header
        │
        ├─→ 5. Invalidate all React Query caches
        │       - queryClient.invalidateQueries()
        │
        └─→ 6. Re-fetch organization-specific data
                │
                ▼
        Application re-renders with new org context
                │
                ├─→ Layout updates org name
                ├─→ Dashboard shows new org data
                ├─→ All pages show new org data
                └─→ Navigation updates if permissions changed
```

### Permission Check Flow

```
Component needs to render permission-based content
        │
        ▼
<PermissionGate permission="users.create">
  <Button>Create User</Button>
</PermissionGate>
        │
        ▼
PermissionGate calls useAuth()
        │
        ▼
const { checkPermission } = useAuth()
        │
        ▼
checkPermission("users.create")
        │
        ├─→ 1. Check user role
        │       │
        │       ├─→ super_admin? → Always return true
        │       │
        │       └─→ Other roles → Check permissions array
        │
        ├─→ 2. Check user.permissions array
        │       │
        │       └─→ permissions.includes("users.create")
        │
        └─→ 3. Return boolean
                │
                ├─→ true  → Render children
                │
                └─→ false → Render fallback (or null)
```

### API Request Flow with Auth & Org Context

```
Component makes API request
        │
        ▼
usersAPI.list({ page: 1, limit: 25 })
        │
        ▼
Axios Request Interceptor
        │
        ├─→ 1. Get token from localStorage
        │       └─→ Add Authorization header
        │
        ├─→ 2. Get current_organization_id from localStorage
        │       └─→ Add X-Organization-Id header
        │
        └─→ 3. Send request
                │
                ▼
        Backend API
                │
                ├─→ Verify JWT token
                ├─→ Extract organization from header
                ├─→ Verify user has access to org
                ├─→ Filter data by organization
                └─→ Return response
                        │
                        ▼
        Axios Response Interceptor
                │
                ├─→ Success (200-299)
                │       └─→ Return data to component
                │
                └─→ Error
                        │
                        ├─→ 401 Unauthorized
                        │       │
                        │       ├─→ Try token refresh
                        │       │   │
                        │       │   ├─→ Success → Retry original request
                        │       │   │
                        │       │   └─→ Fail → Logout & redirect to /login
                        │       │
                        │       └─→ Return error
                        │
                        ├─→ 403 Forbidden
                        │       └─→ Show "No permission" error
                        │
                        └─→ Other errors
                                └─→ Show error message
```

---

## State Management Architecture

### Global State (Context API)

```
┌─────────────────────────────────────────────────────────────────┐
│                        AuthContext                               │
├─────────────────────────────────────────────────────────────────┤
│ State:                                                           │
│  - user (object)                                                 │
│  - currentOrganization (object)                                  │
│  - isAuthenticated (boolean)                                     │
│  - isLoading (boolean)                                           │
│  - token (string)                                                │
│                                                                   │
│ Methods:                                                         │
│  - login(credentials)                                            │
│  - logout()                                                      │
│  - refreshToken()                                                │
│  - updateUser(userData)                                          │
│  - checkPermission(permission)                                   │
│  - hasRole(role)                                                 │
│                                                                   │
│ Consumers:                                                       │
│  - ALL protected components                                      │
│  - Layout (for user info)                                        │
│  - Navigation (for permission filtering)                         │
│  - Route guards                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   OrganizationContext                            │
├─────────────────────────────────────────────────────────────────┤
│ State:                                                           │
│  - currentOrganization (object)                                  │
│  - organizations (array)                                         │
│  - settings (object)                                             │
│  - stats (object)                                                │
│  - isLoading (boolean)                                           │
│                                                                   │
│ Methods:                                                         │
│  - switchOrganization(orgId)                                     │
│  - updateSettings(settings)                                      │
│  - refreshStats()                                                │
│                                                                   │
│ Consumers:                                                       │
│  - OrganizationSwitcher                                          │
│  - Dashboard (for org stats)                                     │
│  - Settings (organization tab)                                   │
│  - All pages (via org context)                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ThemeContext                               │
├─────────────────────────────────────────────────────────────────┤
│ State:                                                           │
│  - theme ('light' | 'dark')                                      │
│  - isDark (boolean)                                              │
│                                                                   │
│ Methods:                                                         │
│  - toggleTheme()                                                 │
│  - setTheme(theme)                                               │
│                                                                   │
│ Consumers:                                                       │
│  - Layout (theme toggle)                                         │
│  - All components (for styling)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Server State (React Query)

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Query Cache                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Query Keys Structure:                                            │
│                                                                   │
│ ['users']                     → All users list                   │
│ ['users', { page, limit }]    → Paginated users                  │
│ ['users', userId]             → Single user detail               │
│ ['users', userId, 'activity'] → User activity logs               │
│                                                                   │
│ ['devices']                   → All devices                      │
│ ['devices', { status }]       → Filtered devices                 │
│ ['devices', deviceId]         → Single device                    │
│                                                                   │
│ ['content']                   → All content                      │
│ ['content', contentId]        → Single content                   │
│                                                                   │
│ ['organizations']             → All organizations                │
│ ['organizations', orgId]      → Single org                       │
│ ['organizations', orgId, 'stats'] → Org statistics               │
│                                                                   │
│ ['profile']                   → Current user profile             │
│ ['profile', 'organizations']  → User's organizations             │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Cache Invalidation Strategy:                                     │
│                                                                   │
│ On organization switch:                                          │
│   queryClient.invalidateQueries()  // Clear all                  │
│                                                                   │
│ On user update:                                                  │
│   queryClient.invalidateQueries(['users', userId])               │
│   queryClient.invalidateQueries(['profile'])                     │
│                                                                   │
│ On content upload:                                               │
│   queryClient.invalidateQueries(['content'])                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Local State (useState/useReducer)

```
Component-specific UI state:

- Modal open/closed state
- Form input values
- Dropdown open state
- Selected items
- Filter values
- Sort direction
- Pagination state
- Loading states
- Error messages
```

---

## Component Communication Patterns

### Pattern 1: Parent → Child (Props)
```javascript
<UserTable
  users={users}
  onEdit={handleEdit}
  onDelete={handleDelete}
  loading={isLoading}
/>
```

### Pattern 2: Child → Parent (Callbacks)
```javascript
// Parent
const [selectedUser, setSelectedUser] = useState(null)

<UserTableRow
  user={user}
  onSelect={(user) => setSelectedUser(user)}
/>

// Child
<button onClick={() => onSelect(user)}>
  Select
</button>
```

### Pattern 3: Sibling Communication (Lifted State)
```javascript
// Parent
const [filters, setFilters] = useState({})

<UserFilters filters={filters} onChange={setFilters} />
<UserTable filters={filters} />
```

### Pattern 4: Global State (Context)
```javascript
// Any component deep in tree
const { user, checkPermission } = useAuth()

if (checkPermission('users.create')) {
  return <CreateUserButton />
}
```

### Pattern 5: Server State (React Query)
```javascript
// Component A (fetches data)
const { data } = useQuery({
  queryKey: ['users'],
  queryFn: usersAPI.list
})

// Component B (uses cached data)
const { data } = useQuery({
  queryKey: ['users']
  // Won't refetch if fresh - uses cache
})

// Component C (invalidates cache)
const mutation = useMutation({
  mutationFn: usersAPI.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['users'])
  }
})
```

---

## Custom Hooks Architecture

### useAuth Hook
```javascript
export function useAuth() {
  const context = useContext(AuthContext)

  return {
    user: context.user,
    isAuthenticated: context.isAuthenticated,
    isLoading: context.isLoading,
    login: context.login,
    logout: context.logout,
    checkPermission: context.checkPermission,
    hasRole: context.hasRole
  }
}

// Usage
const { user, checkPermission } = useAuth()
```

### useOrganization Hook
```javascript
export function useOrganization() {
  const context = useContext(OrganizationContext)

  return {
    currentOrganization: context.currentOrganization,
    organizations: context.organizations,
    switchOrganization: context.switchOrganization,
    settings: context.settings,
    stats: context.stats
  }
}

// Usage
const { currentOrganization, switchOrganization } = useOrganization()
```

### usePermission Hook
```javascript
export function usePermission(permission) {
  const { checkPermission } = useAuth()
  return checkPermission(permission)
}

// Usage
const canCreateUser = usePermission(PERMISSIONS.USERS_CREATE)
```

### useUsers Hook
```javascript
export function useUsers(filters = {}) {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => usersAPI.list(filters),
    staleTime: 5 * 60 * 1000
  })
}

// Usage
const { data, isLoading, error } = useUsers({ role: 'editor' })
```

### useUser Hook
```javascript
export function useUser(userId) {
  return useQuery({
    queryKey: ['users', userId],
    queryFn: () => usersAPI.get(userId),
    enabled: !!userId
  })
}

// Usage
const { data: user } = useUser(selectedUserId)
```

### useDebounce Hook
```javascript
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}

// Usage (for search)
const [search, setSearch] = useState('')
const debouncedSearch = useDebounce(search, 300)

const { data } = useUsers({ search: debouncedSearch })
```

---

## Component Reusability Patterns

### Compound Components Pattern
```javascript
// Table compound component
<DataTable data={users}>
  <DataTable.Header>
    <DataTable.Column>Name</DataTable.Column>
    <DataTable.Column>Email</DataTable.Column>
    <DataTable.Column>Role</DataTable.Column>
  </DataTable.Header>

  <DataTable.Body>
    {users.map(user => (
      <DataTable.Row key={user.id}>
        <DataTable.Cell>{user.name}</DataTable.Cell>
        <DataTable.Cell>{user.email}</DataTable.Cell>
        <DataTable.Cell><RoleBadge role={user.role} /></DataTable.Cell>
      </DataTable.Row>
    ))}
  </DataTable.Body>

  <DataTable.Footer>
    <Pagination />
  </DataTable.Footer>
</DataTable>
```

### Render Props Pattern
```javascript
// Permission check with render prop
<HasPermission permission="users.create">
  {(hasPermission) => (
    hasPermission
      ? <CreateButton />
      : <UpgradePrompt />
  )}
</HasPermission>
```

### Higher-Order Component Pattern
```javascript
// HOC for permission checking
const withPermission = (permission) => (Component) => {
  return (props) => {
    const hasPermission = usePermission(permission)

    if (!hasPermission) {
      return <Forbidden />
    }

    return <Component {...props} />
  }
}

// Usage
export default withPermission(PERMISSIONS.USERS_VIEW)(UsersPage)
```

---

## Summary

This component hierarchy and data flow architecture provides:

1. **Clear separation of concerns**: Each component has a specific purpose
2. **Efficient data flow**: Context for global state, React Query for server state
3. **Permission-based rendering**: Multiple patterns for different use cases
4. **Reusable components**: Common patterns across the application
5. **Scalable structure**: Easy to add new features without breaking existing ones

The architecture supports both the current simple auth and the future multi-tenant requirements with minimal changes to existing components.
