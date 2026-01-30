"""
Monitoring & Observability Module

Provides:
- Prometheus metrics
- Structured logging
- OpenTelemetry tracing
- Health checks
"""

from .metrics import (
    metrics,
    request_counter,
    request_latency,
    decision_counter,
    validation_counter,
    retrieval_latency,
    export_counter,
    job_counter,
)
from .logging import (
    setup_logging,
    get_logger,
    StructuredLogger,
)
from .tracing import (
    setup_tracing,
    get_tracer,
    trace_span,
)
from .health import (
    HealthCheck,
    HealthStatus,
    check_all_services,
)

__all__ = [
    # Metrics
    "metrics",
    "request_counter",
    "request_latency",
    "decision_counter",
    "validation_counter",
    "retrieval_latency",
    "export_counter",
    "job_counter",
    # Logging
    "setup_logging",
    "get_logger",
    "StructuredLogger",
    # Tracing
    "setup_tracing",
    "get_tracer",
    "trace_span",
    # Health
    "HealthCheck",
    "HealthStatus",
    "check_all_services",
]
