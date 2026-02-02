"""
Prometheus Metrics Infrastructure

Provides metrics collection with Prometheus client.
Uses middleware + decorator pattern to wrap Phase 1 WITHOUT modifying it.

Source: Phase 2 Design & Execution Plan - Section 3.2

NOTE: prometheus_client is OPTIONAL for Phase A.
If not installed, stub implementations are used.
"""

from typing import Optional

# Try to import prometheus_client, provide stubs if not available
try:
    from .prometheus_client import (
        metrics_registry,
        get_metrics_registry,
        initialize_metrics,
        database_pool_active_connections,
        core_decisions_total,
        core_decision_latency_seconds,
        core_workflows_total,
        core_idempotency_hits,
        core_idempotency_conflicts,
        core_rule_evaluations,
        core_errors_total,
        http_requests_total,
        http_request_duration_seconds,
        get_metrics_text,
    )
    from .prometheus_middleware import PrometheusMiddleware
    from .metrics_decorator import MetricsDecorator
    PROMETHEUS_AVAILABLE = True

except ImportError:
    # Phase A mode: prometheus_client not installed
    # Provide stub implementations
    PROMETHEUS_AVAILABLE = False
    metrics_registry = None
    database_pool_active_connections = None
    core_decisions_total = None
    core_decision_latency_seconds = None
    core_workflows_total = None
    core_idempotency_hits = None
    core_idempotency_conflicts = None
    core_rule_evaluations = None
    core_errors_total = None
    http_requests_total = None
    http_request_duration_seconds = None

    def get_metrics_registry():
        """Stub: prometheus not available"""
        return None

    def initialize_metrics(registry=None):
        """Stub: prometheus not available"""
        pass

    def get_metrics_text() -> bytes:
        """Stub: prometheus not available"""
        return b"# Prometheus metrics not available (Phase A mode)\n"

    class PrometheusMiddleware:
        """Stub middleware when prometheus not available"""
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)

    class MetricsDecorator:
        """Stub decorator when prometheus not available"""
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, func):
            return func


__all__ = [
    "PROMETHEUS_AVAILABLE",
    "metrics_registry",
    "get_metrics_registry",
    "initialize_metrics",
    "get_metrics_text",
    "database_pool_active_connections",
    "core_decisions_total",
    "core_decision_latency_seconds",
    "core_workflows_total",
    "core_idempotency_hits",
    "core_idempotency_conflicts",
    "core_rule_evaluations",
    "core_errors_total",
    "http_requests_total",
    "http_request_duration_seconds",
    "PrometheusMiddleware",
    "MetricsDecorator",
]
