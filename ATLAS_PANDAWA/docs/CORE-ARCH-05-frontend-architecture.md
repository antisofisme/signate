# Frontend Architecture

> **Date**: 2025-12-23
> **Status**: Draft
> **Pattern**: App Shell + Lazy-loaded Modules

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  APP SHELL (Single SPA)                                         │   │
│  │  - Authentication flow                                          │   │
│  │  - Tenant picker & context                                      │   │
│  │  - Module launcher                                              │   │
│  │  - Permission guard                                             │   │
│  │  - Feature flags                                                │   │
│  │  - Global state management                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  MODULE ROUTES (Lazy-loaded)                                    │   │
│  │  /app/pms/*        → PMS Module                                 │   │
│  │  /app/pos/*        → POS Module                                 │   │
│  │  /app/accounting/* → Accounting Module                          │   │
│  │  /app/inventory/*  → Inventory Module                           │   │
│  │  /app/signage/*    → Digital Signage Module                     │   │
│  │  /app/hrm/*        → HR Management Module                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SHARED INFRASTRUCTURE                                          │   │
│  │  - Design system (Tailwind + shadcn/ui)                         │   │
│  │  - API client (with tenant context injection)                   │   │
│  │  - Error boundary & logging                                     │   │
│  │  - Toast notifications                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Core Principles

### 1.1 Fundamental Concepts

#### Tenant = Work Context
- Tenant represents a business entity (hotel, restaurant, company)
- User selects tenant after login
- All operations happen within active tenant context

#### Module = Work Tool
- Module is a functional capability (PMS, POS, Accounting, etc.)
- Each module is an independent lazy-loaded bundle
- Modules share common infrastructure and design system

#### Frontend = Single Entry Point
- **One SPA (Single Page Application)**, not multiple separate apps
- Better UX (no page reloads between modules)
- Easier deployment (single build artifact)
- Shared state and infrastructure

---

## Part 2: Authentication & Tenant Flow

### 2.1 Login Flow (Mandatory Steps)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOGIN FLOW                                      │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Login (Identity Global)
┌──────────────────────────┐
│ Email / Password         │
│ or SSO                   │
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│ Authenticate User        │
│ GET /api/auth/login      │
│ Returns: access_token    │
└──────────────────────────┘
          │
          ▼

Step 2: Tenant Picker
┌──────────────────────────┐
│ GET /api/user/tenants    │
│ Returns: List of tenants │
│ user has access to       │
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│ User selects tenant      │
│ activeTenantId = "xyz"   │
└──────────────────────────┘
          │
          ▼

Step 3: App Shell Loads
┌──────────────────────────┐
│ Tenant context active    │
│ Load user permissions    │
│ Load subscribed modules  │
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│ Show module navigation   │
│ based on:                │
│ - tenant subscriptions   │
│ - user permissions       │
└──────────────────────────┘
          │
          ▼

Step 4: Module View
┌──────────────────────────┐
│ User clicks module       │
│ Lazy-load module bundle  │
│ Render module UI         │
└──────────────────────────┐
```

### 2.2 Tenant Management

#### Storage Strategy
```typescript
// In-memory state (primary)
const appState = {
  user: User,
  activeTenantId: string,
  tenants: Tenant[],
  permissions: Permission[],
  subscribedModules: Module[]
}

// localStorage (persistence)
localStorage.setItem('activeTenantId', tenantId)
localStorage.setItem('lastUsedModule', moduleCode)
```

#### Backend Communication
All API requests must include tenant context:

**Option A: HTTP Header** (Recommended)
```typescript
axios.defaults.headers.common['X-Tenant-ID'] = activeTenantId

// Example request
GET /api/pms/reservations
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-ID: tenant_abc123
```

**Option B: JWT Claim**
```typescript
// Token includes tenant claim
{
  "sub": "user_123",
  "tenant_id": "tenant_abc123",
  "role": "front_desk",
  ...
}
```

**Backend MUST validate**:
- User has access to specified tenant
- Tenant exists and is active
- User has required permissions for the operation

### 2.3 Tenant Switching

```typescript
async function switchTenant(newTenantId: string) {
  // 1. Validate user has access
  if (!user.tenants.includes(newTenantId)) {
    throw new Error('Access denied')
  }

  // 2. Update state
  setActiveTenantId(newTenantId)
  localStorage.setItem('activeTenantId', newTenantId)

  // 3. Reload permissions & subscriptions
  const permissions = await fetchPermissions(newTenantId)
  const modules = await fetchSubscribedModules(newTenantId)

  // 4. Update navigation
  updateModuleNavigation(modules, permissions)

  // 5. Navigate to dashboard or last used module
  const lastModule = localStorage.getItem('lastUsedModule')
  if (lastModule && modules.includes(lastModule)) {
    navigate(`/app/${lastModule}`)
  } else {
    navigate('/app/dashboard')
  }
}
```

---

## Part 3: App Shell Architecture

### 3.1 Recommended Structure

**Single SPA with modular routes:**
```
/                           → Landing page or redirect to /auth/login
/auth/login                 → Login page
/auth/register              → Registration (if applicable)
/auth/select-tenant         → Tenant picker
/app                        → App Shell (protected route)
  /app/dashboard            → Main dashboard
  /app/pms/*                → PMS module (lazy-loaded)
  /app/pos/*                → POS module (lazy-loaded)
  /app/accounting/*         → Accounting module (lazy-loaded)
  /app/inventory/*          → Inventory module (lazy-loaded)
  /app/signage/*            → Digital Signage module (lazy-loaded)
  /app/hrm/*                → HR Management module (lazy-loaded)
  /app/settings             → User/tenant settings
```

### 3.2 App Shell Components

The App Shell is responsible for:

#### A. Layout
```typescript
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar with module navigation */}
      <Sidebar />

      <main className="flex-1">
        {/* Top bar with tenant switcher, user menu */}
        <TopBar />

        {/* Module content area */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
```

#### B. Tenant Switcher
```typescript
export function TenantSwitcher() {
  const { tenants, activeTenantId, switchTenant } = useTenantContext()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <div className="flex items-center gap-2">
          <Building className="h-4 w-4" />
          <span>{tenants.find(t => t.id === activeTenantId)?.name}</span>
          <ChevronDown className="h-4 w-4" />
        </div>
      </DropdownMenuTrigger>

      <DropdownMenuContent>
        {tenants.map(tenant => (
          <DropdownMenuItem
            key={tenant.id}
            onClick={() => switchTenant(tenant.id)}
          >
            {tenant.name}
            {tenant.id === activeTenantId && <Check className="ml-auto" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

#### C. Module Launcher
```typescript
export function ModuleNavigation() {
  const { subscribedModules, permissions } = useAppContext()

  // Filter modules based on subscription and permissions
  const visibleModules = subscribedModules.filter(module => {
    return hasPermission(permissions, module.requiredPermission)
  })

  return (
    <nav className="space-y-1">
      {visibleModules.map(module => (
        <NavItem
          key={module.code}
          to={`/app/${module.code}`}
          icon={module.icon}
          label={module.name}
        />
      ))}
    </nav>
  )
}
```

#### D. Permission Guard
```typescript
export function PermissionGuard({
  permission,
  children,
  fallback = null
}: {
  permission: string
  children: React.ReactNode
  fallback?: React.ReactNode
}) {
  const { permissions } = useAppContext()

  if (!hasPermission(permissions, permission)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

// Usage
<PermissionGuard permission="pms:reservations:create">
  <Button>Create Reservation</Button>
</PermissionGuard>
```

#### E. Feature Flag Support
```typescript
export function FeatureFlag({
  flag,
  children,
  fallback = null
}: {
  flag: string
  children: React.ReactNode
  fallback?: React.ReactNode
}) {
  const { featureFlags } = useAppContext()

  if (!featureFlags[flag]) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

// Usage
<FeatureFlag flag="pms_new_checkout_flow">
  <NewCheckoutFlow />
</FeatureFlag>
```

---

## Part 4: Module Access & Permissions

### 4.1 Visibility Rules

**Default behavior: HIDDEN**
- Modules are **hidden by default** if user has no access
- Menu only displays modules where:
  - Tenant has active subscription
  - User has required permissions

**Exception (Optional - Commercial UX):**
For **Owner/Admin** of tenant:
- Unsubscribed modules MAY be shown as **disabled**
- Label: "Upgrade required" or "Not subscribed"
- Click opens subscription/upgrade flow
- MUST NOT open actual module UI

### 4.2 Implementation

```typescript
interface ModuleAccess {
  moduleCode: string
  subscribed: boolean
  hasPermission: boolean
}

function getModuleAccess(
  modules: Module[],
  subscriptions: Subscription[],
  permissions: Permission[]
): ModuleAccess[] {
  return modules.map(module => {
    const subscribed = subscriptions.some(
      s => s.module_code === module.code && s.status === 'active'
    )

    const hasPermission = permissions.some(
      p => p.resource === module.code
    )

    return {
      moduleCode: module.code,
      subscribed,
      hasPermission
    }
  })
}

function renderModuleNav(access: ModuleAccess[], userRole: string) {
  return access.map(({ moduleCode, subscribed, hasPermission }) => {
    // Hidden by default
    if (!subscribed || !hasPermission) {
      // Exception: Owner/Admin can see disabled state
      if (userRole === 'owner' || userRole === 'admin') {
        return (
          <NavItem
            key={moduleCode}
            disabled
            badge="Upgrade required"
            onClick={() => openUpgradeModal(moduleCode)}
          />
        )
      }

      // Regular users: completely hidden
      return null
    }

    // User has access: show as enabled
    return (
      <NavItem
        key={moduleCode}
        to={`/app/${moduleCode}`}
      />
    )
  })
}
```

### 4.3 Backend Authority

**Frontend is for UI rendering only.**
**Backend is the authority** for:
- Tenant validation
- Role validation
- Subscription validation
- Permission enforcement

```python
# Backend middleware
async def validate_module_access(
    tenant_id: str,
    user_id: str,
    module_code: str
):
    # 1. Validate tenant
    tenant = await get_tenant(tenant_id)
    if not tenant or tenant.status != 'active':
        raise HTTPException(403, "Tenant inactive")

    # 2. Validate subscription
    subscription = await get_subscription(tenant_id, module_code)
    if not subscription or subscription.status != 'active':
        raise HTTPException(403, "Module not subscribed")

    # 3. Validate user permission
    has_permission = await check_permission(user_id, tenant_id, module_code)
    if not has_permission:
        raise HTTPException(403, "Permission denied")

    return True
```

**Principle:**
> **Hidden by default. Visible only if allowed.**

---

## Part 5: Routing Strategy

### 5.1 Route Structure

```typescript
import { createBrowserRouter } from 'react-router-dom'
import { lazy } from 'react'

// Lazy-loaded modules
const PMSModule = lazy(() => import('@/modules/pms'))
const POSModule = lazy(() => import('@/modules/pos'))
const AccountingModule = lazy(() => import('@/modules/accounting'))
const InventoryModule = lazy(() => import('@/modules/inventory'))
const SignageModule = lazy(() => import('@/modules/signage'))
const HRMModule = lazy(() => import('@/modules/hrm'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />
  },
  {
    path: '/auth',
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { path: 'select-tenant', element: <TenantPickerPage /> }
    ]
  },
  {
    path: '/app',
    element: <ProtectedRoute><AppShell /></ProtectedRoute>,
    children: [
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'pms/*', element: <PMSModule /> },
      { path: 'pos/*', element: <POSModule /> },
      { path: 'accounting/*', element: <AccountingModule /> },
      { path: 'inventory/*', element: <InventoryModule /> },
      { path: 'signage/*', element: <SignageModule /> },
      { path: 'hrm/*', element: <HRMModule /> },
      { path: 'settings', element: <SettingsPage /> }
    ]
  }
])
```

### 5.2 Protected Route Guard

```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, activeTenantId } = useAuth()
  const location = useLocation()

  // Not authenticated → redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  // Authenticated but no tenant selected → redirect to tenant picker
  if (!activeTenantId) {
    return <Navigate to="/auth/select-tenant" replace />
  }

  // All good → render app
  return <>{children}</>
}
```

### 5.3 Module Route Guard

```typescript
function ModuleRoute({
  moduleCode,
  children
}: {
  moduleCode: string
  children: React.ReactNode
}) {
  const { subscribedModules, permissions } = useAppContext()

  // Check subscription
  const isSubscribed = subscribedModules.some(m => m.code === moduleCode)
  if (!isSubscribed) {
    return <Navigate to="/app/dashboard" replace />
  }

  // Check permission
  const hasAccess = hasPermission(permissions, moduleCode)
  if (!hasAccess) {
    return <Navigate to="/app/dashboard" replace />
  }

  return <>{children}</>
}

// Usage
<Route
  path="/app/pms/*"
  element={
    <ModuleRoute moduleCode="pms">
      <PMSModule />
    </ModuleRoute>
  }
/>
```

---

## Part 6: State Management

### 6.1 Global State Structure

```typescript
interface AppState {
  // Authentication
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null

  // Tenant context
  tenants: Tenant[]
  activeTenantId: string | null

  // Authorization
  permissions: Permission[]
  subscribedModules: Module[]
  featureFlags: Record<string, boolean>

  // UI state
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
}

interface User {
  id: string
  email: string
  name: string
  avatar?: string
}

interface Tenant {
  id: string
  name: string
  logo?: string
  subscription_tier: string
}

interface Permission {
  resource: string      // e.g., "pms", "pms:reservations"
  action: string        // e.g., "read", "write", "delete"
  granted: boolean
}

interface Module {
  code: string          // e.g., "pms", "pos"
  name: string
  icon: string
  route: string
  requiredPermission: string
}
```

### 6.2 Context Providers

```typescript
// App Context Provider
export function AppContextProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AppState>(initialState)

  const value = {
    ...state,

    // Actions
    login: async (email: string, password: string) => {
      const { user, token } = await api.login(email, password)
      setState(prev => ({
        ...prev,
        user,
        accessToken: token,
        isAuthenticated: true
      }))
    },

    logout: () => {
      setState(initialState)
      localStorage.clear()
    },

    switchTenant: async (tenantId: string) => {
      const [permissions, modules, flags] = await Promise.all([
        api.getPermissions(tenantId),
        api.getSubscribedModules(tenantId),
        api.getFeatureFlags(tenantId)
      ])

      setState(prev => ({
        ...prev,
        activeTenantId: tenantId,
        permissions,
        subscribedModules: modules,
        featureFlags: flags
      }))

      localStorage.setItem('activeTenantId', tenantId)
    }
  }

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}

// Hook for consuming context
export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within AppContextProvider')
  }
  return context
}
```

### 6.3 Persistence Strategy

```typescript
// On app initialization
function initializeApp() {
  // 1. Check localStorage for previous session
  const savedTenantId = localStorage.getItem('activeTenantId')
  const savedToken = localStorage.getItem('accessToken')

  // 2. Validate token
  if (savedToken) {
    const isValid = await validateToken(savedToken)

    if (isValid) {
      // Restore session
      const user = await fetchUser()
      const tenants = await fetchTenants()

      setState({
        user,
        accessToken: savedToken,
        isAuthenticated: true,
        tenants
      })

      // Restore tenant context if available
      if (savedTenantId && tenants.some(t => t.id === savedTenantId)) {
        await switchTenant(savedTenantId)
      }
    } else {
      // Token expired → clear and redirect to login
      localStorage.clear()
      navigate('/auth/login')
    }
  }
}
```

---

## Part 7: Subdomain Strategy (Optional)

### 7.1 When to Use Subdomain

Use subdomain **only if**:
- Strong white-label requirements
- Custom domain for customers
- Branding isolation needed

Examples:
- `hotelA.yourapp.com`
- `hotelB.yourapp.com`
- Custom domain: `app.hotelA.com` (CNAME)

### 7.2 Implementation Notes

**Subdomain = UI Hint, NOT Authority**

```typescript
// Extract tenant from subdomain
function getTenantHintFromSubdomain(): string | null {
  const hostname = window.location.hostname
  const parts = hostname.split('.')

  // app.yourapp.com → no tenant hint
  if (parts.length === 3 && parts[0] === 'app') {
    return null
  }

  // hotelA.yourapp.com → tenant hint: "hotelA"
  if (parts.length === 3) {
    return parts[0]
  }

  return null
}

// Use hint to pre-select tenant
async function handleLogin(email: string, password: string) {
  const { user, token } = await api.login(email, password)

  const tenants = await api.getUserTenants()
  const tenantHint = getTenantHintFromSubdomain()

  // If subdomain matches a tenant the user has access to, pre-select it
  if (tenantHint) {
    const matchedTenant = tenants.find(t => t.subdomain === tenantHint)
    if (matchedTenant) {
      await switchTenant(matchedTenant.id)
      navigate('/app/dashboard')
      return
    }
  }

  // Otherwise, show tenant picker
  navigate('/auth/select-tenant')
}
```

**Backend MUST still validate**:
```python
# Backend validation
async def validate_request(request: Request):
    # Extract tenant from header (NOT from subdomain)
    tenant_id = request.headers.get('X-Tenant-ID')

    # Validate user has access to this tenant
    user_tenants = await get_user_tenants(request.user.id)
    if tenant_id not in [t.id for t in user_tenants]:
        raise HTTPException(403, "Access denied")

    return tenant_id
```

**Important:**
- Subdomain is for **UX/branding** only
- Backend always validates tenant from **token/header**
- Never trust subdomain as security boundary

---

## Part 8: Anti-Patterns (What NOT to Do)

### 8.1 Separate Frontend per Module
❌ **Don't:**
```
pms.yourapp.com      → Separate React app for PMS
pos.yourapp.com      → Separate React app for POS
accounting.yourapp.com → Separate React app for Accounting
```

**Problems:**
- User must login separately for each app
- No shared state (tenant context lost when switching)
- Duplicate infrastructure (design system, API client, etc.)
- Harder deployment and maintenance
- Poor UX (full page reload between modules)

✅ **Do:**
```
app.yourapp.com/app/pms
app.yourapp.com/app/pos
app.yourapp.com/app/accounting
→ Single SPA with lazy-loaded modules
```

### 8.2 Login per Module
❌ **Don't:**
- Require login when switching between modules
- Store separate sessions per module

✅ **Do:**
- Single login at app entry
- Maintain session across all modules
- Use permission guards to control access

### 8.3 Tenant from URL Only
❌ **Don't:**
```typescript
// Deriving tenant from URL
const tenantId = window.location.pathname.split('/')[1]
// Backend trusts this without validation
```

**Problems:**
- User can manually change URL to access other tenants
- No security validation

✅ **Do:**
```typescript
// Tenant from authenticated context
const { activeTenantId } = useAppContext()

// Send to backend via header
axios.get('/api/data', {
  headers: { 'X-Tenant-ID': activeTenantId }
})

// Backend validates user has access to this tenant
```

### 8.4 Permission Check on Frontend Only
❌ **Don't:**
```typescript
// Frontend only
if (user.role === 'admin') {
  // Show delete button
  <Button onClick={deleteItem}>Delete</Button>
}
```

**Problems:**
- User can bypass by editing code in browser console
- API endpoint remains exposed

✅ **Do:**
```typescript
// Frontend: Hide UI for better UX
{hasPermission('items:delete') && (
  <Button onClick={deleteItem}>Delete</Button>
)}

// Backend: Enforce permission
@require_permission('items:delete')
async def delete_item(item_id: str):
    # Only executes if user has permission
    ...
```

---

## Part 9: Build & Deployment

### 9.1 Build Strategy

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "build:analyze": "vite-bundle-visualizer",
    "preview": "vite preview"
  }
}
```

### 9.2 Code Splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['@radix-ui/react-dropdown-menu', '@radix-ui/react-dialog'],

          // Module chunks (lazy-loaded)
          'module-pms': ['./src/modules/pms'],
          'module-pos': ['./src/modules/pos'],
          'module-accounting': ['./src/modules/accounting']
        }
      }
    },

    chunkSizeWarningLimit: 1000
  }
})
```

### 9.3 Environment Variables

```bash
# .env.production
VITE_API_BASE_URL=https://api.yourapp.com
VITE_APP_NAME=YourApp
VITE_ENABLE_ANALYTICS=true

# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=YourApp (Dev)
VITE_ENABLE_ANALYTICS=false
```

```typescript
// Usage
const API_URL = import.meta.env.VITE_API_BASE_URL
```

### 9.4 Deployment

**Static hosting (Recommended):**
- Vercel
- Netlify
- Cloudflare Pages
- AWS S3 + CloudFront

**Build output:**
```
dist/
  index.html
  assets/
    index-[hash].js      → Main bundle
    vendor-[hash].js     → Vendor bundle
    pms-[hash].js        → PMS module (lazy)
    pos-[hash].js        → POS module (lazy)
    ...
```

**Nginx configuration (if self-hosting):**
```nginx
server {
  listen 80;
  server_name app.yourapp.com;
  root /var/www/app/dist;

  # SPA fallback
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets
  location /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # Security headers
  add_header X-Frame-Options "SAMEORIGIN";
  add_header X-Content-Type-Options "nosniff";
  add_header X-XSS-Protection "1; mode=block";
}
```

---

## Part 10: Implementation Checklist

### 10.1 Phase 1: Foundation
- [ ] Setup Vite + React + TypeScript
- [ ] Install Tailwind CSS + shadcn/ui
- [ ] Setup React Router with route structure
- [ ] Create App Shell layout (sidebar, top bar)
- [ ] Implement context providers (AppContext, AuthContext)

### 10.2 Phase 2: Authentication
- [ ] Build login page
- [ ] Build tenant picker page
- [ ] Implement protected route guard
- [ ] Setup API client with token injection
- [ ] Implement logout flow

### 10.3 Phase 3: Tenant Management
- [ ] Build tenant switcher component
- [ ] Implement X-Tenant-ID header injection
- [ ] Setup localStorage persistence
- [ ] Implement tenant context loading

### 10.4 Phase 4: Module System
- [ ] Create module route guards
- [ ] Implement permission-based navigation
- [ ] Setup lazy loading for modules
- [ ] Build module launcher UI

### 10.5 Phase 5: Authorization
- [ ] Implement permission guard component
- [ ] Build feature flag system
- [ ] Setup subscription validation
- [ ] Hide/show modules based on access

### 10.6 Phase 6: Production Ready
- [ ] Setup error boundaries
- [ ] Implement logging (integrate with STD-17)
- [ ] Configure code splitting
- [ ] Setup environment variables
- [ ] Build deployment pipeline
- [ ] Configure security headers

---

## Summary

**One-liner:**
> **Login → Select Tenant → App Shell → Select Module**

**Key Principles:**
1. **Single SPA** with App Shell pattern
2. **Tenant = context**, selected after login
3. **Modules = lazy-loaded** based on permissions
4. **Frontend = UI only**, backend = authority
5. **Hidden by default**, visible only if allowed

**Architecture Benefits:**
- ✅ Seamless UX (no page reloads)
- ✅ Shared infrastructure & design system
- ✅ Single deployment artifact
- ✅ Better security (backend validation)
- ✅ Scalable (easy to add new modules)

---

**Related Documents:**
- SEC-01: Security & Authentication (backend auth flows)
- UI-01: Design System (Tailwind + shadcn/ui)
- UI-02: Components (reusable UI components)
- UI-03: Wireframes & Flows (visual designs)
- STD-17: Logging & Observability (structured logging)
