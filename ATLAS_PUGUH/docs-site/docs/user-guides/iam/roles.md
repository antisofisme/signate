---
sidebar_position: 2
---

# Roles & Permissions

Understand how roles and permissions work in ATLAS PUGUH.

## Role-Based Access Control (RBAC)

PUGUH uses RBAC to manage what users can do. Each user has exactly one role per tenant, and roles define their permissions.

## Built-in Roles

### Owner
The highest level of access. Each tenant has exactly one owner.

**Capabilities:**
- All permissions
- Billing and subscription management
- Delete tenant
- Transfer ownership

### Admin
Full management access without billing.

**Capabilities:**
- Create, edit, delete all resources
- Manage users and roles
- Configure tenant settings
- Cannot access billing
- Cannot delete tenant

### Member
Standard user for day-to-day work.

**Capabilities:**
- Create and edit rules, workflows
- View all resources
- Cannot delete resources
- Cannot manage users

### Viewer
Read-only access for observers.

**Capabilities:**
- View all resources
- Cannot make any changes
- Cannot approve workflows

## Permission System

Permissions follow the format:
```
{domain}.{resource}.{action}
```

### Examples

| Permission | Meaning |
|------------|---------|
| `decision.rules.create` | Create new rules |
| `decision.rules.delete` | Delete rules |
| `workflow.workflows.approve` | Approve workflows |
| `iam.users.invite` | Invite new users |
| `tenant.settings.update` | Update tenant settings |

### Domain List

| Domain | Resources |
|--------|-----------|
| `iam` | users, roles, permissions |
| `tenant` | settings, members, projects |
| `decision` | rules, types, history |
| `workflow` | workflows, escalations |
| `control` | audit, events, metrics |
| `billing` | subscription, invoices |

## Permission Matrix

Navigate to **IAM > Permissions** to see the full permission matrix.

The matrix shows:
- All available permissions
- Which roles have which permissions
- Effective permissions for each user

## Custom Roles (Pro/Enterprise)

Pro and Enterprise plans can create custom roles with specific permissions.

### Creating a Custom Role

1. Go to **IAM > Roles**
2. Click **"Create Role"**
3. Enter role name and description
4. Select permissions to include
5. Click **"Create"**

### Custom Role Examples

**Approver Role**
- `workflow.workflows.view`
- `workflow.workflows.approve`
- `workflow.workflows.reject`

**Rule Manager Role**
- `decision.rules.view`
- `decision.rules.create`
- `decision.rules.edit`
- `decision.rules.delete`

**Auditor Role**
- `control.audit.view`
- `control.events.view`
- `control.metrics.view`

## Role Inheritance

PUGUH uses a flat role model - roles don't inherit from each other. Each role explicitly defines its permissions.

This means:
- No hidden permissions from parent roles
- Easy to understand what each role can do
- No complex inheritance chains

## API Permission Checks

When making API calls, permissions are checked:

```typescript
// This will fail if user lacks decision.rules.create
const response = await client.createRule({
  name: 'My Rule',
  // ...
});

// Error response if lacking permission:
// { "error": "PERMISSION_DENIED", "message": "Missing permission: decision.rules.create" }
```

## Checking Permissions in Code

```typescript
import { PuguhClient } from '@atlashub/puguh-sdk';

// Check if user has a specific permission
const canCreate = await client.hasPermission('decision.rules.create');
if (canCreate) {
  // Show create button
}

// Get all user permissions
const permissions = await client.getPermissions();
console.log(permissions);
// ['decision.rules.view', 'decision.rules.create', ...]
```

## Best Practices

1. **Start Restricted**: Use Viewer role by default, upgrade as needed
2. **Review Regularly**: Audit who has what access quarterly
3. **Document Custom Roles**: Keep notes on why custom roles were created
4. **Use Service Accounts**: Don't give API keys to Admin users
5. **Separate Concerns**: Different roles for different responsibilities

## Troubleshooting

### "Permission Denied" Errors

If a user sees permission errors:

1. Check their role in **IAM > Users**
2. Verify the role has the required permission in **IAM > Roles**
3. Ensure they're in the correct tenant
4. Check if they're suspended

### Cannot Change Owner

Ownership transfer requires:
1. Current owner initiates transfer
2. New owner accepts
3. New owner must be an Admin

## Related

- [User Management](/docs/user-guides/iam/users)
- [Access Control](/docs/user-guides/iam/access-control)
- [API Authentication](/docs/api-reference/authentication)
