"""
Event Bus Metrics - Observability for event publishing

CRITICAL METRICS:
- event_publish_lag: Time between recording and publishing
- event_publish_attempts: Number of publish attempts
- event_dlq_size: Dead-letter queue size
- consumer_lag: Consumer processing lag

Source: Phase 3 Requirements - Observability (Event-Level)
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    REGISTRY,
)


# =============================================================================
# PUBLISHER METRICS
# =============================================================================

# Event publish lag (time from recorded_at to published_at)
event_publish_lag = Histogram(
    "event_publish_lag_seconds",
    "Time between event recording and publishing",
    ["event_type"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Publish attempts histogram
event_publish_attempts = Histogram(
    "event_publish_attempts",
    "Number of publish attempts before success or DLQ",
    ["event_type"],
    buckets=(1, 2, 3, 4, 5),
)

# Successful publishes
event_publish_success = Counter(
    "event_publish_success_total",
    "Total successful event publishes",
    ["event_type", "tenant_id"],
)

# Failed publishes (before DLQ)
event_publish_failure = Counter(
    "event_publish_failure_total",
    "Total failed event publish attempts",
    ["event_type", "tenant_id"],
)


# =============================================================================
# DLQ METRICS
# =============================================================================

# DLQ size (gauge - current size)
event_dlq_size = Gauge(
    "event_dlq_size",
    "Current number of events in dead-letter queue",
    ["event_type", "tenant_id"],
)

# DLQ additions
event_dlq_additions = Counter(
    "event_dlq_additions_total",
    "Total events moved to dead-letter queue",
    ["event_type", "tenant_id"],
)

# DLQ reprocessed
event_dlq_reprocessed = Counter(
    "event_dlq_reprocessed_total",
    "Total events reprocessed from dead-letter queue",
    ["event_type", "tenant_id"],
)


# =============================================================================
# OUTBOX METRICS
# =============================================================================

# Outbox size (unpublished events)
outbox_pending_events = Gauge(
    "outbox_pending_events",
    "Current number of unpublished events in outbox",
)

# Outbox poll duration
outbox_poll_duration = Histogram(
    "outbox_poll_duration_seconds",
    "Duration of outbox poll operation",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# Outbox batch size
outbox_batch_size = Histogram(
    "outbox_batch_size",
    "Number of events processed per poll",
    buckets=(1, 5, 10, 25, 50, 100),
)


# =============================================================================
# CONSUMER METRICS
# =============================================================================

# Consumer lag (time from published to consumed)
consumer_lag = Histogram(
    "consumer_lag_seconds",
    "Time between event publishing and consumption",
    ["consumer_group", "event_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Consumer messages processed
consumer_messages_processed = Counter(
    "consumer_messages_processed_total",
    "Total messages processed by consumers",
    ["consumer_group", "event_type", "status"],  # status: success, failure, skipped
)

# Consumer processing duration
consumer_processing_duration = Histogram(
    "consumer_processing_duration_seconds",
    "Duration of consumer message processing",
    ["consumer_group", "event_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# Consumer idempotency hits (duplicate detection)
consumer_idempotency_hits = Counter(
    "consumer_idempotency_hits_total",
    "Number of duplicate events detected by consumer",
    ["consumer_group", "event_type"],
)


# =============================================================================
# HEALTH METRICS
# =============================================================================

# Publisher health
publisher_health = Gauge(
    "publisher_health",
    "Publisher health status (1=healthy, 0=unhealthy)",
)

# Outbox poller health
outbox_poller_health = Gauge(
    "outbox_poller_health",
    "Outbox poller health status (1=running, 0=stopped)",
)

# Last successful poll timestamp
outbox_last_poll_timestamp = Gauge(
    "outbox_last_poll_timestamp_seconds",
    "Timestamp of last successful outbox poll (Unix epoch)",
)

# Stuck event detection
outbox_stuck_events = Gauge(
    "outbox_stuck_events",
    "Number of events stuck (unpublished > threshold)",
    ["threshold_minutes"],
)


# =============================================================================
# INFO METRICS
# =============================================================================

# Event bus configuration info
eventbus_info = Info(
    "eventbus",
    "Event bus configuration information",
)


def set_eventbus_info(
    bootstrap_servers: str,
    schema_registry_url: str = None,
    topics: list = None
):
    """Set event bus info labels"""
    eventbus_info.info({
        "bootstrap_servers": bootstrap_servers,
        "schema_registry_url": schema_registry_url or "none",
        "topics": ",".join(topics) if topics else "none",
    })


# =============================================================================
# ALERT THRESHOLDS (for documentation / alert rules)
# =============================================================================

ALERT_THRESHOLDS = {
    # DLQ alerts
    "dlq_size_warning": 10,
    "dlq_size_critical": 100,
    "dlq_growth_rate_per_minute": 5,

    # Lag alerts
    "publish_lag_warning_seconds": 30,
    "publish_lag_critical_seconds": 300,
    "consumer_lag_warning_seconds": 5,
    "consumer_lag_critical_seconds": 30,

    # Stuck event alerts
    "stuck_warning_minutes": 5,
    "stuck_critical_minutes": 15,

    # Failure rate alerts (per minute)
    "publish_failure_rate_warning": 0.01,  # 1%
    "publish_failure_rate_critical": 0.05,  # 5%
}


# =============================================================================
# PROMETHEUS ALERT RULES (for deployment)
# =============================================================================

PROMETHEUS_ALERT_RULES = """
# Event Bus Alert Rules
# Deploy to Prometheus AlertManager

groups:
  - name: eventbus
    interval: 30s
    rules:
      # DLQ size warning
      - alert: EventDLQSizeWarning
        expr: sum(event_dlq_size) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Event DLQ has {{ $value }} events"
          description: "Dead-letter queue is growing. Check event_dlq table."

      # DLQ size critical
      - alert: EventDLQSizeCritical
        expr: sum(event_dlq_size) > 100
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Event DLQ critical: {{ $value }} events"
          description: "Dead-letter queue is critically high. Immediate attention required."

      # Publish lag warning
      - alert: EventPublishLagWarning
        expr: histogram_quantile(0.95, rate(event_publish_lag_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Event publish lag high: {{ $value }}s"
          description: "95th percentile publish lag exceeds 30 seconds."

      # Publish lag critical
      - alert: EventPublishLagCritical
        expr: histogram_quantile(0.95, rate(event_publish_lag_seconds_bucket[5m])) > 300
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Event publish lag critical: {{ $value }}s"
          description: "95th percentile publish lag exceeds 5 minutes."

      # Outbox poller down
      - alert: OutboxPollerDown
        expr: outbox_poller_health == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Outbox poller is down"
          description: "The outbox poller is not running. Events will not be published."

      # Stuck events
      - alert: EventsStuck
        expr: outbox_stuck_events > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} events stuck in outbox"
          description: "Events have been unpublished for longer than threshold."

      # High failure rate
      - alert: EventPublishFailureRateHigh
        expr: >
          rate(event_publish_failure_total[5m]) /
          (rate(event_publish_success_total[5m]) + rate(event_publish_failure_total[5m]))
          > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Event publish failure rate: {{ $value | humanizePercentage }}"
          description: "More than 5% of event publishes are failing."
"""
