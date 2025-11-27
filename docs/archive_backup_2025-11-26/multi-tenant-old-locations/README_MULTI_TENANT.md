# Multi-Tenant User Management - Complete Documentation

## Overview

This documentation provides a complete guide for implementing multi-tenant user management in the Signage Admin React application. The implementation follows modern React best practices and is designed to be scalable, secure, and maintainable.

---

## Documentation Structure

### 1. **MULTI_TENANT_FRONTEND_ARCHITECTURE.md**
**Purpose**: Comprehensive architectural design and planning document

**Contents**:
- State management strategy (Auth Context, Organization Context)
- Complete component architecture and directory structure
- Routing and navigation structure with protection
- Authentication and authorization system (permissions, roles)
- API integration patterns
- Detailed UI/UX specifications with mockups
- 6-phase migration strategy
- Implementation checklist

**When to use**:
- Understanding the overall architecture
- Planning development phases
- Making architectural decisions
- Reviewing the system design

### 2. **COMPONENT_HIERARCHY.md**
**Purpose**: Visual representation of component relationships and data flow

**Contents**:
- Complete application component tree
- Authentication flow diagrams
- Organization switching flow
- Permission check flow
- API request flow with auth
- State management architecture (Context + React Query)
- Component communication patterns
- Custom hooks architecture
- Reusability patterns

**When to use**:
- Understanding how components interact
- Debugging data flow issues
- Designing new features
- Onboarding new developers

### 3. **IMPLEMENTATION_GUIDE.md**
**Purpose**: Hands-on implementation guide with ready-to-use code

**Contents**:
- Step-by-step Phase 1 implementation
- Complete code for AuthContext
- Updated App.jsx with route protection
- Route protection components (ProtectedRoute, PermissionRoute, RoleRoute)
- Permission and role constants
- Enhanced API service with token refresh
- Updated Layout with profile dropdown
- Enhanced Login page
- Testing checklist
- Troubleshooting guide

**When to use**:
- Starting implementation
- Copy-paste ready code
- Setting up authentication
- Testing implementation

---

## Quick Start

### Prerequisites

```bash
# Current dependencies (already installed)
- React 18.3.1
- React Router DOM 6.26.0
- TanStack React Query 5.56.2
- Axios 1.7.7
- Lucide React 0.445.0
- Tailwind CSS 3.4.11

# Optional (recommended for advanced features)
npm install jwt-decode       # For JWT token parsing
npm install react-hook-form  # For form management
npm install zod              # For validation
```

### Implementation Steps

#### Phase 1: Foundation (Start Here)

1. **Read the Architecture Document**
   ```bash
   # Open and read
   web-admin/MULTI_TENANT_FRONTEND_ARCHITECTURE.md
   ```

2. **Follow the Implementation Guide**
   ```bash
   # Open and follow step-by-step
   web-admin/IMPLEMENTATION_GUIDE.md
   ```

3. **Create Required Directories**
   ```bash
   cd web-admin/src
   mkdir -p contexts hooks components/routing components/profile utils
   ```

4. **Implement in Order**
   - Step 1: Create `contexts/AuthContext.jsx`
   - Step 2: Update `App.jsx`
   - Step 3: Create route protection components
   - Step 4: Create permission constants
   - Step 5: Update `services/api.js`
   - Step 6: Update `components/Layout.jsx`
   - Step 7: Create `components/profile/ProfileDropdown.jsx`
   - Step 8: Update `pages/Login.jsx`

5. **Test Phase 1**
   - Use testing checklist in Implementation Guide
   - Verify all existing functionality still works
   - Test new auth features

#### Phase 2-6: Follow Architecture Document

After Phase 1 is complete, follow the remaining phases outlined in the architecture document:

- **Phase 2**: User Management UI
- **Phase 3**: Organization Support
- **Phase 4**: Enhanced Auth Flows
- **Phase 5**: Permissions & Authorization
- **Phase 6**: Polish & Testing

---

## Key Concepts

### Authentication Flow

