"""
Prometheus Client Wrapper

Centralized metrics registry and metric definitions.

Source: Phase 2 Design & Execution Plan - Section 3.2
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    REGISTRY,
    generate_latest,
)
from typing import Optional


# Global metrics registry (can be replaced for testing)
metrics_registry: Optional[CollectorRegistry] = None


def get_metrics_registry() -> CollectorRegistry:
    """Get global metrics registry"""
    global metrics_registry
    if metrics_registry is None:
        metrics_registry = REGISTRY
    return metrics_registry


def initialize_metrics(registry: Optional[CollectorRegistry] = None):
    """
    Initialize all metrics

    Args:
        registry: Custom registry (optional, defaults to global REGISTRY)
    """
    global metrics_registry
    metrics_registry = registry or REGISTRY

    # Decision metrics
    global core_decisions_total, core_decision_latency_seconds
    core_decisions_total = Counter(
        "core_decisions_total",
        "Total number of decisions created",
        ["tenant_id", "decision_type", "outcome"],
        registry=metrics_registry
    )

    core_decision_latency_seconds = Histogram(
        "core_decision_latency_seconds",
        "Decision creation latency in seconds",
        ["decision_type"],
        registry=metrics_registry,
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
    )

    # Workflow metrics
    global core_workflows_total
    core_workflows_total = Counter(
        "core_workflows_total",
        "Total number of workflows processed",
        ["tenant_id", "state"],
        registry=metrics_registry
    )

    # Idempotency metrics
    global core_idempotency_hits, core_idempotency_conflicts
    core_idempotency_hits = Counter(
        "core_idempotency_hits",
        "Number of idempotency cache hits",
        ["tenant_id"],
        registry=metrics_registry
    )

    core_idempotency_conflicts = Counter(
        "core_idempotency_conflicts",
        "Number of idempotency conflicts detected",
        ["tenant_id"],
        registry=metrics_registry
    )

    # Rule evaluation metrics
    global core_rule_evaluations
    core_rule_evaluations = Counter(
        "core_rule_evaluations",
        "Number of rule evaluations performed",
        ["tenant_id", "rule_id"],
        registry=metrics_registry
    )

    # Error metrics
    global core_errors_total
    core_errors_total = Counter(
        "core_errors_total",
        "Total number of errors",
        ["error_code"],
        registry=metrics_registry
    )

    # HTTP request metrics
    global http_requests_total, http_request_duration_seconds
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
        registry=metrics_registry
    )

    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "endpoint"],
        registry=metrics_registry,
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
    )

    # Database connection pool metrics
    global database_pool_active_connections
    database_pool_active_connections = Gauge(
        "database_pool_active_connections",
        "Number of active database connections",
        registry=metrics_registry
    )


# Metric accessors (initialized on first import)
core_decisions_total: Optional[Counter] = None
core_decision_latency_seconds: Optional[Histogram] = None
core_workflows_total: Optional[Counter] = None
core_idempotency_hits: Optional[Counter] = None
core_idempotency_conflicts: Optional[Counter] = None
core_rule_evaluations: Optional[Counter] = None
core_errors_total: Optional[Counter] = None
http_requests_total: Optional[Counter] = None
http_request_duration_seconds: Optional[Histogram] = None
database_pool_active_connections: Optional[Gauge] = None


def get_metrics_text() -> bytes:
    """
    Get metrics in Prometheus text format

    Returns:
        Metrics in Prometheus exposition format
    """
    return generate_latest(get_metrics_registry())
