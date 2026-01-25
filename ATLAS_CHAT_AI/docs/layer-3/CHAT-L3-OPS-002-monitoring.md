# CHAT-L3-OPS-002: Monitoring Guide

**Status**: Active
**Created**: 2026-01-25

---

## Overview

What to monitor, key metrics, and alerting thresholds for ATLAS_CHAT_AI.

---

## Key Metrics

### API Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `api_requests_total` | Total API requests | - |
| `api_request_duration_seconds` | Request latency | p95 > 2s |
| `api_errors_total` | Error count | > 10/min |
| `api_rate_limited_total` | Rate limited requests | > 50/min |

### Chat Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `chat_messages_total` | Messages processed | - |
| `chat_time_to_first_token_seconds` | Streaming latency | p95 > 1s |
| `chat_tokens_used_total` | LLM tokens consumed | - |
| `chat_sessions_active` | Active sessions | - |

### RAG Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `rag_retrieval_duration_seconds` | Vector search time | p95 > 500ms |
| `rag_documents_retrieved` | Docs per query | avg < 1 (no results) |
| `rag_rerank_duration_seconds` | Reranking time | p95 > 1s |
| `rag_cache_hit_ratio` | Embedding cache hits | < 50% |

### Memory Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `memory_facts_extracted_total` | Facts extracted | - |
| `memory_facts_per_user` | Average facts/user | > 100 (limit) |
| `memory_sessions_summarized_total` | Sessions summarized | - |

### Infrastructure Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `db_connections_active` | Active DB connections | > 80% of pool |
| `db_query_duration_seconds` | Query latency | p95 > 100ms |
| `qdrant_collection_vectors` | Vectors per collection | - |
| `qdrant_search_duration_seconds` | Qdrant search time | p95 > 200ms |
| `redis_memory_used_bytes` | Redis memory | > 80% of max |

---

## Prometheus Configuration

### Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chat-api'
    static_configs:
      - targets: ['chat-api:8003']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: chat-api
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in Chat API"

      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API response time is high"

      - alert: LLMErrors
        expr: rate(chat_llm_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM provider errors"

      - alert: QdrantDown
        expr: up{job="qdrant"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Qdrant is down"
```

---

## Grafana Dashboards

### Chat Overview Dashboard

**Panels:**

1. **Request Rate** (Graph)
   - Query: `rate(api_requests_total[5m])`
   - Breakdown by endpoint

2. **Error Rate** (Graph)
   - Query: `rate(api_errors_total[5m]) / rate(api_requests_total[5m])`
   - Target: < 1%

3. **Latency Distribution** (Heatmap)
   - Query: `api_request_duration_seconds_bucket`

4. **Messages per Minute** (Graph)
   - Query: `rate(chat_messages_total[1m])`

5. **Time to First Token** (Gauge)
   - Query: `histogram_quantile(0.95, rate(chat_time_to_first_token_seconds_bucket[5m]))`
   - Thresholds: Green < 500ms, Yellow < 1s, Red > 1s

6. **Token Usage** (Graph)
   - Query: `increase(chat_tokens_used_total[1h])`
   - Breakdown by provider

### RAG Performance Dashboard

**Panels:**

1. **Retrieval Latency** (Graph)
   - Query: `histogram_quantile(0.95, rate(rag_retrieval_duration_seconds_bucket[5m]))`

2. **Cache Hit Ratio** (Gauge)
   - Query: `rate(rag_cache_hits_total[5m]) / rate(rag_cache_requests_total[5m])`

3. **Documents Retrieved** (Graph)
   - Query: `avg(rag_documents_retrieved)`

4. **Vector Store Size** (Stat)
   - Query: `sum(qdrant_collection_vectors)`

### Tenant Usage Dashboard

**Panels:**

1. **Requests by Tenant** (Pie Chart)
   - Query: `sum by (tenant_id) (rate(api_requests_total[1h]))`

2. **Messages by Tenant** (Bar Graph)
   - Query: `sum by (tenant_id) (increase(chat_messages_total[24h]))`

3. **Token Costs by Tenant** (Table)
   - Query: `sum by (tenant_id) (chat_tokens_used_total)`

---

## Logging

### Log Format

```json
{
  "timestamp": "2026-01-25T10:00:00.000Z",
  "level": "INFO",
  "logger": "chat-api",
  "message": "Chat request processed",
  "tenant_id": "mantra",
  "user_id": "user-123",
  "session_id": "uuid",
  "duration_ms": 1250,
  "tokens_prompt": 500,
  "tokens_completion": 150,
  "documents_retrieved": 5,
  "trace_id": "abc123"
}
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| ERROR | Unhandled exceptions, LLM failures, DB errors |
| WARNING | Rate limits, retries, degraded performance |
| INFO | Request completion, sync jobs, key operations |
| DEBUG | Detailed flow, query parameters, responses |

### Log Aggregation (Loki Example)

```yaml
# promtail.yml
scrape_configs:
  - job_name: chat-api
    static_configs:
      - targets:
          - localhost
        labels:
          job: chat-api
          __path__: /var/log/chat-api/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            tenant_id: tenant_id
      - labels:
          level:
          tenant_id:
```

---

## Health Checks

### Endpoint: GET /health

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 5
    },
    "qdrant": {
      "status": "ok",
      "latency_ms": 10
    },
    "redis": {
      "status": "ok",
      "latency_ms": 2
    },
    "openai": {
      "status": "ok",
      "quota_remaining": 95
    }
  }
}
```

### Degraded States

| Check | Degraded Condition | Impact |
|-------|-------------------|--------|
| database | Latency > 100ms | Slower responses |
| qdrant | Latency > 200ms | RAG degraded |
| redis | Unavailable | No caching |
| openai | Quota < 10% | May hit limits |

---

## Alerting Channels

### Critical Alerts (Immediate)
- API completely down
- Database unreachable
- LLM provider errors > 10%
- Qdrant down

**Channels:** PagerDuty, SMS, Phone

### Warning Alerts (Acknowledge within 1 hour)
- High latency (> 2s p95)
- Error rate > 1%
- Approaching rate limits
- Memory usage > 80%

**Channels:** Slack, Email

### Info Alerts (Review daily)
- High token usage
- New tenant onboarded
- Sync jobs completed
- Backup completed

**Channels:** Slack (low priority channel)

---

## Runbook Links

| Alert | Runbook |
|-------|---------|
| HighErrorRate | [OPS-003 Troubleshooting](#common-issues) |
| SlowResponses | Check database queries, Qdrant performance |
| LLMErrors | Verify API key, check provider status |
| QdrantDown | Restart Qdrant, check disk space |
| DatabasePoolExhausted | Increase pool size, check slow queries |