```
Login → Store JWT → AuthContext Updates → Protected Routes Accessible
                ↓
         Auto Refresh Token (before expiry)
                ↓
         Token Expires → Refresh → Continue
                ↓
         Refresh Fails → Logout → Redirect to Login
```

### Permission System

```
Component Render
    ↓
Check Permission (PERMISSIONS.USERS_VIEW)
    ↓
AuthContext.checkPermission()
    ↓
Is Super Admin? → Yes → Allow
    ↓ No
Has Permission in Array? → Yes → Allow
    ↓ No
Deny → Show Fallback or Hide
```

### Organization Context

```
User has Organizations: [Org A, Org B, Org C]
    ↓
Current Org: Org A
    ↓
Switch to Org B
    ↓
API Call: organizationsAPI.switch(orgB.id)
    ↓
New Token with Org B Context
    ↓
Update AuthContext + invalidate React Query cache
    ↓
All API calls now include X-Organization-Id: orgB.id
    ↓
UI shows Org B data
```

---

## Architecture Highlights

### State Management

```
┌──────────────────────────────────────────┐
│        Global State (Context)            │
│  - AuthContext (user, permissions)       │
│  - OrganizationContext (current org)     │
│  - ThemeContext (dark mode)              │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│      Server State (React Query)          │
│  - Users list                            │
│  - Devices list                          │
│  - Content list                          │
│  - Cached with smart invalidation        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│        Local State (useState)            │
│  - Form inputs                           │
│  - Modal open/close                      │
│  - UI-only state                         │
└──────────────────────────────────────────┘
```

### Component Structure

```
src/
├── contexts/           # Global state providers
├── hooks/             # Custom React hooks
├── components/
│   ├── auth/          # Auth-related UI
│   ├── users/         # User management
│   ├── organizations/ # Org management
│   ├── profile/       # User profile
│   ├── permissions/   # Permission gates
│   ├── routing/       # Route protection
│   ├── layout/        # App layout
│   └── common/        # Reusable components
├── pages/             # Route pages
├── services/          # API services
└── utils/             # Helper functions
```

### Security Layers

1. **Backend (Primary)**: Actual permission enforcement
2. **Route Protection**: Prevent unauthorized route access
3. **Component Gates**: Hide unauthorized UI elements
4. **API Interceptors**: Add auth tokens automatically
5. **Token Refresh**: Seamless session management

---

## API Integration

### Request Flow

```javascript
// 1. Component makes request
const { data } = useQuery({
  queryKey: ['users'],
  queryFn: () => usersAPI.list()
})

// 2. Axios request interceptor adds:
//    - Authorization: Bearer <token>
//    - X-Organization-Id: <current_org_id>

// 3. Backend validates and returns org-specific data

// 4. Response interceptor handles:
//    - 401 → Try token refresh → Retry request
//    - 403 → Show permission error
//    - Success → Return data to component
```

### Backend API Expectations

Your backend should provide these endpoints:

```
Authentication:
POST   /api/auth/login              → { access_token, refresh_token, user }
POST   /api/auth/logout
GET    /api/auth/me                 → { user with permissions }
POST   /api/auth/refresh            → { new access_token }
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
POST   /api/auth/verify-email

Users:
GET    /api/users                   → List users (org-filtered)
POST   /api/users                   → Create user
GET    /api/users/:id               → Get user details
PATCH  /api/users/:id               → Update user
DELETE /api/users/:id               → Delete user
POST   /api/users/invite            → Invite user

Organizations:
GET    /api/organizations           → List orgs (super admin only)
POST   /api/organizations/:id/switch → Switch context

Profile:
GET    /api/profile                 → Current user profile
PATCH  /api/profile                 → Update profile
POST   /api/profile/change-password
```

**Important**: All endpoints (except auth) should:
- Validate JWT token
- Check X-Organization-Id header
- Filter data by organization
- Verify user permissions

---

## Permission Constants

### Available Permissions

