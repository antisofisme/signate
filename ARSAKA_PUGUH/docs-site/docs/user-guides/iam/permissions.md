---
sidebar_position: 3
---

# Permissions Reference

Complete reference for all permissions in ATLAS PUGUH.

## Permission Format

All permissions follow this pattern:

```
{domain}.{resource}.{action}
```

## IAM Domain

| Permission | Description |
|------------|-------------|
| `iam.users.view` | View user list and details |
| `iam.users.invite` | Invite new users to tenant |
| `iam.users.update` | Update user details |
| `iam.users.suspend` | Suspend/activate users |
| `iam.users.remove` | Remove users from tenant |
| `iam.roles.view` | View roles and permissions |
| `iam.roles.create` | Create custom roles |
| `iam.roles.update` | Modify role permissions |
| `iam.roles.delete` | Delete custom roles |
| `iam.service-accounts.view` | View service accounts |
| `iam.service-accounts.create` | Create service accounts |
| `iam.service-accounts.delete` | Delete service accounts |
| `iam.service-accounts.rotate` | Rotate API keys |

## Tenant Domain

| Permission | Description |
|------------|-------------|
| `tenant.settings.view` | View tenant settings |
| `tenant.settings.update` | Update tenant settings |
| `tenant.members.view` | View member list |
| `tenant.members.manage` | Add/remove members |
| `tenant.projects.view` | View projects |
| `tenant.projects.create` | Create new projects |
| `tenant.projects.update` | Update project settings |
| `tenant.projects.delete` | Delete projects |
| `tenant.delete` | Delete the entire tenant |

## Decision Domain

| Permission | Description |
|------------|-------------|
| `decision.rules.view` | View rules and details |
| `decision.rules.create` | Create new rules |
| `decision.rules.update` | Edit existing rules |
| `decision.rules.delete` | Delete rules |
| `decision.rules.activate` | Activate/deactivate rules |
| `decision.rules.test` | Test rules with sample data |
| `decision.types.view` | View decision types |
| `decision.types.create` | Create decision types |
| `decision.types.update` | Update decision types |
| `decision.types.delete` | Delete decision types |
| `decision.history.view` | View decision history |
| `decision.history.export` | Export decision history |

## Workflow Domain

| Permission | Description |
|------------|-------------|
| `workflow.workflows.view` | View workflows |
| `workflow.workflows.create` | Create workflows |
| `workflow.workflows.approve` | Approve pending workflows |
| `workflow.workflows.reject` | Reject pending workflows |
| `workflow.workflows.delegate` | Delegate to another user |
| `workflow.workflows.escalate` | Escalate to higher authority |
| `workflow.templates.view` | View workflow templates |
| `workflow.templates.create` | Create templates |
| `workflow.templates.update` | Update templates |
| `workflow.templates.delete` | Delete templates |

## Control Domain

| Permission | Description |
|------------|-------------|
| `control.audit.view` | View audit trails |
| `control.audit.export` | Export audit logs |
| `control.events.view` | View event timeline |
| `control.events.detail` | View event details |
| `control.metrics.view` | View system metrics |
| `control.dlq.view` | View dead letter queue |
| `control.dlq.retry` | Retry failed events |
| `control.dlq.dismiss` | Dismiss DLQ items |

## Billing Domain

| Permission | Description |
|------------|-------------|
| `billing.subscription.view` | View current subscription |
| `billing.subscription.update` | Change subscription plan |
| `billing.invoices.view` | View invoice history |
| `billing.invoices.download` | Download invoices |
| `billing.payment-methods.view` | View payment methods |
| `billing.payment-methods.update` | Update payment methods |

## Role Permission Mapping

### Owner (All Permissions)

Has all permissions in all domains.

### Admin

```
iam.users.*
iam.roles.*
iam.service-accounts.*
tenant.settings.*
tenant.members.*
tenant.projects.*
decision.*
workflow.*
control.*
```

Excludes:
- `tenant.delete`
- `billing.*`

### Member

```
iam.users.view
iam.roles.view
iam.service-accounts.view
tenant.settings.view
tenant.members.view
tenant.projects.view
decision.rules.view
decision.rules.create
decision.rules.update
decision.rules.test
decision.types.view
decision.history.view
workflow.workflows.*
control.audit.view
control.events.view
control.metrics.view
```

### Viewer

```
iam.users.view
iam.roles.view
tenant.settings.view
tenant.members.view
tenant.projects.view
decision.rules.view
decision.types.view
decision.history.view
workflow.workflows.view
control.audit.view
control.events.view
control.metrics.view
```

## Checking Permissions

### In the Dashboard

Navigate to **IAM > Permissions** to see:
- Your effective permissions
- Comparison across roles
- Missing permissions for specific actions

### Via API

```typescript
// Check single permission
const result = await client.checkPermission('decision.rules.create');
// { allowed: true }

// Check multiple permissions
const results = await client.checkPermissions([
  'decision.rules.create',
  'decision.rules.delete',
  'workflow.workflows.approve'
]);
// {
//   'decision.rules.create': true,
//   'decision.rules.delete': false,
//   'workflow.workflows.approve': true
// }

// Get all permissions
const allPermissions = await client.getMyPermissions();
// ['decision.rules.view', 'decision.rules.create', ...]
```

## Permission Errors

When a permission check fails, you'll see:

**Dashboard:**
> "You don't have permission to perform this action."

**API:**
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Missing permission: decision.rules.delete",
    "required_permission": "decision.rules.delete"
  }
}
```

## Related

- [Roles](/docs/user-guides/iam/roles)
- [Access Control](/docs/user-guides/iam/access-control)
- [API Authentication](/docs/api-reference/authentication)
