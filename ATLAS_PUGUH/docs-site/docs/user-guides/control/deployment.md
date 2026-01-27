---
sidebar_position: 2
---

# Event Timeline

Monitor real-time events and system activity.

## What is the Event Timeline?

The Event Timeline shows real-time events flowing through your PUGUH system. Unlike the audit trail (which focuses on user actions), the event timeline shows system-level events.

## Accessing the Timeline

Navigate to **Control > Events** to view the timeline.

## Event Types

### Decision Events

| Event | Description |
|-------|-------------|
| `decision.requested` | Decision request received |
| `decision.evaluated` | Rules evaluated |
| `decision.completed` | Decision returned to caller |
| `decision.timeout` | Evaluation timed out |

### Rule Events

| Event | Description |
|-------|-------------|
| `rule.matched` | Rule conditions matched |
| `rule.skipped` | Rule was skipped |
| `rule.error` | Rule evaluation error |

### Workflow Events

| Event | Description |
|-------|-------------|
| `workflow.started` | Workflow created |
| `workflow.stage_entered` | Moved to new stage |
| `workflow.action_taken` | Approve/reject/etc |
| `workflow.completed` | Workflow finished |

### System Events

| Event | Description |
|-------|-------------|
| `system.health_check` | Health check performed |
| `system.config_reload` | Configuration reloaded |
| `system.cache_cleared` | Cache was cleared |

## Timeline View

### Live Mode

Watch events in real-time:
```
[LIVE] ● Connected

10:30:15.123 | decision.requested  | expense_approval | req-abc123
10:30:15.125 | rule.matched        | high-value-rule  | req-abc123
10:30:15.130 | decision.completed  | REQUIRE_APPROVAL | req-abc123
10:30:15.135 | workflow.started    | purchase-flow    | wf-xyz789
```

### Historical Mode

Browse past events:
1. Disable live mode
2. Select date/time range
3. Navigate through events

## Filtering Events

### By Event Type

Check/uncheck event categories:
- [ ] Decision events
- [x] Rule events
- [x] Workflow events
- [ ] System events

### By Time Window

Select time range:
- Last 5 minutes
- Last 15 minutes
- Last hour
- Last 24 hours
- Custom range

### By Resource

Filter to specific resources:
- Decision type
- Rule ID
- Workflow ID

### By Severity

Filter by severity level:
- Info
- Warning
- Error
- Critical

## Event Details

Click any event to see details:

```json
{
  "event_id": "evt-123456",
  "type": "decision.completed",
  "timestamp": "2025-01-20T10:30:15.130Z",
  "tenant_id": "uuid",
  "project_id": "uuid",
  "correlation_id": "req-abc123",
  "payload": {
    "decision_type": "expense_approval",
    "outcome": "REQUIRE_APPROVAL",
    "matched_rule": "high-value-rule",
    "evaluation_time_ms": 5,
    "context": {
      "amount": 15000
    }
  }
}
```

## Correlation IDs

Track related events using correlation IDs:

1. Click an event
2. Click **"Show Related"**
3. See all events with same correlation ID

Example flow:
```
[req-abc123] decision.requested   → Rules started
[req-abc123] rule.matched         → High-value rule matched
[req-abc123] decision.completed   → Returns REQUIRE_APPROVAL
[req-abc123] workflow.started     → Workflow created
[wf-xyz789] workflow.started      → New correlation begins
```

## Performance Monitoring

### Latency Distribution

View decision latency:
```
< 10ms:  ████████████████████ 80%
10-50ms: █████ 15%
50-100ms: █ 4%
> 100ms: ░ 1%
```

### Throughput

Events per second/minute:
```
Peak: 150 events/second
Average: 45 events/second
Current: 52 events/second
```

### Error Rate

Track error events:
```
Error rate: 0.1%
Last error: 2 hours ago
Most common: rule.error (timeout)
```

## Alerts from Events

Set up alerts based on event patterns:

### Error Spike Alert

```yaml
alert: Decision Error Spike
trigger:
  event: decision.timeout
  count: > 10
  window: 5m
action:
  email: ops@company.com
  slack: #alerts
```

### Latency Alert

```yaml
alert: High Latency
trigger:
  event: decision.completed
  condition: payload.evaluation_time_ms > 100
  count: > 5
  window: 1m
action:
  pagerduty: high
```

## Dead Letter Queue (DLQ)

Failed events go to the DLQ:

### Viewing DLQ

Navigate to **Control > DLQ**

### DLQ Entry

```json
{
  "dlq_id": "dlq-123",
  "original_event": {...},
  "error": "Rule evaluation timeout",
  "attempts": 3,
  "first_failure": "2025-01-20T10:00:00Z",
  "last_failure": "2025-01-20T10:05:00Z"
}
```

### DLQ Actions

| Action | Description |
|--------|-------------|
| **Retry** | Attempt to reprocess |
| **Skip** | Mark as handled, don't retry |
| **Archive** | Move to archive |
| **Investigate** | Open detailed view |

## API Access

### Query Events

```typescript
const events = await client.queryEvents({
  types: ['decision.completed', 'decision.timeout'],
  start_time: '2025-01-20T00:00:00Z',
  end_time: '2025-01-20T23:59:59Z',
  limit: 100
});
```

### Subscribe to Events

```typescript
const subscription = client.subscribeToEvents({
  types: ['decision.*', 'workflow.*']
}, (event) => {
  console.log('Event:', event);
});

// Later: unsubscribe
subscription.unsubscribe();
```

## Debugging with Events

### Tracing a Decision

1. Get the correlation ID from your application
2. Filter events by correlation ID
3. Follow the event sequence
4. Identify where issues occurred

### Finding Rule Matches

1. Filter by `rule.matched` events
2. Look at which rules are matching
3. Review unexpected matches

### Workflow Issues

1. Find `workflow.started` event
2. Trace through `stage_entered` events
3. See where workflow is stuck

## Best Practices

### 1. Use Correlation IDs
Always include correlation IDs in your API calls.

### 2. Monitor in Real-Time
Keep a dashboard showing live events.

### 3. Set Up Alerts
Don't wait for users to report issues.

### 4. Regular DLQ Review
Check DLQ daily for stuck events.

### 5. Archive for Analysis
Export events for trend analysis.

## Related

- [Audit Trail](/docs/user-guides/control/environments)
- [Metrics Dashboard](/docs/user-guides/control/rollback)
- [Troubleshooting](/docs/advanced/troubleshooting)
