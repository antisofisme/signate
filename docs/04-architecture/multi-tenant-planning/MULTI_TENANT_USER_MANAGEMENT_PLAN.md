# Multi-Tenant User Management - Comprehensive Implementation Plan

**Project:** Digital Signage Management System
**Feature:** Multi-Tenant User Management with Organizations
**Date:** 2025-01-27
**Status:** Planning Complete - Ready for Implementation

---

## 📋 Executive Summary

This document outlines the complete implementation plan for adding enterprise-grade multi-tenant user management to the existing digital signage system. The implementation will add:

- **Multi-Tenancy**: Organization-based isolation with complete data separation
- **User Management**: Full user lifecycle (invite, activate, manage, deactivate)
- **Role-Based Access Control (RBAC)**: Flexible permission system with 4 default roles
- **Authentication**: Secure JWT-based auth with session tracking
- **Authorization**: Granular permission checks across all resources
- **Audit Trail**: Comprehensive activity logging for compliance

### Key Benefits

✅ **Enterprise-Ready**: Supports unlimited organizations and users
✅ **Secure**: Industry-standard JWT auth with bcrypt password hashing
✅ **Scalable**: Designed for thousands of organizations
✅ **Modular**: Clean separation between backend, frontend, and viewer
✅ **Standard**: Follows FastAPI, React, and PostgreSQL best practices
✅ **No Finance Module**: Simplified for private company use (no billing/payments)

---

## 🎯 Project Goals

### Primary Goals

1. **Multi-Organization Support**: Allow multiple companies to use the system with complete data isolation
2. **User Management**: Enable organization admins to manage their team members
3. **Permission System**: Implement flexible RBAC for fine-grained access control
4. **Security**: Ensure data privacy and secure authentication/authorization
5. **User Experience**: Provide intuitive UI for managing users and switching organizations

### Non-Goals (Out of Scope)

❌ Billing and payment processing (for private company use)
❌ Email marketing and newsletters
❌ Advanced analytics and reporting (can be added later)
❌ Mobile app for admin interface (web-only)
❌ SSO/SAML integration (can be added in Phase 2)

---

## 📊 Current System Analysis

### Existing Architecture

**Backend (FastAPI):**
- Location: `/backend/`
- Port: 8001 (Docker container)
- Database: PostgreSQL 5433
- Current Auth: Basic JWT with user roles (admin/editor/viewer)
- **Strength**: Solid foundation with SQLAlchemy models, Pydantic schemas
- **Gap**: No organization model, no multi-tenant isolation

**Frontend (React + Vite):**
- Location: `/web-admin/`
- Port: 3000 (dev mode)
- Stack: React 18, TailwindCSS, Lucide icons
- Current Auth: JWT token in localStorage
- **Strength**: Modern UI with modals, tables, good UX patterns
- **Gap**: No user management UI, no organization switching

**Viewer (Unified Device Client):**
- Location: `/viewer/`
- Port: 8080 (static files on server)
- Purpose: Display content on monitors/TVs/browsers
- **Strength**: Self-registration with activation codes, heartbeat mechanism
- **Gap**: None (viewer doesn't need org awareness - backend handles it)

### Existing Database Tables

**Core Tables (11 total):**
1. `users` - Basic user authentication (needs enhancement)
2. `devices` - Smart TVs and monitors
3. `content` - Media assets (images, videos)
4. `playlists` - Content scheduling
5. `tags` - Device categorization
6. `content_assignments` - Content-to-device/tag mapping
7. `playlist_assignments` - Playlist-to-device/tag mapping
8. `device_tags` - Many-to-many device-tag
9. `playlist_content` - Playlist item ordering
10. `activity_logs` - Audit trail
11. `device_logs` - Device console logs

**Gap Analysis:**
- ❌ No `organizations` table
- ❌ No `roles` table (hardcoded roles)
- ❌ No `user_organizations` junction table
- ❌ Existing tables missing `organization_id` foreign key
- ❌ No row-level security (RLS) for data isolation

---

## 🏗️ Proposed Architecture

### Multi-Tenancy Model

**Schema-Based Multi-Tenancy** (Recommended)
- All organizations share the same database and tables
- Each table has an `organization_id` column
- Data isolation enforced via:
  - Row-level security (RLS) policies
  - Application-level filtering (context injection)
  - Database constraints and indexes

**Why Schema-Based?**
- ✅ Simpler deployment and maintenance
- ✅ Easier to manage backups and migrations
- ✅ Better performance than separate databases
- ✅ Cost-effective for unlimited organizations
- ✅ Standard approach for B2B SaaS

### Database Schema Design

#### New Tables (5 tables)

**1. organizations**
```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    description TEXT,

    -- Contact
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,

    -- Settings
    settings JSONB DEFAULT '{}',

    -- Limits (no billing, just quotas)
    plan_type VARCHAR(50) DEFAULT 'standard',
    device_limit INTEGER DEFAULT 10,
    content_storage_limit_gb INTEGER DEFAULT 100,
    user_limit INTEGER DEFAULT 5,

    -- Status
    status VARCHAR(20) DEFAULT 'active',
    is_verified BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**2. roles**
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT roles_name_org_unique UNIQUE(organization_id, name)
);
```

**3. user_organizations** (Junction Table)
```sql
CREATE TABLE user_organizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id),

    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Invitation
    invited_by INTEGER REFERENCES users(id),
    invitation_token UUID,
    invitation_expires_at TIMESTAMPTZ,

    -- Timestamps
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,

    CONSTRAINT user_org_unique UNIQUE(user_id, organization_id)
);
```

**4. user_sessions**
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,

    ip_address INET,
    user_agent TEXT,
    device_info JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**5. audit_logs** (Enhanced)
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),

    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    entity_uuid UUID,
    old_values JSONB,
    new_values JSONB,

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

