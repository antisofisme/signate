# PUGUH Platform Architecture

## Vision

PUGUH adalah platform infrastruktur yang menyediakan fondasi untuk aplikasi SaaS. Mirip dengan:
- **Google Identity Platform** - Auth, user management
- **Azure AD / Entra ID** - Enterprise identity
- **Stripe Atlas** - Billing infrastructure

Tujuan: App creators fokus pada domain features, bukan rebuild auth/tenant/billing.

---

## Platform Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PUGUH PLATFORM                                     │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         PUGUH PORTAL                                   │  │
│  │                   (Central Management UI)                              │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Identity   │  │   Tenant    │  │   Billing   │  │   Product   │   │  │
│  │  │  (Users)    │  │   (Orgs)    │  │  (Subs)     │  │  Switcher   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                        │  │
│  │  URL: portal.puguh.io                                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      │ Provides                              │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         PUGUH APIs                                     │  │
│  │                                                                        │  │
│  │  /api/v1/auth/*     - Authentication                                  │  │
│  │  /api/v1/tenants/*  - Multi-tenancy                                   │  │
│  │  /api/v1/projects/* - Project isolation                               │  │
│  │  /api/v1/billing/*  - Subscriptions & payments                        │  │
│  │  /api/v1/products/* - Product catalog                                 │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      │ SDK                                   │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         PUGUH SDK                                      │  │
│  │                                                                        │  │
│  │  Python:     pip install puguh-sdk                                    │  │
│  │  TypeScript: npm install @puguh/sdk                                   │  │
│  │  Go:         go get github.com/arsaka-puguh/sdk-go                     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Integrates
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCT APPS                                       │
│                     (Built by App Creators)                                  │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │     MANTRA      │  │   Product B     │  │   Product C     │              │
│  │                 │  │                 │  │                 │              │
│  │ Decision Gov    │  │  (Your App)     │  │  (Your App)     │              │
│  │ AI Assistant    │  │                 │  │                 │              │
│  │ Semantic Search │  │                 │  │                 │              │
│  │                 │  │                 │  │                 │              │
│  │ Uses PUGUH SDK  │  │ Uses PUGUH SDK  │  │ Uses PUGUH SDK  │              │
│  │ for:            │  │ for:            │  │ for:            │              │
│  │ - Auth          │  │ - Auth          │  │ - Auth          │              │
│  │ - Tenant        │  │ - Tenant        │  │ - Tenant        │              │
│  │ - Billing       │  │ - Billing       │  │ - Billing       │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                              │
│  Each product:                                                               │
│  - Has its own frontend & backend                                            │
│  - Focuses only on domain features                                           │
│  - NO auth/tenant/billing code                                               │
│  - Uses PUGUH SDK for infrastructure                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Hierarchy

```
Platform Level (PUGUH Operators):
├── platform_admin         # Platform operators (you, the platform owner)
│   └── Can: See all tenants, revenue, system config
│
Tenant Level (Subscribers):
├── owner                  # Subscriber who pays
│   └── Can: Full control, billing, delete org
│
├── admin                  # Delegated admin
│   └── Can: Manage members, projects, settings (not billing)
│
├── member                 # Regular team member
│   └── Can: Access products based on role
│
└── viewer                 # Read-only access
    └── Can: View only

Product Level (Per-Product Roles):
├── {product}:admin        # Product admin
├── {product}:editor       # Can create/edit
└── {product}:viewer       # Read-only
```

### Role Examples

```json
// Platform Admin (You)
{
  "user_id": "uuid",
  "roles": ["platform_admin"],
  "can_impersonate": true,
  "can_view_all_tenants": true
}

// Tenant Owner
{
  "user_id": "uuid",
  "tenant_id": "tenant_uuid",
  "roles": ["owner", "mantra:admin", "product_b:admin"],
  "is_owner": true
}

// Regular Member
{
  "user_id": "uuid",
  "tenant_id": "tenant_uuid",
  "roles": ["member", "mantra:editor", "product_b:viewer"],
  "is_owner": false
}
```

---

## Dashboard Hierarchy

### 1. Platform Admin Dashboard (For Platform Operators)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PUGUH Platform Admin                                [Admin ▼] [Logout] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Sidebar:                      │  Content:                              │
│  ┌──────────────────────┐      │  ┌────────────────────────────────┐   │
│  │ 📊 Platform Overview │      │  │ PLATFORM METRICS               │   │
│  │ 🏢 All Tenants       │      │  │                                │   │
│  │ 👤 All Users         │      │  │ Total Tenants: 150             │   │
│  │ 📦 Products          │      │  │ Active Subscriptions: 120      │   │
│  │ 💰 Revenue           │      │  │ MRR: $12,000                   │   │
│  │ 🔧 System Config     │      │  │ API Calls (30d): 1.2M          │   │
│  │ 📋 Platform Audit    │      │  │                                │   │
│  │ 🚨 Alerts            │      │  │ [Tenant Growth Chart]          │   │
│  │ ─────────────────    │      │  │ [Revenue Chart]                │   │
│  │ 🔀 Switch to Tenant  │      │  │ [System Health]                │   │
│  └──────────────────────┘      │  └────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Features:
- See all tenants with usage metrics
- Revenue analytics (MRR, ARR, churn)
- System health monitoring
- Impersonate tenant for support
- Product catalog management
- Platform configuration
```

### 2. Tenant Owner Dashboard (For Subscribers)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PUGUH Portal           [My Company ▼] [← Products]    [User ▼] [Help] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Sidebar:                      │  Content:                              │
│  ┌──────────────────────┐      │  ┌────────────────────────────────┐   │
│  │ 🏠 Dashboard         │      │  │ ORGANIZATION OVERVIEW          │   │
│  │ 👥 Members           │      │  │                                │   │
│  │ 📁 Projects          │      │  │ Plan: Pro ($99/mo)             │   │
│  │ 💳 Billing           │      │  │ Members: 8 / 50                │   │
│  │ 🔑 API Keys          │      │  │ Projects: 3 / unlimited        │   │
│  │ ⚙️  Settings          │      │  │                                │   │
│  │ 📋 Audit Log         │      │  │ Usage This Month:              │   │
│  │ ─────────────────    │      │  │ - MANTRA: 2,500 decisions      │   │
│  │ 📦 Products:         │      │  │ - API Calls: 45,000            │   │
│  │   ├── MANTRA ✓       │      │  │                                │   │
│  │   ├── Product B 🔒   │      │  │ [Quick Actions]                │   │
│  │   └── Product C 🔒   │      │  │ - Invite Member                │   │
│  └──────────────────────┘      │  │ - Create Project               │   │
│                                │  │ - Upgrade Plan                 │   │
│                                │  └────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Features:
- Organization overview
- Member management (invite, roles)
- Project management
- Billing & subscription
- API keys for integrations
- Audit log
- Product switcher
```

### 3. Product Dashboard (For End Users)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MANTRA              [My Company] [Project A ▼]   [← Portal] [User ▼]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Sidebar:                      │  Content:                              │
│  ┌──────────────────────┐      │  ┌────────────────────────────────┐   │
│  │ 🏠 Dashboard         │      │  │ MANTRA DASHBOARD               │   │
│  │ 📝 Decisions         │      │  │                                │   │
│  │ ✅ Validator         │      │  │ Recent Decisions:              │   │
│  │ 🔍 Search            │      │  │ - DEC-001: API Versioning      │   │
│  │ 📊 Governance        │      │  │ - DEC-002: Auth Method         │   │
│  │ 🤖 AI Assistant      │      │  │                                │   │
│  │ 📡 MCP Dashboard     │      │  │ [Quick Actions]                │   │
│  │                      │      │  │ - Create Decision              │   │
│  │ (NO tenant menus)    │      │  │ - Validate Text                │   │
│  │ (NO billing menus)   │      │  │ - Search Decisions             │   │
│  └──────────────────────┘      │  └────────────────────────────────┘   │
│                                                                          │
│  Header shows: Current Org, Current Project, Back to Portal link        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Features:
- Domain-specific features only
- No tenant/billing management (handled in Portal)
- Header shows current context
- "Back to Portal" for tenant management
```

---

## Product Integration Flow

### How App Creators Use PUGUH

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       APP CREATOR WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Step 1: Register Product                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ puguh products register                                          │    │
│  │   --name "MANTRA"                                                │    │
│  │   --slug "mantra"                                                │    │
│  │   --redirect-uri "https://mantra.app/callback"                   │    │
│  │   --webhook-url "https://mantra.app/webhooks/puguh"              │    │
│  │                                                                  │    │
│  │ Response:                                                        │    │
│  │   product_id: prod_xxxx                                          │    │
│  │   client_id: cli_xxxx                                            │    │
│  │   client_secret: sec_xxxx                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Step 2: Integrate SDK                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ # Backend middleware                                             │    │
│  │ from puguh_sdk import PuguhClient                                │    │
│  │                                                                  │    │
│  │ puguh = PuguhClient(                                             │    │
│  │     base_url="https://api.puguh.io",                            │    │
│  │     client_id="cli_xxxx",                                        │    │
│  │     client_secret="sec_xxxx"                                     │    │
│  │ )                                                                │    │
│  │                                                                  │    │
│  │ @app.middleware("http")                                          │    │
│  │ async def validate_auth(request, call_next):                     │    │
│  │     token = request.headers.get("Authorization")                 │    │
│  │     user = await puguh.auth.validate_token(token)                │    │
│  │     request.state.user = user                                    │    │
│  │     return await call_next(request)                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Step 3: Define Subscription Plans                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ puguh products plans create                                      │    │
│  │   --product "mantra"                                             │    │
│  │   --name "Pro"                                                   │    │
│  │   --price 29                                                     │    │
│  │   --interval monthly                                             │    │
│  │   --features '{"decisions_limit": 10000, "ai_enabled": true}'    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Step 4: Handle Webhooks                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ @app.post("/webhooks/puguh")                                     │    │
│  │ async def handle_webhook(event: PuguhEvent):                     │    │
│  │     match event.type:                                            │    │
│  │         case "subscription.created":                             │    │
│  │             await setup_tenant(event.data.tenant_id)             │    │
│  │         case "subscription.cancelled":                           │    │
│  │             await cleanup_tenant(event.data.tenant_id)           │    │
│  │         case "member.added":                                     │    │
│  │             await sync_member(event.data)                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │  PUGUH   │     │  MANTRA  │     │  MANTRA  │
│ Browser  │     │  Portal  │     │ Frontend │     │ Backend  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │  1. Access MANTRA              │                │
     │────────────────────────────────>                │
     │                │                │                │
     │  2. No token, redirect to Portal               │
     │<───────────────────────────────┤                │
     │                │                │                │
     │  3. Login at Portal            │                │
     │───────────────>│                │                │
     │                │                │                │
     │  4. JWT + redirect to MANTRA   │                │
     │<───────────────│                │                │
     │                │                │                │
     │  5. Access MANTRA with token   │                │
     │────────────────────────────────>                │
     │                │                │                │
     │                │  6. API call with token        │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │  7. Validate   │
     │                │                │     token      │
     │                │<───────────────────────────────│
     │                │                │                │
     │                │  8. User context               │
     │                │───────────────────────────────>│
     │                │                │                │
     │                │                │  9. Response   │
     │                │                │<───────────────│
     │                │                │                │
     │  10. MANTRA page with data     │                │
     │<───────────────────────────────┤                │
     │                │                │                │
```

### Tenant Context Flow

```
JWT Token includes:
{
  "user_id": "user_uuid",
  "tenant_id": "tenant_uuid",      // Current org context
  "project_id": "project_uuid",    // Current project (optional)
  "roles": ["member", "mantra:editor"]
}

Product Backend uses tenant_id for:
- Data isolation (WHERE tenant_id = ?)
- Permission checks (does user have access?)
- Usage tracking (count towards subscription limits)
```

---

## No Vendor Lock-in Design

### Abstraction Layer

Products should use ports/adapters pattern:

```python
# Your product's identity port (abstract interface)
class IdentityPort(Protocol):
    async def validate_token(self, token: str) -> UserContext: ...
    async def get_tenant(self, tenant_id: str) -> Tenant: ...

# PUGUH adapter (default)
class PuguhIdentityAdapter(IdentityPort):
    def __init__(self, puguh_client: PuguhClient):
        self.client = puguh_client

    async def validate_token(self, token: str) -> UserContext:
        return await self.client.auth.validate_token(token)

# Alternative adapter (self-hosted)
class KeycloakIdentityAdapter(IdentityPort):
    def __init__(self, keycloak_client):
        self.client = keycloak_client

    async def validate_token(self, token: str) -> UserContext:
        # Keycloak-specific validation
        ...

# Usage in your app
identity = PuguhIdentityAdapter(puguh_client)  # or KeycloakIdentityAdapter
user = await identity.validate_token(token)
```

### Data Portability

- All tenant data exportable via API
- Standard formats (JSON, CSV)
- No proprietary data structures
- Clear ownership (tenant owns their data)

---

## Subscription Model

### Platform Subscription (PUGUH base)

Every subscriber starts with PUGUH base:
- Identity management (users, auth)
- Tenant management (orgs, members)
- Basic billing

### Product Subscriptions (Add-ons)

Products are subscribed per-tenant:

```
Tenant "My Company":
├── PUGUH Base: Active (included)
├── MANTRA: Pro Plan ($29/mo)
├── Product B: Not subscribed
└── Product C: Trial (14 days left)
```

### Pricing Options

1. **Per-product pricing**: Each product has its own plans
2. **Bundle pricing**: Discounted bundle of multiple products
3. **Usage-based**: Pay per API call, decision, etc.

---

## Security Model

### Token Security

- Short-lived access tokens (1 hour)
- Long-lived refresh tokens (30 days)
- Token rotation on refresh
- Blacklist for logout

### Tenant Isolation

- All data queries include tenant_id
- Cross-tenant access blocked at SDK level
- Audit log for sensitive operations

### Permission Model

```
Permission format: {product}:{resource}:{action}

Examples:
- mantra:decisions:create
- mantra:decisions:read
- mantra:validator:use
- product_b:reports:export
```

---

## Summary

| Component | Responsibility |
|-----------|----------------|
| **PUGUH Portal** | Central UI for identity, tenant, billing management |
| **PUGUH API** | Backend services for auth, tenant, billing |
| **PUGUH SDK** | Client libraries for product integration |
| **Product Apps** | Domain-specific features only, uses SDK |

**Key Principles:**
1. Products don't implement auth/tenant/billing
2. All users managed centrally in PUGUH
3. Products receive user context via JWT
4. Tenant isolation enforced by SDK
5. No vendor lock-in via adapter pattern