```javascript
// Device Permissions
PERMISSIONS.DEVICES_VIEW
PERMISSIONS.DEVICES_CREATE
PERMISSIONS.DEVICES_EDIT
PERMISSIONS.DEVICES_DELETE
PERMISSIONS.DEVICES_APPROVE

// Content Permissions
PERMISSIONS.CONTENT_VIEW
PERMISSIONS.CONTENT_UPLOAD
PERMISSIONS.CONTENT_EDIT
PERMISSIONS.CONTENT_DELETE

// User Permissions
PERMISSIONS.USERS_VIEW
PERMISSIONS.USERS_CREATE
PERMISSIONS.USERS_EDIT
PERMISSIONS.USERS_DELETE
PERMISSIONS.USERS_INVITE

// ... and more (see utils/permissions.js)
```

### Role Hierarchy

```
Super Admin (100)  → All permissions, all orgs
    ↓
Org Admin (75)     → Manage org, users, content
    ↓
Editor (50)        → Create/edit content, devices
    ↓
Viewer (25)        → Read-only access
```

---

## Usage Examples

### Protect a Route

```javascript
// Require specific permission
<Route
  path="/users"
  element={
    <PermissionRoute permission={PERMISSIONS.USERS_VIEW}>
      <Users />
    </PermissionRoute>
  }
/>

// Require specific role
<Route
  path="/organizations"
  element={
    <RoleRoute role="super_admin">
      <Organizations />
    </RoleRoute>
  }
/>
```

### Hide UI Elements

```javascript
import { useAuth } from '../contexts/AuthContext'
import { PERMISSIONS } from '../utils/permissions'

function UserActions() {
  const { checkPermission } = useAuth()

  return (
    <div>
      {checkPermission(PERMISSIONS.USERS_CREATE) && (
        <button>Create User</button>
      )}

      {checkPermission(PERMISSIONS.USERS_DELETE) && (
        <button>Delete User</button>
      )}
    </div>
  )
}
```

### Use Permission Gate Component

```javascript
import PermissionGate from '../components/permissions/PermissionGate'

<PermissionGate permission={PERMISSIONS.USERS_CREATE}>
  <CreateUserButton />
</PermissionGate>

// With fallback
<PermissionGate
  permission={PERMISSIONS.USERS_CREATE}
  fallback={<UpgradePrompt />}
>
  <CreateUserButton />
</PermissionGate>
```

### Check Roles

```javascript
import { useAuth } from '../contexts/AuthContext'

function AdminPanel() {
  const { hasRole, hasMinRole } = useAuth()

  if (hasRole('super_admin')) {
    return <SuperAdminDashboard />
  }

  if (hasMinRole('editor')) {
    return <EditorDashboard />
  }

  return <ViewerDashboard />
}
```

---

## Testing Strategy

### Unit Testing

```javascript
// Test AuthContext
describe('AuthContext', () => {
  it('should login successfully')
  it('should logout and clear state')
  it('should check permissions correctly')
  it('should handle token refresh')
})

// Test Permission Gates
describe('PermissionGate', () => {
  it('should render children when permission granted')
  it('should render fallback when permission denied')
  it('should handle super admin correctly')
})
```

### Integration Testing

```javascript
// Test Login Flow
it('should login and redirect to dashboard')
it('should show error on invalid credentials')
it('should remember user on page refresh')

// Test Route Protection
it('should redirect to login when not authenticated')
it('should block access without permission')
it('should allow access with correct permission')
```

### E2E Testing

```javascript
// User Journey
1. Login as admin
2. Navigate to users page
3. Create new user
4. Assign role
5. Logout
6. Login as new user
7. Verify limited access
```

---

## Performance Optimization

### Code Splitting

```javascript
// Lazy load routes
const Users = lazy(() => import('./pages/Users'))
const Organizations = lazy(() => import('./pages/Organizations'))

<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/users" element={<Users />} />
  </Routes>
</Suspense>
```

### Query Optimization

```javascript
// Cache user list
const { data: users } = useQuery({
  queryKey: ['users', filters],
  queryFn: () => usersAPI.list(filters),
  staleTime: 5 * 60 * 1000,  // Fresh for 5 mins
  cacheTime: 10 * 60 * 1000  // Keep in memory for 10 mins
})

// Invalidate on mutation
const createUser = useMutation({
  mutationFn: usersAPI.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['users'])
  }
})
```