#### Enhanced Existing Tables

**All core tables get these additions:**
```sql
ALTER TABLE devices
    ADD COLUMN organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN created_by_user_id INTEGER REFERENCES users(id);

ALTER TABLE content
    ADD COLUMN organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN uploaded_by_user_id INTEGER REFERENCES users(id);

ALTER TABLE playlists
    ADD COLUMN organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN created_by_user_id INTEGER REFERENCES users(id);

ALTER TABLE tags
    ADD COLUMN organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN created_by_user_id INTEGER REFERENCES users(id);
```

**Enhanced users table:**
```sql
ALTER TABLE users
    ADD COLUMN first_name VARCHAR(100),
    ADD COLUMN last_name VARCHAR(100),
    ADD COLUMN display_name VARCHAR(200),
    ADD COLUMN avatar_url VARCHAR(500),
    ADD COLUMN phone VARCHAR(50),
    ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC',
    ADD COLUMN locale VARCHAR(10) DEFAULT 'en',
    ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN email_verified_at TIMESTAMPTZ,
    ADD COLUMN last_login_at TIMESTAMPTZ,
    ADD COLUMN password_changed_at TIMESTAMPTZ;
```

### Permission Model

**Resource-Action Based Permissions**

Format: `{resource}: [actions]`

```json
{
  "devices": ["create", "read", "update", "delete"],
  "content": ["create", "read", "update", "delete"],
  "playlists": ["create", "read", "update", "delete"],
  "users": ["create", "read", "update", "delete"],
  "settings": ["read", "update"],
  "*": ["*"]  // Super admin only
}
```

**System Roles (4 default roles):**

1. **Super Admin** (`super_admin`)
   - Full system access
   - Permissions: `{"*": ["*"]}`
   - Can: Everything
   - Cannot: N/A

2. **Admin** (`admin`)
   - Full organization management
   - Permissions:
     ```json
     {
       "devices": ["create", "read", "update", "delete"],
       "content": ["create", "read", "update", "delete"],
       "playlists": ["create", "read", "update", "delete"],
       "tags": ["create", "read", "update", "delete"],
       "users": ["create", "read", "update", "delete"],
       "settings": ["read", "update"]
     }
     ```
   - Can: Manage all resources, invite users
   - Cannot: Delete organization, change billing

3. **Editor** (`editor`)
   - Content and device management
   - Permissions:
     ```json
     {
       "devices": ["read", "update"],
       "content": ["create", "read", "update", "delete"],
       "playlists": ["create", "read", "update", "delete"],
       "tags": ["read"]
     }
     ```
   - Can: Create/edit content, assign to devices
   - Cannot: Delete devices, manage users

4. **Viewer** (`viewer`)
   - Read-only access
   - Permissions:
     ```json
     {
       "devices": ["read"],
       "content": ["read"],
       "playlists": ["read"],
       "tags": ["read"]
     }
     ```
   - Can: View all resources
   - Cannot: Make any changes

**Custom Roles:**
- Organizations can create custom roles
- Inherit from base role, modify permissions
- Stored in `roles` table with `organization_id`

### Authentication Flow

```
┌─────────────┐                  ┌─────────────┐                  ┌─────────────┐
│   Browser   │                  │   Backend   │                  │  Database   │
└──────┬──────┘                  └──────┬──────┘                  └──────┬──────┘
       │                                │                                │
       │ 1. POST /api/v1/auth/login    │                                │
       │    {email, password}           │                                │
       ├───────────────────────────────>│                                │
       │                                │                                │
       │                                │ 2. Query user by email         │
       │                                ├───────────────────────────────>│
       │                                │                                │
       │                                │ 3. Return user + password_hash │
       │                                │<───────────────────────────────┤
       │                                │                                │
       │                                │ 4. Verify password (bcrypt)    │
       │                                │                                │
       │                                │ 5. Query user_organizations    │
       │                                ├───────────────────────────────>│
       │                                │                                │
       │                                │ 6. Return orgs + roles         │
       │                                │<───────────────────────────────┤
       │                                │                                │
       │                                │ 7. Generate JWT tokens          │
       │                                │    - access_token (15 min)     │
       │                                │    - refresh_token (7 days)    │
       │                                │                                │
       │                                │ 8. Create session record       │
       │                                ├───────────────────────────────>│
       │                                │                                │
       │ 9. Return tokens + user data   │                                │
       │<───────────────────────────────┤                                │
       │                                │                                │
       │ 10. Store in localStorage      │                                │
       │     - access_token             │                                │
       │     - refresh_token            │                                │
       │     - user                     │                                │
       │     - organizations            │                                │
       │                                │                                │
```

