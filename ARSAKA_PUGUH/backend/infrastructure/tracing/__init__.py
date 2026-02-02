"""
Distributed Tracing Infrastructure (OpenTelemetry)

Provides distributed tracing with OpenTelemetry.
Auto-instruments FastAPI and SQLAlchemy WITHOUT modifying Phase 1 code.

Source: Phase 2 Design & Execution Plan - Section 3.3
"""

from .opentelemetry_config import initialize_tracing, get_tracer
from .tracing_decorator import TracingDecorator

__all__ = [
    "initialize_tracing",
    "get_tracer",
    "TracingDecorator",
]