### Memoization

```javascript
// Memoize expensive computations
const filteredUsers = useMemo(() =>
  users.filter(u => u.name.includes(search)),
  [users, search]
)

// Memoize callbacks
const handleUserClick = useCallback((userId) => {
  navigate(`/users/${userId}`)
}, [navigate])
```

---

## Accessibility Considerations

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Logical tab order maintained
- Focus indicators visible

### ARIA Labels
- Buttons have descriptive labels
- Form fields properly labeled
- Dynamic content announced

### Screen Reader Support
- Semantic HTML structure
- Role attributes where needed
- Status messages announced

---

## Browser Support

- **Chrome/Edge**: Latest 2 versions
- **Firefox**: Latest 2 versions
- **Safari**: Latest 2 versions
- **Mobile**: iOS Safari, Chrome Android

---

## Troubleshooting

### Common Issues

**Problem**: Token refresh creates infinite loop
**Solution**: Ensure `originalRequest._retry` flag is set

**Problem**: Navigation shows items user can't access
**Solution**: Check that permissions are loaded in user object

**Problem**: Organization switching doesn't update data
**Solution**: Verify React Query cache invalidation on org switch

**Problem**: Profile dropdown doesn't show user info
**Solution**: Ensure authAPI.me() returns complete user object

### Debug Mode

```javascript
// Enable React Query devtools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

---

## Migration Checklist

```markdown
## Pre-Implementation
- [ ] Read architecture document
- [ ] Review component hierarchy
- [ ] Understand authentication flow
- [ ] Coordinate with backend team
- [ ] Set up development environment

## Phase 1: Foundation
- [ ] Create AuthContext
- [ ] Create route protection components
- [ ] Update App.jsx
- [ ] Create permission constants
- [ ] Update API service
- [ ] Update Layout
- [ ] Create ProfileDropdown
- [ ] Update Login page
- [ ] Test all existing functionality
- [ ] Test new auth features

## Phase 2-6
- [ ] Follow architecture document phases
- [ ] Test each phase before proceeding
- [ ] Document any deviations
- [ ] Update team on progress
```

---

## Additional Resources

### Documentation
- [React Documentation](https://react.dev/)
- [React Router v6](https://reactrouter.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Axios](https://axios-http.com/)

### Best Practices
- [React Best Practices 2024](https://react.dev/learn)
- [Authentication in React](https://react.dev/learn/adding-interactivity)
- [State Management Guide](https://react.dev/learn/managing-state)

### Community
- React Discord
- Stack Overflow (tag: reactjs)
- GitHub Discussions

---

## Support & Contribution

### Getting Help
1. Check this documentation
2. Review implementation guide
3. Check troubleshooting section
4. Contact development team

### Contributing
1. Follow existing code structure
2. Match naming conventions
3. Add tests for new features
4. Update documentation
5. Submit for review

---

## Changelog

### Version 1.0 (2025-01-27)
- Initial architecture design
- Phase 1 implementation guide
- Complete documentation set
- Ready for implementation

---

## Summary

This multi-tenant user management system provides:

- **Secure Authentication**: JWT-based with automatic refresh
- **Flexible Authorization**: Role and permission-based access control
- **Multi-Organization**: Seamless switching between organizations
- **Scalable Architecture**: Context API + React Query for state management
- **Developer Experience**: Clear structure, reusable components, comprehensive docs
- **User Experience**: Smooth flows, loading states, error handling

The architecture is designed to be implemented in phases, allowing for incremental deployment without breaking existing functionality.

---

**Questions or Issues?**
Refer to the specific documentation files for detailed information:
- Architecture: `MULTI_TENANT_FRONTEND_ARCHITECTURE.md`
- Component Flow: `COMPONENT_HIERARCHY.md`
- Implementation: `IMPLEMENTATION_GUIDE.md`

**Happy Coding!**