**JWT Payload Structure:**
```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@company.com",
  "organization_id": 5,
  "role": "admin",
  "permissions": ["devices:*", "content:*", "users:*"],
  "exp": 1706395200,
  "iat": 1706394300,
  "type": "access"
}
```

### Authorization Context Injection

**Dependency Injection Pattern:**

```python
from fastapi import Depends, Header, HTTPException
from app.core.deps_v2 import OrganizationContext

@router.get("/api/v1/devices")
async def list_devices(
    context: OrganizationContext = Depends(get_current_user_with_context),
    db: AsyncSession = Depends(get_db)
):
    # context contains:
    # - user: User object
    # - organization: Organization object
    # - role: Role object
    # - permissions: Set of permission strings

    # Check permission
    if not context.has_permission("devices", "read"):
        raise HTTPException(403, "No permission")

    # Query with organization filter
    devices = await db.execute(
        select(Device)
        .where(Device.organization_id == context.organization.id)
    )

    return devices.scalars().all()
```

**OrganizationContext Class:**

```python
@dataclass
class OrganizationContext:
    user: User
    organization: Organization
    user_organization: UserOrganization
    role: Role
    permissions: set[str]

    def has_permission(self, resource: str, action: str) -> bool:
        return f"{resource}:{action}" in self.permissions or "*:*" in self.permissions

    def has_any_permission(self, *permissions: str) -> bool:
        return any(perm in self.permissions for perm in permissions)

    def is_admin(self) -> bool:
        return self.role.name in ["admin", "super_admin"]

    def is_super_admin(self) -> bool:
        return self.role.name == "super_admin"
```

---

## 🚀 API Endpoints Design

### Authentication Endpoints

**Base Path:** `/api/v1/auth`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/login` | User login with email/password | ❌ |
| POST | `/logout` | Invalidate session | ✅ |
| POST | `/refresh` | Refresh access token | Refresh Token |
| POST | `/forgot-password` | Request password reset | ❌ |
| POST | `/reset-password` | Reset password with token | ❌ |
| GET | `/me` | Get current user profile | ✅ |
| PUT | `/me` | Update current user profile | ✅ |
| PUT | `/me/password` | Change password | ✅ |

### Organization Endpoints

**Base Path:** `/api/v1/organizations`

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/` | List user's organizations | Auto (user's orgs) |
| POST | `/` | Create organization | Super Admin |
| GET | `/{id}` | Get organization details | Member |
| PUT | `/{id}` | Update organization | Admin |
| DELETE | `/{id}` | Delete organization | Super Admin |
| GET | `/{id}/users` | List organization users | Member |
| POST | `/{id}/invite` | Invite user to org | Admin |
| GET | `/{id}/settings` | Get org settings | Member |
| PUT | `/{id}/settings` | Update org settings | Admin |
| POST | `/{id}/switch` | Switch current org context | Member |

### User Management Endpoints

**Base Path:** `/api/v1/users`

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/` | List users in org | `users:read` |
| POST | `/` | Create user | `users:create` |
| GET | `/{id}` | Get user details | `users:read` |
| PUT | `/{id}` | Update user | `users:update` |
| DELETE | `/{id}` | Delete user | `users:delete` |
| PUT | `/{id}/role` | Change user role | Admin |
| POST | `/{id}/activate` | Activate user | `users:update` |
| POST | `/{id}/deactivate` | Deactivate user | `users:update` |
| GET | `/{id}/activity` | Get user activity log | `users:read` |
| POST | `/invite` | Send invitation | Admin |
| POST | `/accept-invitation` | Accept invitation | ❌ (token-based) |

### Role Management Endpoints

**Base Path:** `/api/v1/roles`

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/` | List roles | Member |
| POST | `/` | Create custom role | Admin |
| GET | `/{id}` | Get role details | Member |
| PUT | `/{id}` | Update role | Admin |
| DELETE | `/{id}` | Delete role | Admin |

### Enhanced Existing Endpoints

**All existing endpoints updated to include organization context:**

```
/api/v1/devices/*       - Filter by organization_id
/api/v1/content/*       - Filter by organization_id
/api/v1/playlists/*     - Filter by organization_id
/api/v1/tags/*          - Filter by organization_id
/api/v1/activities/*    - Filter by organization_id
```

