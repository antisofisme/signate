# INFRA-DEC-007: Identity Model & Entity Hierarchy

**VERSION**: Layer 0 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines the identity model for ARSAKA_PUGUH SaaS transformation:
- **User**: Global identity across the platform
- **Tenant**: Organization/workspace boundary
- **Project**: Sub-workspace within tenant for resource isolation
- **Membership**: User-to-Tenant relationship with roles

---

## Entity Hierarchy

```
User (global identity)
  └── TenantMembership (role: owner/admin/member/viewer)
        └── Tenant (organization/workspace)
              └── Project (sub-workspace)
                    └── Rules, Decisions, Workflows (scoped)
```

**Key Principles**:
1. One email = one User (global identity)
2. User can belong to N tenants (via memberships)
3. Tenant can have N projects (sub-workspaces)
4. Resources (Rules, Decisions, Workflows) are scoped to Tenant OR Project

---

## 1. User Entity (Global Identity)

### Definition

A **User** is a global identity representing a person who can access the platform.

```typescript
User {
  user_id: UUID              // Primary key, immutable
  email: string              // UNIQUE, verified
  password_hash: string      // bcrypt hash (null if OAuth-only)

  // Authentication
  auth_provider: "local" | "google" | "github"  // Primary auth method
  oauth_provider_id: string  // Provider-specific ID (null if local)

  // Profile (metadata, non-logical)
  display_name: string       // Display name (can change)
  avatar_url: string         // Profile picture URL

  // Status
  status: "active" | "suspended" | "pending_verification"
  email_verified_at: timestamp | null

  // Timestamps
  created_at: timestamp
  updated_at: timestamp
  last_login_at: timestamp | null
}
```

### Validation Rules

```
GR-USR-1: Email Uniqueness
  - Email MUST be unique across all users
  - Email is case-insensitive (stored lowercase)
  - Email change requires re-verification

GR-USR-2: Status Restrictions
  - "pending_verification" users CANNOT access dashboard
  - "suspended" users CANNOT login
  - Only "active" users have full access

GR-USR-3: Auth Provider
  - Local auth requires password_hash
  - OAuth auth requires oauth_provider_id
  - User can have both (link accounts)
```

### Database Schema

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255),

  auth_provider VARCHAR(20) NOT NULL DEFAULT 'local',
  oauth_provider_id VARCHAR(255),

  display_name VARCHAR(100),
  avatar_url VARCHAR(500),

  status VARCHAR(30) NOT NULL DEFAULT 'pending_verification',
  email_verified_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMPTZ,

  CONSTRAINT check_auth_provider CHECK (
    auth_provider IN ('local', 'google', 'github')
  ),
  CONSTRAINT check_status CHECK (
    status IN ('active', 'suspended', 'pending_verification')
  ),
  CONSTRAINT check_local_password CHECK (
    auth_provider != 'local' OR password_hash IS NOT NULL
  ),
  CONSTRAINT check_oauth_id CHECK (
    auth_provider = 'local' OR oauth_provider_id IS NOT NULL
  )
);

CREATE INDEX idx_users_email ON users(LOWER(email));
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_oauth ON users(auth_provider, oauth_provider_id);
```

---

## 2. Tenant Entity (Organization)

### Definition

A **Tenant** is an organizational boundary representing a company, team, or workspace.

```typescript
Tenant {
  tenant_id: UUID            // Primary key, immutable

  // Identity
  name: string               // Display name (e.g., "Acme Corp")
  slug: string               // UNIQUE, URL-safe (e.g., "acme-corp")

  // Ownership
  owner_user_id: UUID        // FK to users.user_id

  // Subscription
  plan: "free" | "starter" | "pro" | "enterprise"

  // Status
  status: "active" | "suspended" | "trial"
  trial_ends_at: timestamp | null

  // Timestamps
  created_at: timestamp
  updated_at: timestamp
}
```

### Validation Rules

```
GR-TEN-1: Slug Uniqueness
  - Slug MUST be unique across all tenants
  - Slug is URL-safe (lowercase, alphanumeric, hyphens)
  - Slug CANNOT be changed after creation

