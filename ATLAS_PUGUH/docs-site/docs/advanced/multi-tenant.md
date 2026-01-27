---
sidebar_position: 1
---

# Multi-Tenant Architecture

Understanding multi-tenancy in ATLAS PUGUH.

## Overview

PUGUH uses a multi-tenant architecture where each tenant (organization) has completely isolated data and configuration. This enables:

- **Data Isolation**: Complete separation between tenants
- **Configuration Independence**: Each tenant has its own rules and workflows
- **Resource Management**: Per-tenant billing and limits
- **Security**: No cross-tenant data leakage

## Tenant Hierarchy

```
Tenant (Organization)
├── Users (via Memberships)
│   ├── Owner (1 per tenant)
│   ├── Admins
│   ├── Members
│   └── Viewers
│
├── Projects
│   ├── Production
│   ├── Staging
│   └── Development
│
├── Rules
│   ├── Tenant-level (shared)
│   └── Project-level (isolated)
│
├── Workflows
│   └── Project-scoped
│
├── Decisions
│   └── Project-scoped
│
└── Subscription
    └── Plan + Billing
```

## Data Isolation

### Database Level

Every table includes `tenant_id`:

```sql
CREATE TABLE rules (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,  -- Tenant isolation
  project_id UUID,          -- Optional project scope
  name TEXT,
  ...
);

-- Row-Level Security (RLS) enforces isolation
CREATE POLICY tenant_isolation ON rules
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### API Level

All API requests are scoped to a tenant:

```http
GET /api/v1/rules
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

The token contains tenant membership information, and all queries are automatically filtered.

### Application Level

```typescript
// SDK automatically includes tenant context
const client = new PuguhClient({
  tenantId: 'your-tenant-id',
  // ...
});

// All operations scoped to this tenant
const rules = await client.listRules(); // Only returns tenant's rules
```

## Tenant Membership

### User-Tenant Relationship

Users can belong to multiple tenants:

```
User: alice@example.com
├── Tenant: Acme Corp (Owner)
├── Tenant: Consulting Co (Admin)
└── Tenant: Partner Inc (Member)
```

### Membership Model

```typescript
interface TenantMembership {
  userId: string;
  tenantId: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  status: 'active' | 'invited' | 'suspended';
  joinedAt: Date;
}
```

### Switching Tenants

```typescript
// List user's tenants
const tenants = await client.listMyTenants();

// Switch active tenant
await client.setActiveTenant(tenantId);
```

## Project Scoping

Projects provide an additional isolation layer within tenants.

### When to Use Projects

| Use Case | Recommendation |
|----------|----------------|
| Multiple environments | Separate projects (prod/staging/dev) |
| Different applications | Separate projects per app |
| Team isolation | Separate projects per team |
| Testing | Dedicated test project |

### Rule Scoping

Rules can be:

1. **Tenant-level**: Shared across all projects
2. **Project-level**: Isolated to one project

```typescript
// Tenant-level rule
await client.createRule({
  name: 'Company Policy',
  scope: 'tenant',
  // ...
});

// Project-level rule
await client.createRule({
  name: 'Production Rule',
  scope: 'project',
  projectId: 'prod-project-id',
  // ...
});
```

### Rule Priority

When evaluating decisions:
1. Project-level rules evaluated first
2. Tenant-level rules evaluated if no project match
3. Highest priority rule wins

## Tenant Limits

Each plan has tenant-level limits:

| Limit | Free | Starter | Pro | Enterprise |
|-------|------|---------|-----|------------|
| Projects | 1 | 5 | Unlimited | Unlimited |
| Users | 3 | 10 | Unlimited | Unlimited |
| Decisions/month | 1,000 | 10,000 | 100,000 | Unlimited |
| Rules | 10 | 50 | 500 | Unlimited |

### Checking Limits

```typescript
const usage = await client.getTenantUsage();

console.log(usage.decisions.used);  // 5432
console.log(usage.decisions.limit); // 10000
console.log(usage.decisions.remaining); // 4568
```

### Limit Enforcement

When limits are exceeded:
- **Decisions**: API returns 429 with upgrade prompt
- **Projects**: Cannot create new projects
- **Users**: Cannot invite new members

## Cross-Tenant Operations

Cross-tenant operations are **not allowed** by design:

- Users cannot access other tenants' data
- API keys are tenant-scoped
- No cross-tenant queries possible

### Shared Resources (Enterprise)

Enterprise customers can set up controlled sharing:

1. **Service Tenants**: Shared services across tenants
2. **Federation**: Connect multiple tenants
3. **Data Sync**: Controlled replication

Contact support for enterprise features.

## Security Considerations

### Tenant Isolation Guarantees

1. **Query Isolation**: All queries filtered by tenant_id
2. **Index Separation**: Tenant-scoped indexes
3. **Encryption**: Per-tenant encryption keys (Enterprise)
4. **Audit Isolation**: Tenant-specific audit logs

### Security Best Practices

1. **Use Project Separation**: Separate sensitive data in projects
2. **Regular Access Review**: Audit tenant memberships
3. **Minimal Permissions**: Use least privilege principle
4. **Monitor Cross-Tenant**: Watch for anomalies

## Migration Between Tenants

### Moving Resources

Resources cannot be moved between tenants directly. To migrate:

1. Export from source tenant
2. Import to destination tenant
3. Verify and validate
4. Delete from source

### Export/Import

```bash
# Export rules
puguh-cli export rules --tenant SOURCE_TENANT --output rules.json

# Import to new tenant
puguh-cli import rules --tenant DEST_TENANT --input rules.json
```

## Troubleshooting

### "Tenant not found"

- Verify tenant ID is correct
- Check user has access to tenant
- Ensure tenant is not suspended

### "Cross-tenant access denied"

- Cannot access resources from another tenant
- Switch to correct tenant first
- Verify membership status

### "Limit exceeded"

- Check current usage vs limits
- Upgrade plan or reduce usage
- Contact support for temporary increase

## Related

- [Project Scoping](/docs/advanced/scoping)
- [Best Practices](/docs/advanced/best-practices)
- [Troubleshooting](/docs/advanced/troubleshooting)