**Header for Organization Selection:**
```
X-Organization-ID: 123
```

If not provided, use user's primary organization.

---

## 🎨 Frontend Architecture

### State Management

**AuthContext** (Global User State)
```javascript
const AuthContext = createContext({
  user: null,
  organizations: [],
  currentOrganization: null,
  isAuthenticated: false,
  login: async (email, password) => {},
  logout: async () => {},
  switchOrganization: async (orgId) => {},
  refreshToken: async () => {}
});
```

**Permission Hooks**
```javascript
// Check single permission
const canCreateDevice = usePermission('devices', 'create');

// Check multiple permissions (any)
const canManageContent = usePermissions(['content:create', 'content:update']);

// Check role
const isAdmin = useRole(['admin', 'super_admin']);
```

### Component Structure

```
web-admin/src/
├── pages/
│   ├── Login.jsx                      # Login screen
│   ├── Users.jsx                      # User management page
│   └── Settings.jsx                   # Organization settings
├── components/
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── ProtectedRoute.jsx
│   │   └── PermissionGuard.jsx
│   ├── organizations/
│   │   ├── OrgSelector.jsx            # Header dropdown
│   │   ├── OrgSettings.jsx
│   │   └── OrgSwitcher.jsx
│   ├── users/
│   │   ├── UserTable.jsx
│   │   ├── UserRow.jsx
│   │   └── modals/
│   │       ├── InviteUserModal.jsx
│   │       ├── UserDetailModal.jsx
│   │       ├── EditUserModal.jsx
│   │       └── ActivityLogModal.jsx
│   └── shared/
│       ├── PermissionCheckbox.jsx
│       └── RoleBadge.jsx
├── contexts/
│   ├── AuthContext.jsx
│   └── OrganizationContext.jsx
├── hooks/
│   ├── useAuth.js
│   ├── usePermission.js
│   ├── useRole.js
│   └── useOrganization.js
└── services/
    ├── authAPI.js
    ├── usersAPI.js
    └── organizationsAPI.js
```

### UI Components

**1. Login Screen**
- Email/password form
- "Remember me" checkbox
- "Forgot password" link
- Organization context (if needed)

**2. Organization Selector (Header Dropdown)**
- Current organization name with chevron
- Dropdown list of user's organizations
- Radio button indicator for current org
- "Create Organization" option (super admin only)

**3. Users Management Page**
- PageHeader with search and filters
- Stats tabs: All, Active, Pending, Deactivated
- Pending invitations section (highlighted)
- Users table with columns:
  - Avatar, Name, Email, Role, Status, Last Active, Actions
- Row actions: Edit, View Details, Activate/Deactivate, Delete

**4. Invite User Modal**
- Email input (supports multiple emails)
- Role selection (radio cards with descriptions)
- Personal message (optional)
- "Send welcome email" checkbox

**5. User Detail Modal**
- User profile information
- Permission list (checkmarks)
- Activity summary
- Quick actions: Edit, Reset Password, Deactivate, Delete

**6. Edit User Modal**
- Full name, email, phone, department
- Role selector
- Active/Deactivated status
- Permissions checkboxes (grouped by category)

**7. Organization Settings**
- Profile: Name, industry, timezone
- Branding: Logo, colors
- Limits: Device, storage, user quotas with usage bars
- Danger Zone: Delete organization

### Responsive Design

**Mobile (< 640px):**
- Login: Full-width card
- Users: Card layout instead of table
- Modals: Full screen
- Floating action button for "Invite User"

**Tablet (640-1024px):**
- Users: Table with horizontal scroll
- Modals: Centered with padding

**Desktop (> 1024px):**
- Full layout as designed
- Hover states
- Tooltips

---

## 🔧 Backend Implementation

### File Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── organization.py         # NEW
│   │   ├── role.py                 # NEW
│   │   ├── user_organization.py    # NEW
│   │   ├── user_session.py         # NEW
│   │   ├── audit_log.py            # ENHANCED
│   │   ├── user.py                 # ENHANCED
│   │   ├── device.py               # Add org_id
│   │   ├── content.py              # Add org_id
│   │   └── playlist.py             # Add org_id
│   ├── schemas/
│   │   ├── organization.py         # NEW
│   │   ├── role.py                 # NEW
│   │   ├── user.py                 # ENHANCED
│   │   └── auth_v2.py              # NEW
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py             # ENHANCED
│   │       ├── organizations.py    # NEW
│   │       ├── users.py            # NEW
│   │       ├── roles.py            # NEW
│   │       ├── devices.py          # Add org filter
│   │       ├── content.py          # Add org filter
│   │       └── playlists.py        # Add org filter
│   ├── core/
│   │   ├── deps_v2.py              # NEW (org context)
│   │   ├── security/
│   │   │   ├── jwt.py              # Enhanced JWT
│   │   │   ├── password.py         # Password utils
│   │   │   └── permissions.py      # NEW
│   │   └── config.py               # Add new settings
│   └── utils/
│       ├── audit.py                # NEW
│       ├── email.py                # NEW
│       └── validators.py           # NEW
├── migrations/
│   └── 006_add_multi_tenancy.sql   # NEW (COMPLETE)
├── scripts/
│   ├── run_migration.py            # NEW
│   └── create_admin.py             # NEW
└── tests/
    ├── test_auth.py
    ├── test_organizations.py
    ├── test_users.py
    └── test_permissions.py