GR-TEN-2: Owner Requirements
  - Every tenant MUST have an owner
  - Owner MUST be a verified user
  - Owner gets "owner" role automatically

GR-TEN-3: Status Restrictions
  - "suspended" tenants CANNOT access resources
  - "trial" tenants have limited features
  - Only "active" tenants have full access

GR-TEN-4: Plan Limits
  - Free: 1 project, 1K decisions/month
  - Starter: 5 projects, 10K decisions/month
  - Pro: Unlimited projects, 100K decisions/month
  - Enterprise: Custom limits
```

### Database Schema

```sql
CREATE TABLE tenants (
  tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  name VARCHAR(100) NOT NULL,
  slug VARCHAR(50) NOT NULL UNIQUE,

  owner_user_id UUID NOT NULL REFERENCES users(user_id),

  plan VARCHAR(20) NOT NULL DEFAULT 'free',

  status VARCHAR(20) NOT NULL DEFAULT 'active',
  trial_ends_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT check_plan CHECK (
    plan IN ('free', 'starter', 'pro', 'enterprise')
  ),
  CONSTRAINT check_status CHECK (
    status IN ('active', 'suspended', 'trial')
  ),
  CONSTRAINT check_slug_format CHECK (
    slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' AND
    LENGTH(slug) >= 3 AND
    LENGTH(slug) <= 50
  )
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_owner ON tenants(owner_user_id);
CREATE INDEX idx_tenants_plan ON tenants(plan);
```

---

## 3. Tenant Membership Entity

### Definition

A **TenantMembership** represents a user's membership in a tenant with a specific role.

```typescript
TenantMembership {
  user_id: UUID              // FK to users.user_id
  tenant_id: UUID            // FK to tenants.tenant_id

  // Role
  role: "owner" | "admin" | "member" | "viewer"

  // Status
  status: "active" | "invited" | "suspended"
  invited_by_user_id: UUID   // Who invited this user
  invited_at: timestamp
  accepted_at: timestamp | null

  // Timestamps
  created_at: timestamp
  updated_at: timestamp
}
```

### Role Permissions

| Permission | Owner | Admin | Member | Viewer |
|------------|-------|-------|--------|--------|
| View resources | ✅ | ✅ | ✅ | ✅ |
| Create/edit rules | ✅ | ✅ | ✅ | ❌ |
| Create decisions | ✅ | ✅ | ✅ | ❌ |
| Approve workflows | ✅ | ✅ | ✅* | ❌ |
| Manage projects | ✅ | ✅ | ❌ | ❌ |
| Invite members | ✅ | ✅ | ❌ | ❌ |
| Manage billing | ✅ | ❌ | ❌ | ❌ |
| Transfer ownership | ✅ | ❌ | ❌ | ❌ |
| Delete tenant | ✅ | ❌ | ❌ | ❌ |

*Member can only approve if assigned as approver in workflow

### Validation Rules

```
GR-MEM-1: Unique Membership
  - User can have only ONE membership per tenant
  - (user_id, tenant_id) is UNIQUE

GR-MEM-2: Owner Constraint
  - Exactly ONE owner per tenant
  - Owner CANNOT be demoted
  - Owner CANNOT leave (must transfer first)

GR-MEM-3: Invitation Flow
  - New members start as "invited"
  - "invited" users CANNOT access tenant
  - Accepting invitation changes status to "active"

GR-MEM-4: Status Restrictions
  - "suspended" members CANNOT access tenant
  - Only "active" members have full access
```

### Database Schema

```sql
CREATE TABLE tenant_memberships (
  user_id UUID NOT NULL REFERENCES users(user_id),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

  role VARCHAR(20) NOT NULL DEFAULT 'member',

  status VARCHAR(20) NOT NULL DEFAULT 'invited',
  invited_by_user_id UUID REFERENCES users(user_id),
  invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  accepted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  PRIMARY KEY (user_id, tenant_id),

  CONSTRAINT check_role CHECK (
    role IN ('owner', 'admin', 'member', 'viewer')
  ),
  CONSTRAINT check_status CHECK (
    status IN ('active', 'invited', 'suspended')
  )
);

CREATE INDEX idx_memberships_user ON tenant_memberships(user_id);
CREATE INDEX idx_memberships_tenant ON tenant_memberships(tenant_id);
CREATE INDEX idx_memberships_role ON tenant_memberships(tenant_id, role);

-- Enforce exactly one owner per tenant
CREATE UNIQUE INDEX idx_memberships_owner ON tenant_memberships(tenant_id)
  WHERE role = 'owner';
```

---

## 4. Project Entity

### Definition

A **Project** is a sub-workspace within a tenant for resource isolation.

```typescript
Project {
  project_id: UUID           // Primary key, immutable
  tenant_id: UUID            // FK to tenants.tenant_id

  // Identity
  name: string               // Display name (e.g., "Production")
  slug: string               // Unique within tenant (e.g., "production")
  description: string        // Optional description

  // Environment
  environment: "production" | "staging" | "development"

  // Status
  is_default: boolean        // Is this the default project?

  // Timestamps
  created_at: timestamp
  updated_at: timestamp
}
```

### Validation Rules

```
GR-PRJ-1: Slug Uniqueness (Tenant-Scoped)
  - Slug MUST be unique within tenant
  - (tenant_id, slug) is UNIQUE
  - Slug is URL-safe

GR-PRJ-2: Default Project
  - Every tenant MUST have exactly one default project
  - Default project is auto-created on tenant creation
  - Default project CANNOT be deleted

GR-PRJ-3: Plan Limits
  - Free plan: max 1 project
  - Starter plan: max 5 projects
  - Pro/Enterprise: unlimited

GR-PRJ-4: Project Access
  - All tenant members can access all projects
  - Project-level permissions may be added in v2
```

### Database Schema

```sql
CREATE TABLE projects (
  project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

  name VARCHAR(100) NOT NULL,
  slug VARCHAR(50) NOT NULL,
  description TEXT,

  environment VARCHAR(20) NOT NULL DEFAULT 'production',

  is_default BOOLEAN NOT NULL DEFAULT FALSE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(tenant_id, slug),

  CONSTRAINT check_environment CHECK (
    environment IN ('production', 'staging', 'development')
  ),
  CONSTRAINT check_slug_format CHECK (
    slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$' AND
    LENGTH(slug) >= 3 AND
    LENGTH(slug) <= 50
  )
);

CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_projects_environment ON projects(tenant_id, environment);

-- Enforce exactly one default project per tenant
CREATE UNIQUE INDEX idx_projects_default ON projects(tenant_id)
  WHERE is_default = TRUE;
```

---

## 5. Resource Scoping Rules

### Hybrid Scope Model

Resources (Rules, Decisions, Workflows) can be scoped at two levels:

1. **Tenant-Level** (shared across projects)
   - `project_id IS NULL`
   - Visible in all projects within tenant
   - Use case: Global rules like "all transactions > $10K need CFO approval"

2. **Project-Level** (isolated)
   - `project_id IS NOT NULL`
   - Visible only in specific project
   - Use case: Environment-specific rules

```
┌─────────────────────────────────────────────────────────────────┐
│                          TENANT                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Tenant-Level Rules (project_id = NULL)                     │ │
│  │ - Rule A: "All transactions > $10K need CFO approval"      │ │
│  │ - Rule B: "Block transactions from blacklisted vendors"    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PROJECT: Prod │  │ PROJECT: Staging│  │  PROJECT: Dev   │ │
│  │                 │  │                 │  │                 │ │
│  │ Project Rules:  │  │ Project Rules:  │  │ Project Rules:  │ │
│  │ - Rule C        │  │ - Rule D        │  │ - Rule E        │ │
│  │                 │  │ (less strict)   │  │ (no approval)   │ │
│  │ Decisions:      │  │ Decisions:      │  │ Decisions:      │ │
│  │ - Dec-001       │  │ - Dec-100       │  │ - Dec-200       │ │
│  │ - Dec-002       │  │ - Dec-101       │  │ - Dec-201       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Rule Evaluation Order

When evaluating a decision in a project:

```
1. Load project-level rules (project_id = current_project)
2. Load tenant-level rules (project_id IS NULL)
3. Merge rules (project-level takes precedence if same decision_type)
4. Evaluate merged rules (first-match-wins)
```

### Resource Scope Table

| Resource | Tenant-Scoped | Project-Scoped | Notes |
|----------|---------------|----------------|-------|
| Rules | ✅ (shared) | ✅ (isolated) | Hybrid, project rules override |
| Decisions | ❌ | ✅ (required) | Always project-scoped |
| Workflows | ❌ | ✅ (required) | Always project-scoped |
| Events | ❌ | ✅ (required) | Always project-scoped |
| Audit Log | ✅ (filterable) | ✅ (filterable) | Queryable by both |

### Database Updates

Add `project_id` to existing tables:

```sql
-- Add project_id to rules (nullable = tenant-level)
ALTER TABLE rules ADD COLUMN project_id UUID REFERENCES projects(project_id);
CREATE INDEX idx_rules_project ON rules(tenant_id, project_id);

-- Add project_id to decisions (required)
ALTER TABLE decisions ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);
CREATE INDEX idx_decisions_project ON decisions(tenant_id, project_id);

-- Add project_id to workflows (required)
ALTER TABLE workflows ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);
CREATE INDEX idx_workflows_project ON workflows(tenant_id, project_id);

-- Add project_id to event_log (required)
ALTER TABLE event_log ADD COLUMN project_id UUID NOT NULL REFERENCES projects(project_id);
CREATE INDEX idx_events_project ON event_log(tenant_id, project_id);
```

---

## 6. JWT Token Structure

### Access Token Claims

```typescript
AccessToken {
  // Standard claims
  sub: string              // user_id
  iat: number              // Issued at (Unix timestamp)
  exp: number              // Expiration (Unix timestamp)

  // User claims
  email: string
  display_name: string

  // Context claims
  tenants: Array<{
    tenant_id: string
    role: "owner" | "admin" | "member" | "viewer"
    projects: Array<{
      project_id: string
      slug: string
      is_default: boolean
    }>
  }>

  // Active context (current selection)
  active_tenant_id: string | null
  active_project_id: string | null
}
```

### Token Lifecycle

```
Registration Flow:
  1. User registers (status = pending_verification)
  2. Email verification sent
  3. User verifies email (status = active)
  4. Auto-create: Tenant "{name}'s Workspace" + Default Project
  5. Issue access token with tenant/project context
  6. Redirect to /app/{tenant-slug}/{project-slug}/dashboard

Login Flow:
  1. Validate credentials (password or OAuth)
  2. Load user's tenants and projects
  3. If N tenants → Show tenant selector
  4. If N projects → Show project selector
  5. Issue access token with active context
  6. Redirect to /app/{tenant-slug}/{project-slug}/dashboard

Token Refresh:
  - Access token: 15 minutes
  - Refresh token: 7 days
  - Refresh returns new access token with same context
```

---

## 7. Auto-Provisioning on Registration

### Flow

```
1. User completes registration
   └── User created (status = pending_verification)

2. User verifies email
   └── User updated (status = active)

3. Auto-create Tenant
   └── Tenant created:
       - name: "{display_name}'s Workspace"
       - slug: auto-generated from display_name
       - owner_user_id: user_id
       - plan: "free"
       - status: "active"

4. Auto-create Membership
   └── TenantMembership created:
       - user_id: user_id
       - tenant_id: tenant_id
       - role: "owner"
       - status: "active"

5. Auto-create Default Project
   └── Project created:
       - name: "Default"
       - slug: "default"
       - tenant_id: tenant_id
       - is_default: true
       - environment: "production"

6. Issue Token
   └── JWT with tenant/project context

7. Redirect
   └── /app/{tenant-slug}/default/dashboard
```

### Slug Generation

```typescript
function generateSlug(name: string): string {
  // 1. Lowercase
  let slug = name.toLowerCase();

  // 2. Replace spaces/special chars with hyphens
  slug = slug.replace(/[^a-z0-9]+/g, '-');

  // 3. Remove leading/trailing hyphens
  slug = slug.replace(/^-+|-+$/g, '');

  // 4. Truncate to max length
  slug = slug.substring(0, 50);

  // 5. If empty or too short, use random
  if (slug.length < 3) {
    slug = 'workspace-' + randomString(8);
  }

  // 6. Check uniqueness, append number if needed
  let finalSlug = slug;
  let counter = 1;
  while (await tenantExists(finalSlug)) {
    finalSlug = `${slug}-${counter}`;
    counter++;
  }

  return finalSlug;
}
```

---

## 8. Guard Rails (Identity Model)

### GR-IDM-1: Email Uniqueness
```
IF user registration with existing email
THEN registration REJECTED
     error: "Email already exists"
```

### GR-IDM-2: Tenant Slug Uniqueness
```
IF tenant creation with existing slug
THEN creation REJECTED
     error: "Slug already taken"
```

### GR-IDM-3: Single Owner Constraint
```
IF tenant has no owner
THEN system error, audit logged
     tenant suspended until resolved

IF tenant has multiple owners
THEN system error, audit logged
     demote extras to admin
```

### GR-IDM-4: Project Plan Limits
```
IF project creation exceeds plan limit
THEN creation REJECTED
     error: "Plan limit reached. Upgrade to create more projects."
```

### GR-IDM-5: Membership Validation
```
IF user tries to access tenant without membership
THEN access DENIED
     error: 404 (not found, no tenant leak)

IF user tries to access project without tenant membership
THEN access DENIED
     error: 404
```

### GR-IDM-6: OAuth Account Linking
```
IF OAuth login with email that exists (local account)
THEN prompt to link accounts
     require password confirmation
     merge OAuth provider

IF OAuth login with new email
THEN create new user
     auto-verify email (trusted from OAuth)
```

---

## 9. Migration Strategy

### Existing Data Migration

Current state: Single hardcoded tenant with decisions, workflows, rules.

```sql
-- Step 1: Create admin user
INSERT INTO users (user_id, email, password_hash, status, auth_provider)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',  -- Reuse existing tenant_id as user_id
  'admin@example.com',
  '$2b$12$...',  -- bcrypt hash
  'active',
  'local'
);

-- Step 2: Create tenant from existing
INSERT INTO tenants (tenant_id, name, slug, owner_user_id, plan, status)
SELECT
  tenant_id,
  'Migrated Workspace',
  'migrated-workspace',
  '550e8400-e29b-41d4-a716-446655440000',  -- Admin user
  'free',
  'active'
FROM (SELECT '550e8400-e29b-41d4-a716-446655440000'::uuid AS tenant_id) t;

-- Step 3: Create membership
INSERT INTO tenant_memberships (user_id, tenant_id, role, status)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '550e8400-e29b-41d4-a716-446655440000',
  'owner',
  'active'
);

-- Step 4: Create default project
INSERT INTO projects (project_id, tenant_id, name, slug, is_default)
VALUES (
  gen_random_uuid(),
  '550e8400-e29b-41d4-a716-446655440000',
  'Default',
  'default',
  TRUE
);

-- Step 5: Backfill project_id on existing data
UPDATE decisions SET project_id = (
  SELECT project_id FROM projects
  WHERE tenant_id = decisions.tenant_id AND is_default = TRUE
);

UPDATE workflows SET project_id = (
  SELECT project_id FROM projects
  WHERE tenant_id = workflows.tenant_id AND is_default = TRUE
);

-- Rules stay as tenant-level (project_id = NULL) initially
```

---

## 10. Checklist: Identity Model DRAFT

- ✅ User entity defined (global identity)
- ✅ Tenant entity defined (organization boundary)
- ✅ TenantMembership entity defined (role-based access)
- ✅ Project entity defined (sub-workspace)
- ✅ Hybrid scoping model (tenant-level + project-level)
- ✅ JWT structure defined
- ✅ Auto-provisioning flow defined
- ✅ Guard rails defined (7 rules)
- ✅ Database schemas defined
- ✅ Migration strategy defined

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-008: Auth Flow (for registration/login details)
- INFRA-DEC-009: Project Scoping (for rule evaluation details)
- INFRA-DEC-010: Payment/Billing (for plan limits)
