---
sidebar_position: 3
---

# Best Practices

Recommendations for using ATLAS PUGUH effectively.

## Rule Design

### Keep Rules Simple

Complex rules are harder to understand and maintain:

```typescript
// Bad: Overly complex
{
  conditions: {
    all: [
      { field: 'a', operator: '>', value: 1 },
      {
        any: [
          { field: 'b', operator: '=', value: 'x' },
          {
            all: [
              { field: 'c', operator: '<', value: 10 },
              { field: 'd', operator: '!=', value: 'y' }
            ]
          }
        ]
      }
    ]
  }
}

// Good: Split into multiple rules
// Rule 1: High priority
{
  name: 'Condition A with B',
  priority: 100,
  conditions: {
    all: [
      { field: 'a', operator: '>', value: 1 },
      { field: 'b', operator: '=', value: 'x' }
    ]
  }
}

// Rule 2: Lower priority
{
  name: 'Condition A with C and D',
  priority: 50,
  conditions: {
    all: [
      { field: 'a', operator: '>', value: 1 },
      { field: 'c', operator: '<', value: 10 },
      { field: 'd', operator: '!=', value: 'y' }
    ]
  }
}
```

### Use Meaningful Names

```typescript
// Bad
'Rule 1', 'Test', 'New Rule'

// Good
'High Value Equipment Requires CFO Approval'
'Marketing Budget Over $10K Needs VP Sign-off'
'After-Hours Access Requires Security Review'
```

### Document the Why

```typescript
{
  name: 'Emergency Purchase Bypass',
  description: `
    Allows purchases up to $5000 without approval when marked as emergency.
    Created after incident INC-1234 where critical equipment couldn't be purchased.
    Requires is_emergency flag from procurement system.
    Review quarterly for abuse patterns.
  `
}
```

## Testing

### Test Every Rule

No rule should go to production without tests:

```typescript
describe('High Value Approval Rule', () => {
  it('should require approval for amounts over $5000', async () => {
    const result = await testRule(ruleId, { amount: 7500 });
    expect(result.outcome).toBe('REQUIRE_APPROVAL');
  });

  it('should allow amounts under $5000', async () => {
    const result = await testRule(ruleId, { amount: 3000 });
    expect(result.matches).toBe(false);
  });

  it('should handle boundary case at exactly $5000', async () => {
    const result = await testRule(ruleId, { amount: 5000 });
    expect(result.matches).toBe(false); // > 5000, not >=
  });
});
```

### Use Staging Projects

1. Create rules in Development project
2. Test thoroughly
3. Move to Staging project
4. Final verification
5. Activate in Production

### Automate Testing in CI/CD

```yaml
# .github/workflows/test-rules.yml
- name: Test PUGUH Rules
  run: |
    npm run test:rules
    puguh-cli test --scenarios ./tests/rules/
```

## Organization

### Use Project Structure

```
Tenant: Acme Corp
├── Project: production
│   ├── Rules (strict)
│   └── Workflows (with SLAs)
├── Project: staging
│   ├── Rules (mirrors prod)
│   └── Workflows (relaxed SLAs)
└── Project: development
    ├── Rules (experimental)
    └── Workflows (auto-approve)
```

### Consistent Priority Scheme

Adopt a standard priority scheme across your organization:

| Range | Purpose |
|-------|---------|
| 900-999 | Emergency overrides |
| 500-599 | Critical compliance |
| 300-399 | Business policies |
| 100-199 | Standard rules |
| 1-99 | Default fallbacks |

### Version Control Integration

Store rule definitions in git:

```
rules/
├── tenant/
│   ├── compliance/
│   │   └── soc2-requirements.json
│   └── policies/
│       └── approval-thresholds.json
└── projects/
    ├── production/
    │   └── strict-limits.json
    └── staging/
        └── test-rules.json
```

Sync with PUGUH via CI/CD:

```bash
puguh-cli sync --config ./rules/
```

## Security

### Principle of Least Privilege

1. Start users as Viewers
2. Upgrade to Member when needed
3. Admin only for management
4. Owner is singular

### Audit Regularly

```typescript
// Weekly audit script
const changes = await client.queryAuditTrail({
  startDate: sevenDaysAgo,
  actions: ['rule.created', 'rule.updated', 'rule.deleted'],
});

for (const change of changes) {
  console.log(`${change.timestamp}: ${change.actor} - ${change.action}`);
}
```

### Monitor for Anomalies

Set up alerts for:
- Unusual approval patterns
- Spike in denied decisions
- After-hours activity
- Bulk operations

### Secure API Keys

```typescript
// Use environment variables
const client = new PuguhClient({
  apiKey: process.env.PUGUH_API_KEY, // Never hardcode
});

// Rotate regularly
await client.rotateApiKey(keyId);
```

## Performance

### Use Caching

Enable decision caching for repeated identical requests:

```typescript
const decision = await client.decide({
  type: 'access_control',
  context: { userId, resourceId },
  options: {
    cache: true,
    cacheTtl: 300, // 5 minutes
  },
});
```

### Batch When Possible

```typescript
// Bad: Individual requests
for (const item of items) {
  await client.decide({ type: 'approval', context: item });
}

// Good: Batch request
const decisions = await client.decideBatch(
  items.map(item => ({ type: 'approval', context: item }))
);
```

### Optimize Rule Complexity

Simple rules evaluate faster:

```typescript
// Slower: Complex nested conditions
{
  conditions: {
    any: [
      { all: [...] },
      { all: [...] },
      { all: [...] }
    ]
  }
}

// Faster: Multiple simpler rules
// Rule 1: ...
// Rule 2: ...
// Rule 3: ...
```

## Workflow Design

### Set Appropriate Timeouts

Too short = missed approvals. Too long = delays.

| Scenario | Recommended Timeout |
|----------|---------------------|
| Manager approval | 24-48 hours |
| Finance review | 48-72 hours |
| Executive sign-off | 72-96 hours |
| Emergency | 4-8 hours |

### Define Escalation Paths

```typescript
{
  stages: [
    { name: 'Manager', timeout: '24h', onTimeout: 'escalate' },
    { name: 'Director', timeout: '24h', onTimeout: 'escalate' },
    { name: 'VP', timeout: '48h', onTimeout: 'reject' }
  ]
}
```

### Use Dynamic Assignment

```typescript
{
  participants: {
    type: 'dynamic',
    expression: 'context.requester.manager'
  }
}
```

## Monitoring

### Track Key Metrics

- Decision latency (P50, P95, P99)
- Approval rate trends
- Workflow cycle time
- Error rates

### Set Up Alerts

```yaml
alerts:
  - name: High Latency
    condition: decision.latency.p99 > 100ms
    duration: 5m
    notify: ops-team

  - name: Spike in Denials
    condition: decision.denied_rate > 10%
    duration: 15m
    notify: business-team
```

### Review Regularly

Schedule regular reviews:
- **Daily**: Check pending workflows, DLQ
- **Weekly**: Review audit logs, usage metrics
- **Monthly**: Analyze trends, optimize rules
- **Quarterly**: Security audit, role review

## Related

- [Troubleshooting](/docs/advanced/troubleshooting)
- [Multi-Tenant Architecture](/docs/advanced/multi-tenant)
- [Resource Scoping](/docs/advanced/scoping)
