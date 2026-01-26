"""
Prometheus Metrics Infrastructure

Provides metrics collection with Prometheus client.
Uses middleware + decorator pattern to wrap Phase 1 WITHOUT modifying it.

Source: Phase 2 Design & Execution Plan - Section 3.2
"""

from .prometheus_client import (
    metrics_registry,
    get_metrics_registry,
    initialize_metrics,
)
from .prometheus_middleware import PrometheusMiddleware
from .metrics_decorator import MetricsDecorator

__all__ = [
    "metrics_registry",
    "get_metrics_registry",
    "initialize_metrics",
    "PrometheusMiddleware",
    "MetricsDecorator",
]
