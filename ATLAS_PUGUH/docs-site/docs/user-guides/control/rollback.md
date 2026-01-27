---
sidebar_position: 3
---

# Metrics Dashboard

Monitor system health and performance with the metrics dashboard.

## Overview

The Metrics Dashboard provides real-time and historical insights into your PUGUH system's performance, usage, and health.

## Accessing Metrics

Navigate to **Control > Metrics** to view the dashboard.

## Key Metrics

### Decision Metrics

| Metric | Description |
|--------|-------------|
| **Decisions/min** | Current decision throughput |
| **Avg Latency** | Mean decision evaluation time |
| **P99 Latency** | 99th percentile latency |
| **Error Rate** | Percentage of failed decisions |

### Rule Metrics

| Metric | Description |
|--------|-------------|
| **Active Rules** | Currently active rules |
| **Matches/min** | Rule matches per minute |
| **Evaluation Time** | Time to evaluate rules |

### Workflow Metrics

| Metric | Description |
|--------|-------------|
| **Pending** | Workflows awaiting action |
| **Completed/day** | Daily completions |
| **Avg Cycle Time** | Creation to completion |
| **SLA Compliance** | % meeting SLA |

### System Metrics

| Metric | Description |
|--------|-------------|
| **API Requests** | Total API calls |
| **Cache Hit Rate** | Cache effectiveness |
| **DB Connections** | Active connections |
| **Memory Usage** | Current memory use |

## Dashboard Panels

### Decision Volume

Line chart showing decisions over time:
- Requests received
- Successful decisions
- Failed decisions

### Latency Distribution

Histogram of decision latency:
```
< 10ms:  ████████████████████ 75%
10-50ms: ██████ 20%
50-100ms: █ 4%
> 100ms: ░ 1%

P50: 8ms | P95: 35ms | P99: 85ms
```

### Rule Performance

Table of rule performance:
```
| Rule Name          | Matches | Avg Time | Errors |
|--------------------|---------|----------|--------|
| high-value-rule    | 1,234   | 2ms      | 0      |
| dept-approval      | 5,678   | 3ms      | 2      |
| executive-bypass   | 123     | 1ms      | 0      |
```

### Workflow Funnel

Workflow completion funnel:
```
Created:    1000 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
Stage 1:     900 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
Stage 2:     750 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
Completed:   700 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓

Approval Rate: 70%
```

### Usage by Project

Pie chart of usage distribution:
- Project A: 45%
- Project B: 30%
- Project C: 25%

## Time Ranges

Select the time range for metrics:
- Last 15 minutes (real-time)
- Last hour
- Last 24 hours
- Last 7 days
- Last 30 days
- Custom range

## Alerts Configuration

### Creating Metric Alerts

1. Click on any metric panel
2. Click **"Create Alert"**
3. Configure threshold and duration
4. Set notification channels

### Example Alerts

**High Latency Alert:**
```yaml
metric: decision.latency.p99
condition: > 100ms
duration: 5 minutes
severity: warning
notify: ops-team
```

**Error Rate Alert:**
```yaml
metric: decision.error_rate
condition: > 1%
duration: 2 minutes
severity: critical
notify: [ops-team, on-call]
```

**Low Cache Hit Rate:**
```yaml
metric: cache.hit_rate
condition: < 80%
duration: 10 minutes
severity: warning
notify: ops-team
```

## Usage Monitoring

### Plan Usage

Track usage against plan limits:

```
Decisions This Month:
[████████████░░░░░░░░] 60% (6,000 / 10,000)

Projects:
[████░░░░░░░░░░░░░░░░] 20% (1 / 5)

Team Members:
[██████░░░░░░░░░░░░░░] 30% (3 / 10)
```

### Usage Trends

Line chart showing monthly usage:
- Current month
- Previous month
- Projected usage

### Usage Alerts

Get notified before hitting limits:
```yaml
alert: Usage Warning
trigger:
  usage_percent: > 80%
  resource: decisions
notify: billing-admin
```

## Custom Dashboards (Pro+)

### Creating Custom Dashboards

1. Go to **Metrics > Dashboards**
2. Click **"New Dashboard"**
3. Add panels from available metrics
4. Arrange and resize
5. Save dashboard

### Sharing Dashboards

- Share with team members
- Export as PDF
- Schedule email reports

## API Access

### Query Metrics

```typescript
const metrics = await client.queryMetrics({
  metrics: ['decision.count', 'decision.latency.p99'],
  start_time: '2025-01-20T00:00:00Z',
  end_time: '2025-01-20T23:59:59Z',
  interval: '5m'
});
```

### Get Current Values

```typescript
const current = await client.getCurrentMetrics([
  'decision.rate',
  'workflow.pending_count',
  'cache.hit_rate'
]);
```

## Interpreting Metrics

### Healthy System

- Decision latency P99 < 100ms
- Error rate < 0.1%
- Cache hit rate > 90%
- No DLQ backlog

### Warning Signs

- Increasing latency trend
- Error rate spikes
- Decreasing cache hit rate
- Growing DLQ

### Troubleshooting by Metric

| Symptom | Possible Cause | Action |
|---------|----------------|--------|
| High latency | Complex rules | Optimize rule conditions |
| Low cache hit | Cache invalidation | Review cache strategy |
| High error rate | Rule errors | Check rule configurations |
| DLQ growth | Processing failures | Investigate DLQ entries |

## Best Practices

### 1. Set Baseline
Establish normal metric ranges during quiet periods.

### 2. Alert on Deviations
Alert when metrics deviate from baseline.

### 3. Review Regularly
Check dashboards daily, review trends weekly.

### 4. Correlate Metrics
Look at multiple metrics together for context.

### 5. Document Incidents
Record what metrics looked like during incidents.

## Related

- [Audit Trail](/docs/user-guides/control/environments)
- [Event Timeline](/docs/user-guides/control/deployment)
- [Troubleshooting](/docs/advanced/troubleshooting)
