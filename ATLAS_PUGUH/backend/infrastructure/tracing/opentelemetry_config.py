"""
OpenTelemetry Configuration

Configures distributed tracing with Jaeger exporter.
Auto-instruments FastAPI, SQLAlchemy, and httpx.

Source: Phase 2 Design & Execution Plan - Section 3.3
"""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


# Global tracer instance
_tracer_provider: Optional[TracerProvider] = None
_initialized = False


def initialize_tracing(
    service_name: str = "core-service",
    service_version: str = "2.0.0",
    jaeger_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
):
    """
    Initialize OpenTelemetry tracing

    Args:
        service_name: Service name for tracing
        service_version: Service version
        jaeger_endpoint: Jaeger collector endpoint (optional)
        enable_console_export: Enable console exporter for debugging (optional)

    Environment Variables:
        JAEGER_ENDPOINT: Jaeger collector endpoint (e.g., "http://localhost:14268/api/traces")
        OTEL_TRACES_ENABLED: Enable/disable tracing (default: true)
    """
    global _tracer_provider, _initialized

    if _initialized:
        return

    # Check if tracing is enabled
    if os.getenv("OTEL_TRACES_ENABLED", "true").lower() == "false":
        print("OpenTelemetry tracing disabled")
        return

    # Create resource with service metadata
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Add Jaeger exporter if endpoint provided
    jaeger_endpoint = jaeger_endpoint or os.getenv("JAEGER_ENDPOINT")
    if jaeger_endpoint:
        jaeger_exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        print(f"✅ OpenTelemetry Jaeger exporter configured: {jaeger_endpoint}")

    # Add console exporter if enabled (for debugging)
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        print("✅ OpenTelemetry console exporter enabled")

    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Auto-instrument libraries
    _instrument_libraries()

    _initialized = True
    print(f"✅ OpenTelemetry tracing initialized for service: {service_name}")


def _instrument_libraries():
    """
    Auto-instrument libraries with OpenTelemetry

    Instruments:
    - FastAPI: HTTP request/response spans
    - SQLAlchemy: Database query spans
    - HTTPX: Outgoing HTTP request spans (for future SDK calls)
    """
    # Instrument FastAPI (auto-creates spans for all HTTP requests)
    FastAPIInstrumentor().instrument()

    # Instrument SQLAlchemy (auto-creates spans for database queries)
    SQLAlchemyInstrumentor().instrument()

    # Instrument HTTPX (for future outgoing HTTP calls)
    HTTPXClientInstrumentor().instrument()

    print("✅ OpenTelemetry auto-instrumentation enabled: FastAPI, SQLAlchemy, HTTPX")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get tracer instance for manual span creation

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance

    Example:
        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("custom_operation"):
            # Your code here
            pass
    """
    return trace.get_tracer(name)


def shutdown_tracing():
    """
    Shutdown tracing and flush remaining spans

    Should be called on application shutdown.
    """
    global _tracer_provider

    if _tracer_provider:
        _tracer_provider.shutdown()
        print("✅ OpenTelemetry tracing shutdown complete")