```

### Dependencies to Add

**requirements.txt:**
```txt
# Existing
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# NEW for multi-tenancy
python-slugify>=8.0.1        # Generate organization slugs
aiosmtplib>=3.0.0            # Send invitation emails
jinja2>=3.1.2                # Email templates
slowapi>=0.1.9               # Rate limiting
redis>=5.0.0                 # Session storage (optional)
```

### Environment Variables

**.env additions:**
```bash
# Organization Settings
DEFAULT_ORGANIZATION_NAME="Default Organization"
DEFAULT_ORGANIZATION_SLUG="default-org"

# User Limits
DEFAULT_DEVICE_LIMIT=10
DEFAULT_USER_LIMIT=5
DEFAULT_STORAGE_LIMIT_GB=100

# Email Configuration (for invitations)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@signage.com
SMTP_FROM_NAME="Signage Admin"

# JWT Configuration
JWT_SECRET=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Session Configuration
SESSION_EXPIRE_MINUTES=60
MAX_SESSIONS_PER_USER=5

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

---

## 📱 Viewer Changes

### Analysis

The **viewer (device client) requires MINIMAL changes** because:

✅ Already uses `device_id` for identification
✅ Backend already filters content by `organization_id`
✅ Devices are assigned to organizations when activated by admin
✅ No user authentication needed on viewer
✅ No organization switching needed

### Required Changes

**1. Update API Base URL (if needed)**
- Ensure viewer points to correct backend port (8001)
- Already configured: `API_BASE_URL: "http://192.168.5.12:8001"`

**2. No Code Changes Required**
- ✅ Registration flow works as-is
- ✅ Activation flow works as-is
- ✅ Heartbeat works as-is
- ✅ Content fetching works as-is

**3. Backend Handles Organization Context**
- When device registers, admin assigns it to their organization
- All content queries automatically filtered by device's organization
- Viewer doesn't need to know about organizations

### Optional Enhancements (Future)

- Show organization logo on viewer UI
- Display organization name during activation
- Multi-language support based on org settings

---

## 🔒 Security Considerations

### Authentication Security

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Hashing: bcrypt with cost factor 12

**JWT Security:**
- Algorithm: HS256 (HMAC SHA-256)
- Secret: 32+ character random string
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Token rotation on refresh

**Session Security:**
- Track active sessions per user
- Limit: 5 concurrent sessions
- Auto-logout on inactivity (60 minutes)
- IP address and user agent tracking

### Authorization Security

**Data Isolation:**
- All queries filtered by `organization_id`
- Row-level security policies (optional, for extra safety)
- Foreign key cascades for organization deletion
- Prevent cross-organization data access

**Permission Checks:**
- Every endpoint checks permissions
- Decorators: `@require_permission("resource", "action")`
- Admin cannot edit super admin
- Users cannot modify their own role
- Users cannot deactivate themselves

### API Security

**Rate Limiting:**
- Login: 5 attempts per minute per IP
- Password reset: 3 attempts per hour per email
- API calls: 60 requests per minute per user

**CORS Configuration:**
```python
origins = [
    "http://localhost:3000",           # Dev frontend
    "http://192.168.5.12:8080",        # Viewer
    "http://192.168.5.12:3000",        # Frontend on server
]
```

**Security Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### Input Validation

**Pydantic Schemas:**
- Email: Valid email format
- Password: Complexity rules
- Username: Alphanumeric + underscore
- Phone: International format
- URLs: Valid URL format
- SQL Injection: Prevented by SQLAlchemy ORM

---

## 📝 Migration Strategy

### Phase 0: Preparation (1 day)

**Tasks:**
1. ✅ Backup production database
2. ✅ Review migration script
3. ✅ Test on staging environment
4. ✅ Prepare rollback plan

**Deliverables:**
- Database backup file
- Tested migration script
- Rollback procedure document

### Phase 1: Database Migration (2 hours)

**Steps:**
1. Run migration script: `006_add_multi_tenancy.sql`
2. Create default organization: "Default Organization"
3. Migrate existing users to default org
4. Assign existing devices/content to default org
5. Create system roles (super_admin, admin, editor, viewer)
6. Verify data integrity

