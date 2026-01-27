---
sidebar_position: 1
---

# Audit Trail

Learn how to use the audit trail for compliance and troubleshooting.

## What is the Audit Trail?

The audit trail is a comprehensive log of all significant actions in your PUGUH tenant. It provides:

- **Accountability**: Who did what and when
- **Compliance**: Evidence for regulatory requirements
- **Troubleshooting**: Debug issues by reviewing history
- **Security**: Detect unauthorized actions

## Accessing the Audit Trail

Navigate to **Control > Audit Trail** to view the log.

## Audit Entry Structure

Each entry contains:

```json
{
  "audit_id": "uuid",
  "timestamp": "2025-01-20T10:30:00.123Z",
  "actor": {
    "user_id": "uuid",
    "email": "jane@company.com",
    "type": "user"
  },
  "action": "rule.created",
  "resource": {
    "type": "rule",
    "id": "rule-123",
    "name": "High Value Approval"
  },
  "tenant_id": "uuid",
  "project_id": "uuid",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "conditions": {...},
    "actions": {...}
  },
  "result": "success"
}
```

## Action Types

### Authentication Actions

| Action | Description |
|--------|-------------|
| `auth.login` | User logged in |
| `auth.logout` | User logged out |
| `auth.failed` | Failed login attempt |
| `auth.password_reset` | Password was reset |
| `auth.mfa_enabled` | MFA was enabled |

### User Management

| Action | Description |
|--------|-------------|
| `user.invited` | User was invited |
| `user.joined` | User accepted invite |
| `user.suspended` | User was suspended |
| `user.removed` | User was removed |
| `user.role_changed` | Role was changed |

### Rule Actions

| Action | Description |
|--------|-------------|
| `rule.created` | Rule was created |
| `rule.updated` | Rule was modified |
| `rule.activated` | Rule went live |
| `rule.deprecated` | Rule was deprecated |
| `rule.deleted` | Rule was deleted |

### Workflow Actions

| Action | Description |
|--------|-------------|
| `workflow.created` | Workflow started |
| `workflow.approved` | Workflow approved |
| `workflow.rejected` | Workflow rejected |
| `workflow.delegated` | Workflow delegated |
| `workflow.escalated` | Workflow escalated |

### Decision Actions

| Action | Description |
|--------|-------------|
| `decision.evaluated` | Decision was made |
| `decision.allowed` | Decision allowed |
| `decision.denied` | Decision denied |
| `decision.flagged` | Decision flagged |

### Tenant Actions

| Action | Description |
|--------|-------------|
| `tenant.settings_updated` | Settings changed |
| `tenant.plan_changed` | Subscription changed |
| `tenant.project_created` | Project created |

## Filtering the Audit Trail

### By Date Range

Select start and end dates to filter:
- Last 24 hours
- Last 7 days
- Last 30 days
- Custom range

### By Actor

Filter by who performed the action:
- Specific user
- Service account
- System (automated)

### By Action Type

Filter by category:
- Authentication
- User management
- Rules
- Workflows
- Decisions

### By Resource

Find actions on specific resources:
- Specific rule
- Specific workflow
- Specific user

### By Result

Filter by outcome:
- Success
- Failure
- Partial

## Searching

Use the search bar for text search across:
- User emails
- Resource names
- Action details

Example searches:
- `jane@company.com` - All actions by Jane
- `rule.activated` - All rule activations
- `failed` - All failed actions

## Exporting Audit Logs

### Export Options

| Format | Use Case |
|--------|----------|
| CSV | Spreadsheet analysis |
| JSON | Integration/API |
| PDF | Compliance reports |

### Export Process

1. Apply desired filters
2. Click **"Export"**
3. Select format
4. Choose fields to include
5. Download file

### Scheduled Exports

Pro+ plans can schedule automatic exports:
1. Go to **Settings > Scheduled Exports**
2. Configure schedule (daily/weekly/monthly)
3. Choose destination (email/S3/SFTP)

## Retention Policies

| Plan | Retention Period |
|------|------------------|
| Free | 7 days |
| Starter | 30 days |
| Pro | 1 year |
| Enterprise | Custom (unlimited) |

Older entries are archived but can be retrieved on request (Enterprise).

## Compliance Features

### Immutability

Audit logs cannot be modified or deleted:
- Entries are append-only
- No edit or delete capabilities
- Cryptographic verification available (Enterprise)

### Chain of Custody

Enterprise plans provide:
- Tamper-evident logging
- Cryptographic signatures
- Third-party attestation

### Compliance Reports

Generate reports for:
- SOC 2 audits
- ISO 27001
- GDPR data access logs
- Custom frameworks

## API Access

### Query Audit Trail

```typescript
const entries = await client.queryAuditTrail({
  start_date: '2025-01-01',
  end_date: '2025-01-31',
  actions: ['rule.created', 'rule.updated'],
  limit: 100
});
```

### Stream Audit Events

```typescript
client.streamAuditEvents({
  filter: { actions: ['auth.failed'] }
}, (event) => {
  console.log('Security event:', event);
});
```

## Security Monitoring

### Suspicious Activity Detection

Watch for:
- Multiple failed logins
- Unusual access patterns
- Off-hours activity
- Bulk deletions

### Setting Up Alerts

1. Go to **Control > Alerts**
2. Click **"New Alert"**
3. Configure trigger conditions
4. Set notification method
5. Activate alert

### Example Alerts

```yaml
alert: Failed Login Spike
trigger:
  action: auth.failed
  count: > 5
  window: 5m
notification:
  email: security@company.com
  slack: #security-alerts
```

## Best Practices

### 1. Regular Review
Schedule weekly audit log reviews.

### 2. Set Up Alerts
Configure alerts for critical actions.

### 3. Export for Compliance
Maintain offline copies for compliance.

### 4. Correlate with Other Systems
Cross-reference with other security logs.

### 5. Document Access
Track who reviews audit logs and when.

## Troubleshooting with Audit Trail

### Finding Rule Changes

"Why did this rule stop working?"
1. Filter by rule resource
2. Look for `rule.updated` actions
3. Compare before/after

### Tracing Decision Flow

"Why was this decision denied?"
1. Find the `decision.denied` entry
2. Check which rule matched
3. Review rule conditions

### Identifying Access Issues

"Why can't user X access resource Y?"
1. Filter by user
2. Look for `auth.failed` or permission errors
3. Check role changes

## Related

- [Event Timeline](/docs/user-guides/control/deployment)
- [Metrics Dashboard](/docs/user-guides/control/rollback)
- [Security Best Practices](/docs/advanced/best-practices)
