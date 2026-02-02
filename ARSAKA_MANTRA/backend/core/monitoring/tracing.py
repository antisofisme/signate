"""
OpenTelemetry Tracing

Distributed tracing for MANTRA using OpenTelemetry.
"""

import os
from typing import Any, Optional, Callable
from functools import wraps
from contextvars import ContextVar

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    Resource = None
    OTLPSpanExporter = None
    Status = None
    StatusCode = None
    SpanKind = None
    TraceContextTextMapPropagator = None


# Current span context
current_span_var: ContextVar[Optional[Any]] = ContextVar("current_span", default=None)


class NoopSpan:
    """No-op span when tracing is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, key: str, value: Any):
        pass

    def set_status(self, status: Any):
        pass

    def record_exception(self, exception: Exception):
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None):
        pass


class NoopTracer:
    """No-op tracer when tracing is disabled."""

    def start_as_current_span(self, name: str, **kwargs):
        return NoopSpan()


_tracer: Optional[Any] = None
_propagator: Optional[Any] = None


def setup_tracing(
    service_name: str = "arsaka_mantra",
    otlp_endpoint: Optional[str] = None,
    enabled: bool = True,
) -> bool:
    """
    Set up OpenTelemetry tracing.

    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint (default from env)
        enabled: Whether to enable tracing

    Returns:
        True if tracing was set up successfully
    """
    global _tracer, _propagator

    if not enabled or not OTEL_AVAILABLE:
        _tracer = NoopTracer()
        return False

    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

    try:
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Create exporter
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

        # Add processor
        provider.add_span_processor(BatchSpanProcessor(exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        _tracer = trace.get_tracer(service_name)

        # Set up propagator
        _propagator = TraceContextTextMapPropagator()

        return True

    except Exception as e:
        print(f"Failed to set up tracing: {e}")
        _tracer = NoopTracer()
        return False


def get_tracer() -> Any:
    """
    Get the tracer instance.

    Returns:
        Tracer instance (or NoopTracer if not available)
    """
    global _tracer
    if _tracer is None:
        _tracer = NoopTracer()
    return _tracer


def trace_span(
    name: str,
    kind: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
):
    """
    Decorator to trace a function.

    Args:
        name: Span name
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
        attributes: Additional span attributes

    Usage:
        @trace_span("my_operation", attributes={"custom": "value"})
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()

            span_kind = None
            if OTEL_AVAILABLE and kind and SpanKind:
                span_kind = getattr(SpanKind, kind.upper(), SpanKind.INTERNAL)

            with tracer.start_as_current_span(name, kind=span_kind) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    if OTEL_AVAILABLE and Status:
                        span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    if OTEL_AVAILABLE and Status:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()

            span_kind = None
            if OTEL_AVAILABLE and kind and SpanKind:
                span_kind = getattr(SpanKind, kind.upper(), SpanKind.INTERNAL)

            with tracer.start_as_current_span(name, kind=span_kind) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    if OTEL_AVAILABLE and Status:
                        span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    if OTEL_AVAILABLE and Status:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_trace_context() -> dict[str, str]:
    """
    Get the current trace context for propagation.

    Returns:
        Dictionary with trace context headers
    """
    if not OTEL_AVAILABLE or _propagator is None:
        return {}

    carrier: dict[str, str] = {}
    _propagator.inject(carrier)
    return carrier


def extract_trace_context(headers: dict[str, str]) -> Any:
    """
    Extract trace context from headers.

    Args:
        headers: HTTP headers containing trace context

    Returns:
        Context object (or None if not available)
    """
    if not OTEL_AVAILABLE or _propagator is None:
        return None

    return _propagator.extract(headers)


# ============================================================================
# Tracing Middleware
# ============================================================================


async def tracing_middleware(request, call_next):
    """
    Middleware to add tracing to requests.

    Usage with FastAPI:
        app.middleware("http")(tracing_middleware)
    """
    tracer = get_tracer()

    # Extract context from headers
    if OTEL_AVAILABLE and _propagator:
        ctx = extract_trace_context(dict(request.headers))
    else:
        ctx = None

    span_name = f"{request.method} {request.url.path}"

    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.SERVER if OTEL_AVAILABLE and SpanKind else None,
    ) as span:
        # Add request attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.route", request.url.path)

        if request.client:
            span.set_attribute("http.client_ip", request.client.host)

        try:
            response = await call_next(request)

            # Add response attributes
            span.set_attribute("http.status_code", response.status_code)

            if OTEL_AVAILABLE and Status:
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))

            return response

        except Exception as e:
            span.record_exception(e)
            if OTEL_AVAILABLE and Status:
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