**SQL Script:**
```sql
-- Already created: backend/migrations/006_add_multi_tenancy.sql
-- Includes:
-- 1. Create new tables (organizations, roles, user_organizations, etc.)
-- 2. Add organization_id to existing tables
-- 3. Create default organization
-- 4. Migrate existing data
-- 5. Create system roles
-- 6. Add foreign keys and indexes
```

### Phase 2: Backend Implementation (1 week)

**Day 1-2: Models and Schemas**
- ✅ Create Organization, Role, UserOrganization models
- ✅ Create Pydantic schemas for validation
- ✅ Update existing models with organization_id
- ✅ Write unit tests for models

**Day 3-4: Authentication & Authorization**
- ✅ Implement OrganizationContext dependency
- ✅ Update JWT token generation/validation
- ✅ Create permission checking decorators
- ✅ Write auth endpoint handlers

**Day 5: API Endpoints**
- ✅ Implement organization endpoints
- ✅ Implement user management endpoints
- ✅ Update existing endpoints with org filter
- ✅ Write integration tests

**Day 6-7: Testing & Documentation**
- ✅ Comprehensive testing (unit + integration)
- ✅ API documentation (Swagger/OpenAPI)
- ✅ Security audit
- ✅ Performance testing

### Phase 3: Frontend Implementation (1 week)

**Day 1-2: Authentication Flow**
- Create AuthContext
- Implement login page
- Add token refresh logic
- Create ProtectedRoute component

**Day 3-4: User Management UI**
- Create Users page
- Implement user table
- Create invite, edit, detail modals
- Add permission guards

**Day 5: Organization Management**
- Create organization selector
- Implement organization switching
- Add organization settings page
- Update navigation

**Day 6-7: Polish & Testing**
- Responsive design
- Error handling
- Loading states
- E2E testing

### Phase 4: Integration & Testing (3 days)

**Day 1: Integration Testing**
- Backend + Frontend integration
- End-to-end user flows
- Cross-browser testing
- Mobile responsiveness

**Day 2: Security & Performance**
- Security audit
- Performance optimization
- Load testing
- Penetration testing

**Day 3: User Acceptance Testing**
- Internal testing
- Bug fixes
- Documentation updates
- Deployment preparation

### Phase 5: Deployment (1 day)

**Steps:**
1. Deploy backend to server
2. Run database migration
3. Create first super admin user
4. Deploy frontend
5. Smoke tests
6. Monitor for issues

**Rollback Plan:**
- Restore database from backup
- Deploy previous backend version
- Revert frontend deployment

---

## 📊 Testing Strategy

### Unit Tests

**Backend (pytest):**
```python
# Test authentication
test_login_success()
test_login_invalid_password()
test_jwt_token_generation()
test_jwt_token_validation()

# Test permissions
test_permission_check_super_admin()
test_permission_check_admin()
test_permission_check_editor()
test_permission_check_viewer()

# Test organization isolation
test_devices_filtered_by_organization()
test_content_filtered_by_organization()
test_cross_organization_access_denied()

# Test user management
test_create_user()
test_invite_user()
test_activate_user()
test_deactivate_user()
```

**Frontend (Vitest + React Testing Library):**
```javascript
// Test authentication
test('login with valid credentials')
test('login with invalid credentials')
test('token refresh on expiry')
test('logout clears session')

// Test permissions
test('admin can see user management')
test('editor cannot see user management')
test('viewer has read-only access')

// Test organization switching
test('switch organization updates context')
test('switch organization refetches data')
```

### Integration Tests

**API Integration (pytest + httpx):**
```python
# Full user flow
async def test_user_invitation_flow():
    # 1. Admin invites user
    # 2. User receives invitation
    # 3. User accepts invitation
    # 4. User logs in
    # 5. User accesses resources

# Organization switching
async def test_organization_switching():
    # 1. User has multiple orgs
    # 2. Login returns all orgs
    # 3. Switch to different org
    # 4. Verify data changes
```

### E2E Tests (Playwright/Cypress)

```javascript
// Complete user journey
test('admin invites and manages user', async ({ page }) => {
  // 1. Login as admin
  await page.goto('/login');
  await page.fill('input[type=email]', 'admin@test.com');
  await page.fill('input[type=password]', 'password');
  await page.click('button[type=submit]');

  // 2. Navigate to users page
  await page.click('text=Users');

  // 3. Invite new user
  await page.click('text=Invite User');
  await page.fill('input[type=email]', 'newuser@test.com');
  await page.selectOption('select[name=role]', 'editor');
  await page.click('text=Send Invite');

  // 4. Verify invitation sent
  await expect(page.locator('text=Invitation sent')).toBeVisible();
});
```

---

## 🚀 Deployment Plan

### Server Setup

**Current Server:**
- IP: 192.168.5.12
- SSH: gzjbbk@192.168.5.12 (Password@2021)
- Docker: Already running backend + database

**Deployment Steps:**

