"""
Prometheus Metrics

Defines and exports Prometheus metrics for MANTRA.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry

# Create a registry
metrics = CollectorRegistry()

# ============================================================================
# Application Info
# ============================================================================

app_info = Info(
    "mantra_app",
    "MANTRA application information",
    registry=metrics,
)
app_info.info({
    "version": "1.0.0",
    "service": "atlas_mantra",
})

# ============================================================================
# HTTP Request Metrics
# ============================================================================

request_counter = Counter(
    "mantra_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=metrics,
)

request_latency = Histogram(
    "mantra_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=metrics,
)

# ============================================================================
# Decision Metrics
# ============================================================================

decision_counter = Counter(
    "mantra_decisions_total",
    "Total decisions processed",
    ["operation", "domain", "status"],
    registry=metrics,
)

decision_gauge = Gauge(
    "mantra_decisions_count",
    "Current count of decisions",
    ["domain", "aspect"],
    registry=metrics,
)

# ============================================================================
# Validation Metrics
# ============================================================================

validation_counter = Counter(
    "mantra_validations_total",
    "Total validation operations",
    ["gate", "result"],
    registry=metrics,
)

validation_latency = Histogram(
    "mantra_validation_duration_seconds",
    "Validation latency in seconds",
    ["gate"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=metrics,
)

validation_violations = Counter(
    "mantra_validation_violations_total",
    "Total validation violations",
    ["rule_id", "severity"],
    registry=metrics,
)

# ============================================================================
# Retrieval Metrics
# ============================================================================

retrieval_counter = Counter(
    "mantra_retrievals_total",
    "Total retrieval operations",
    ["source", "cache_hit"],
    registry=metrics,
)

retrieval_latency = Histogram(
    "mantra_retrieval_duration_seconds",
    "Retrieval latency in seconds",
    ["source"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=metrics,
)

retrieval_results = Histogram(
    "mantra_retrieval_results_count",
    "Number of results returned per retrieval",
    ["source"],
    buckets=[1, 5, 10, 20, 50, 100],
    registry=metrics,
)

# ============================================================================
# Export Metrics
# ============================================================================

export_counter = Counter(
    "mantra_exports_total",
    "Total export operations",
    ["target", "status"],
    registry=metrics,
)

export_latency = Histogram(
    "mantra_export_duration_seconds",
    "Export latency in seconds",
    ["target"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=metrics,
)

# ============================================================================
# Background Job Metrics
# ============================================================================

job_counter = Counter(
    "mantra_jobs_total",
    "Total background jobs",
    ["task", "status"],
    registry=metrics,
)

job_latency = Histogram(
    "mantra_job_duration_seconds",
    "Job execution latency in seconds",
    ["task"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
    registry=metrics,
)

job_queue_size = Gauge(
    "mantra_job_queue_size",
    "Number of jobs in queue",
    ["queue"],
    registry=metrics,
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits = Counter(
    "mantra_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
    registry=metrics,
)

cache_misses = Counter(
    "mantra_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
    registry=metrics,
)

cache_size = Gauge(
    "mantra_cache_size_bytes",
    "Cache size in bytes",
    ["cache_type"],
    registry=metrics,
)

# ============================================================================
# Embedding Metrics
# ============================================================================

embedding_counter = Counter(
    "mantra_embeddings_total",
    "Total embedding computations",
    ["provider"],
    registry=metrics,
)

embedding_latency = Histogram(
    "mantra_embedding_duration_seconds",
    "Embedding computation latency in seconds",
    ["provider"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=metrics,
)

# ============================================================================
# AI Service Metrics
# ============================================================================

ai_counter = Counter(
    "mantra_ai_requests_total",
    "Total AI service requests",
    ["provider", "operation"],
    registry=metrics,
)

ai_latency = Histogram(
    "mantra_ai_duration_seconds",
    "AI service latency in seconds",
    ["provider", "operation"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=metrics,
)

ai_tokens = Counter(
    "mantra_ai_tokens_total",
    "Total AI tokens used",
    ["provider", "type"],
    registry=metrics,
)

# ============================================================================
# Service Health Metrics
# ============================================================================

service_health = Gauge(
    "mantra_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
    registry=metrics,
)

service_uptime = Gauge(
    "mantra_service_uptime_seconds",
    "Service uptime in seconds",
    registry=metrics,
)


# ============================================================================
# Helper Functions
# ============================================================================


def record_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics."""
    request_counter.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()
    request_latency.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)


def record_validation(gate: str, passed: bool, duration: float):
    """Record validation metrics."""
    validation_counter.labels(
        gate=gate,
        result="pass" if passed else "fail",
    ).inc()
    validation_latency.labels(gate=gate).observe(duration)


def record_retrieval(source: str, cache_hit: bool, duration: float, result_count: int):
    """Record retrieval metrics."""
    retrieval_counter.labels(
        source=source,
        cache_hit=str(cache_hit).lower(),
    ).inc()
    retrieval_latency.labels(source=source).observe(duration)
    retrieval_results.labels(source=source).observe(result_count)


def record_export(target: str, success: bool, duration: float):
    """Record export metrics."""
    export_counter.labels(
        target=target,
        status="success" if success else "failure",
    ).inc()
    export_latency.labels(target=target).observe(duration)


def record_job(task: str, success: bool, duration: float):
    """Record background job metrics."""
    job_counter.labels(
        task=task,
        status="success" if success else "failure",
    ).inc()
    job_latency.labels(task=task).observe(duration)
