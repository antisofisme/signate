---
sidebar_position: 3
---

# Monitoring Workflows

Learn how to monitor and manage active workflows.

## Workflow Dashboard

Navigate to **Workflow > Dashboard** for an overview:

### Key Metrics

| Metric | Description |
|--------|-------------|
| **Pending** | Workflows awaiting action |
| **Approved (24h)** | Completed approvals today |
| **Rejected (24h)** | Rejected workflows today |
| **Avg. Time** | Average time to completion |

### Charts

- Workflow volume over time
- Approval rate trends
- Stage bottleneck analysis
- SLA compliance

## My Pending

View workflows waiting for YOUR action:

1. Go to **Workflow > My Pending**
2. See list of workflows assigned to you
3. Quick actions: Approve, Reject, Delegate

### Sorting and Filtering

| Filter | Options |
|--------|---------|
| Priority | High, Medium, Low |
| Age | Newest, Oldest |
| Type | By workflow template |
| Due Soon | Approaching timeout |

## All Workflows

View all workflows (admins):

1. Go to **Workflow > All Workflows**
2. Filter by status, type, user
3. Export to CSV

### Status Filters

| Status | Description |
|--------|-------------|
| `PENDING` | Awaiting approval |
| `APPROVED` | Completed successfully |
| `REJECTED` | Declined |
| `ESCALATED` | Moved to higher authority |
| `DELEGATED` | Reassigned |
| `TIMED_OUT` | Exceeded timeout |
| `CANCELLED` | Manually cancelled |

## Workflow Detail View

Click any workflow to see details:

### Overview Tab

```
Workflow ID: wf-12345
Template: Purchase Approval
Status: PENDING
Created: 2025-01-20 10:30 AM
Current Stage: Finance Review

Context:
- Amount: $15,000
- Category: Equipment
- Requester: john@company.com
```

### Timeline Tab

Visual history of all actions:

```
┌───────────────────────────────────────────┐
│ Jan 20, 10:30 AM                          │
│ Workflow created by rule: high-value-rule │
├───────────────────────────────────────────┤
│ Jan 20, 10:31 AM                          │
│ Assigned to: jane@company.com (Manager)   │
├───────────────────────────────────────────┤
│ Jan 20, 2:15 PM                           │
│ Approved by: jane@company.com             │
│ Comment: "Looks good, proceed"            │
├───────────────────────────────────────────┤
│ Jan 20, 2:15 PM                           │
│ Moved to Stage: Finance Review            │
│ Assigned to: finance-team                 │
└───────────────────────────────────────────┘
```

### Comments Tab

Discussion thread for the workflow:
- Add comments
- @mention users
- Attach files (Enterprise)

### Audit Tab

Detailed audit log:
- Every state change
- Who took action
- Timestamps
- IP addresses

## Taking Action

### Approve

1. Click **"Approve"** button
2. Add optional comment
3. Confirm

### Reject

1. Click **"Reject"** button
2. Add required reason
3. Confirm

### Delegate

Reassign to another user:
1. Click **"Delegate"**
2. Select user
3. Add reason
4. Confirm

### Escalate

Move to higher authority:
1. Click **"Escalate"**
2. Select escalation path
3. Add reason
4. Confirm

## Bulk Actions

Process multiple workflows at once:

1. Select workflows using checkboxes
2. Click **"Bulk Action"** dropdown
3. Choose action:
   - Approve all
   - Reject all
   - Reassign all
4. Confirm

:::caution
Bulk actions are logged and cannot be undone. Use carefully.
:::

## Notifications

### Email Notifications

Receive emails for:
- New workflows assigned
- Approaching timeout
- Workflow completed
- Comments/mentions

Configure in **Settings > Notifications**.

### In-App Notifications

Bell icon shows:
- Unread notifications
- Recent activity
- Quick actions

### Slack Integration (Pro+)

Post workflow updates to Slack:
1. Go to **Settings > Integrations**
2. Connect Slack
3. Configure channel
4. Choose notification types

## SLA Monitoring

Track approval times against targets:

### Setting SLAs

Per workflow template:
```json
{
  "sla": {
    "warning_threshold": "4h",
    "critical_threshold": "8h",
    "escalation_threshold": "24h"
  }
}
```

### SLA Dashboard

View SLA compliance:
- % meeting SLA
- Average delay
- Problem areas

### SLA Alerts

Automatic alerts when:
- Approaching warning threshold
- Hit critical threshold
- SLA breached

## Reports

### Standard Reports

| Report | Description |
|--------|-------------|
| Volume | Workflow count over time |
| Cycle Time | Time from creation to completion |
| Bottleneck | Stages with longest wait times |
| User Activity | Actions per user |

### Custom Reports (Pro+)

Build custom reports:
1. Go to **Workflow > Reports**
2. Click **"New Report"**
3. Select metrics
4. Configure filters
5. Schedule (optional)

### Exporting Data

Export workflow data:
- CSV for spreadsheets
- JSON for integrations
- PDF for documentation

## Troubleshooting

### Workflow Stuck

1. Check current stage
2. Verify assignee exists and is active
3. Check for timeout configuration
4. Review escalation path

### Missing Notifications

1. Check notification settings
2. Verify email is correct
3. Check spam folder
4. Review notification logs

### Unexpected Rejection

1. Review workflow timeline
2. Check who took action
3. Read rejection reason
4. Review audit log

## API Monitoring

### List Pending Workflows

```typescript
const pending = await client.listWorkflows({
  status: 'PENDING',
  assigned_to: 'me',
  limit: 20
});
```

### Subscribe to Updates

```typescript
client.subscribeToWorkflow('wf-123', (event) => {
  console.log('Workflow updated:', event);
});
```

### Get Metrics

```typescript
const metrics = await client.getWorkflowMetrics({
  period: '7d',
  group_by: 'template'
});
```

## Related

- [Creating Workflows](/docs/user-guides/workflows/creating)
- [Workflow Triggers](/docs/user-guides/workflows/triggers)
- [Audit Trail](/docs/user-guides/control/environments)