**1. Update Backend (15 minutes)**
```bash
# SSH to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Navigate to project
cd /home/gzjbbk/signage

# Pull latest code
git pull origin main

# Backup database
docker exec signage-db pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
docker exec signage-backend python scripts/run_migration.py

# Rebuild backend container
docker-compose up -d --build backend-api

# Verify
curl http://192.168.5.12:8001/api/v1/auth/me
```

**2. Create Default Admin (5 minutes)**
```bash
# Create super admin user
docker exec -it signage-backend python scripts/create_admin.py

# Follow prompts:
# Email: admin@signage.local
# Password: [secure password]
# Name: System Administrator
```

**3. Deploy Frontend (10 minutes)**
```bash
# Build frontend locally
cd web-admin
npm run build

# Copy to server
sshpass -p 'Password@2021' scp -r dist/* gzjbbk@192.168.5.12:/home/gzjbbk/signage/web-admin/dist/

# Or deploy to static hosting
```

**4. Smoke Tests (5 minutes)**
```bash
# Test backend health
curl http://192.168.5.12:8001/health

# Test login
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@signage.local","password":"yourpassword"}'

# Test organization list
curl http://192.168.5.12:8001/api/v1/organizations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Monitoring

**Health Checks:**
- Backend: `http://192.168.5.12:8001/health`
- Database: `docker exec signage-db pg_isready`
- Viewer: `http://192.168.5.12:8080/`

**Logging:**
```bash
# Backend logs
docker logs -f signage-backend

# Database logs
docker logs -f signage-db
```

**Metrics to Monitor:**
- API response times
- Database query performance
- Active user sessions
- Failed login attempts
- Error rates

---

## 📅 Timeline & Milestones

### Overall Timeline: 3 weeks

**Week 1: Backend Foundation**
- Days 1-2: Database migration + models
- Days 3-4: Authentication & authorization
- Days 5-7: API endpoints + testing

**Week 2: Frontend Development**
- Days 1-2: Auth flow + protected routes
- Days 3-4: User management UI
- Days 5-7: Organization management + polish

**Week 3: Integration & Deployment**
- Days 1-2: Integration testing
- Days 3-4: Security audit + performance
- Day 5: Staging deployment + UAT
- Days 6-7: Production deployment + monitoring

### Milestones

✅ **M1: Database Ready** (Day 2)
- Migration completed
- Default org created
- System roles created

✅ **M2: Backend API Complete** (Day 7)
- All endpoints implemented
- Tests passing (>90% coverage)
- Documentation updated

✅ **M3: Frontend Complete** (Day 14)
- All UI components implemented
- E2E tests passing
- Responsive design verified

✅ **M4: Production Deployed** (Day 21)
- Deployed to server
- Smoke tests passed
- Monitoring active

---

## 📚 Documentation Deliverables

### Technical Documentation

1. **API Reference**
   - OpenAPI/Swagger spec
   - Endpoint descriptions
   - Request/response examples
   - Error codes

2. **Database Schema**
   - ERD diagram
   - Table descriptions
   - Relationship mappings
   - Migration guide

3. **Security Guide**
   - Authentication flow
   - Authorization model
   - Security best practices
   - Threat model

4. **Deployment Guide**
   - Server setup
   - Migration steps
   - Rollback procedures
   - Troubleshooting

### User Documentation

1. **Admin Guide**
   - User management
   - Organization settings
   - Permission assignment
   - Troubleshooting

2. **User Guide**
   - Login and access
   - Profile management
   - Organization switching
   - Feature overview

---

## 🎯 Success Criteria

### Functional Requirements

✅ Users can be invited to organizations
✅ Users can accept invitations and set passwords
✅ Users can log in with email/password
✅ Users can switch between organizations
✅ Admins can manage team members
✅ Admins can assign roles and permissions
✅ All resources are organization-scoped
✅ Audit logs track all changes

### Non-Functional Requirements

✅ **Performance**: API response < 200ms (p95)
✅ **Scalability**: Support 1000+ organizations
✅ **Security**: Pass security audit
✅ **Reliability**: 99.9% uptime
✅ **Usability**: Users can complete tasks without training
✅ **Maintainability**: Code coverage > 90%

### Acceptance Tests

1. ✅ Admin can invite 5 users successfully
2. ✅ Users receive invitation emails
3. ✅ Users can accept invitations
4. ✅ Users can log in and access resources
5. ✅ Organization switching works correctly
6. ✅ Permissions are enforced correctly
7. ✅ Data isolation prevents cross-org access
8. ✅ Audit logs capture all actions

---

## 🔗 Related Documentation

### Implementation Guides (Already Created)

1. **Database Architecture** (`BACKEND_API_ARCHITECTURE.md`)
   - Complete database schema design
   - Models and relationships
   - Migration strategy

2. **Backend API Guide** (`MULTI_TENANT_IMPLEMENTATION_GUIDE.md` Parts 1-3)
   - FastAPI implementation
   - Authentication & authorization
   - Testing and deployment

3. **Frontend Architecture** (`MULTI_TENANT_FRONTEND_ARCHITECTURE.md`)
   - React component structure
   - State management
   - UI/UX design

4. **Security Guide** (`SECURITY_ARCHITECTURE.md`)
   - Security best practices
   - Threat mitigation
   - Compliance

5. **Quick Start** (`MULTI_TENANT_QUICK_START.md`)
   - 30-minute setup guide
   - Common issues
   - API reference

6. **Visual Guide** (`VISUAL_GUIDE.md`)
   - Flow diagrams
   - Component hierarchy
   - User journeys

7. **UI/UX Design** (From UI/UX agent)
   - Wireframes
   - Component specifications
   - Interaction patterns

---

## 🤝 Team Responsibilities

### Backend Developer
- Implement database models
- Create API endpoints
- Write backend tests
- Security implementation
- Performance optimization

### Frontend Developer
- Implement React components
- State management
- API integration
- Frontend tests
- Responsive design

### DevOps Engineer
- Database migration
- Server deployment
- Monitoring setup
- Backup procedures
- Performance tuning

### QA Engineer
- Test plan creation
- Manual testing
- Automated testing
- Security testing
- UAT coordination

### Product Owner
- Requirements review
- UAT testing
- Documentation review
- Go-live approval
- User training

---

## 🚨 Risks & Mitigation

### Risk 1: Data Migration Failure
**Impact:** High
**Probability:** Low
**Mitigation:**
- Comprehensive backup before migration
- Test migration on staging first
- Rollback plan ready
- Verify data integrity after migration

### Risk 2: Performance Degradation
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- Add database indexes on organization_id
- Implement query optimization
- Load testing before deployment
- Monitor performance metrics

### Risk 3: Security Vulnerabilities
**Impact:** High
**Probability:** Low
**Mitigation:**
- Security audit before deployment
- Rate limiting on auth endpoints
- Regular security updates
- Penetration testing

### Risk 4: User Adoption Issues
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- User-friendly UI design
- Comprehensive user documentation
- Training sessions
- Gradual rollout

---

## 📞 Support & Maintenance

### Post-Deployment Support

**Week 1: Intensive Monitoring**
- Monitor all endpoints
- Track error rates
- User feedback collection
- Quick bug fixes

**Week 2-4: Stabilization**
- Address reported issues
- Performance tuning
- Documentation updates
- User training

**Ongoing: Maintenance**
- Regular security updates
- Feature enhancements
- Performance optimization
- User support

### Escalation Path

1. **Level 1**: User documentation & FAQ
2. **Level 2**: Admin user support
3. **Level 3**: Development team
4. **Level 4**: System administrator

---

## ✅ Next Steps

### Immediate Actions (Today)

1. ✅ Review this planning document
2. ✅ Get stakeholder approval
3. ✅ Set up development environment
4. ✅ Create project board/tickets

### This Week

1. ✅ Run database migration on staging
2. ✅ Start backend implementation
3. ✅ Create UI mockups
4. ✅ Set up CI/CD pipeline

### Next Week

1. ✅ Complete backend implementation
2. ✅ Start frontend development
3. ✅ Write tests
4. ✅ Security audit

### Week 3

1. ✅ Integration testing
2. ✅ User acceptance testing
3. ✅ Production deployment
4. ✅ Monitoring and support

---

## 📖 Glossary

**Multi-Tenancy**: Architecture where a single instance serves multiple organizations (tenants) with complete data isolation.

**RBAC**: Role-Based Access Control - permission system based on user roles.

**JWT**: JSON Web Token - standard for secure authentication tokens.

**Organization**: A company/tenant in the multi-tenant system.

**Context Injection**: Pattern to automatically provide organization context to API endpoints.

**Row-Level Security (RLS)**: Database-level security that filters rows based on user context.

**Permission**: Fine-grained access control in format "resource:action".

**System Role**: Pre-defined roles (super_admin, admin, editor, viewer).

**Custom Role**: Organization-specific roles with custom permissions.

---

## 📝 Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-01-27 | 1.0 | Initial planning document created | AI Team |

---

## 🎉 Conclusion

This comprehensive plan provides a **complete roadmap** for implementing enterprise-grade multi-tenant user management in your digital signage system. The implementation is:

✅ **Well-Architected**: Standard multi-tenancy patterns
✅ **Secure**: Industry-standard security practices
✅ **Scalable**: Designed for thousands of organizations
✅ **Maintainable**: Clean code structure and documentation
✅ **User-Friendly**: Intuitive UI/UX design
✅ **Production-Ready**: Complete with testing and deployment

**All supporting documentation has been created and is ready for implementation.**

The system will enable your digital signage platform to:
- Support unlimited organizations
- Provide complete data isolation
- Offer flexible role-based permissions
- Deliver a professional user management experience
- Scale to enterprise requirements

**Ready to begin implementation!** 🚀
