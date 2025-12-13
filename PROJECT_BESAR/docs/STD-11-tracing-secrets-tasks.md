# Development Standards V11

> Standards #40-42: Distributed Tracing (OpenTelemetry), Secrets & Configuration Management, Scheduled Tasks & Cron Management

---

## Table of Contents

- [Standard #40: Distributed Tracing (OpenTelemetry)](#standard-40-distributed-tracing-opentelemetry)
- [Standard #41: Secrets & Configuration Management](#standard-41-secrets--configuration-management)
- [Standard #42: Scheduled Tasks & Cron Management](#standard-42-scheduled-tasks--cron-management)

---

## Standard #40: Distributed Tracing (OpenTelemetry)

### 40.1 Overview

Distributed Tracing memungkinkan tracking request end-to-end melintasi multiple services. OpenTelemetry (OTel) adalah standard industry untuk observability yang mencakup traces, metrics, dan logs.

### 40.2 Tracing Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED TRACING ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         REQUEST FLOW                              │   │
│  │                                                                   │   │
│  │  Client → API Gateway → Service A → Service B → Database         │   │
│  │    │          │            │           │           │              │   │
│  │    ▼          ▼            ▼           ▼           ▼              │   │
│  │  [Span 1] [Span 2]     [Span 3]    [Span 4]    [Span 5]          │   │
│  │    │          │            │           │           │              │   │
│  │    └──────────┴────────────┴───────────┴───────────┘              │   │
│  │                         │                                          │   │
│  │                    Trace ID: abc-123-xyz                          │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                    COLLECTION PIPELINE                             │   │
│  │                                                                   │   │
│  │  Application → OTel Collector → Jaeger/Tempo → Grafana            │   │
│  │      │              │               │              │              │   │
│  │   Traces         Process         Storage       Visualize          │   │
│  │   Metrics        Filter          Index         Alert              │   │
│  │   Logs           Sample          Query         Dashboard          │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 40.3 OpenTelemetry Configuration

```python
# shared/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
import os

def setup_tracing(app_name: str, app_version: str = "1.0.0"):
    """Initialize OpenTelemetry tracing"""

    # Resource attributes
    resource = Resource(attributes={
        SERVICE_NAME: app_name,
        SERVICE_VERSION: app_version,
        "deployment.environment": os.getenv("APP_ENV", "development"),
        "service.namespace": "hotel-pms",
    })

    # Create TracerProvider
    provider = TracerProvider(resource=resource)

    # Configure exporter
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    # Add BatchSpanProcessor for efficient export
    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
        )
    )

    # Set as global provider
    trace.set_tracer_provider(provider)

    # Set propagator for distributed context
    set_global_textmap(B3MultiFormat())

    return trace.get_tracer(app_name)


def instrument_app(app, engine=None, redis_client=None):
    """Instrument FastAPI app and dependencies"""

    # FastAPI instrumentation
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health/*,/metrics",
        tracer_provider=trace.get_tracer_provider()
    )

    # SQLAlchemy instrumentation
    if engine:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            enable_commenter=True,
            commenter_options={
                "db_framework": True,
                "opentelemetry_values": True,
            }
        )

    # Redis instrumentation
    if redis_client:
        RedisInstrumentor().instrument()

    # Celery instrumentation
    CeleryInstrumentor().instrument()

    # HTTP client instrumentation
    HTTPXClientInstrumentor().instrument()
```

### 40.4 Tracer Context & Span Management

```python
# shared/observability/context.py
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from contextvars import ContextVar
from typing import Optional, Dict, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Context variables
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

propagator = TraceContextTextMapPropagator()


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, '032x')
    return trace_id_var.get()


def get_current_span_id() -> Optional[str]:
    """Get current span ID"""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, '016x')
    return span_id_var.get()


def get_correlation_id() -> Optional[str]:
    """Get correlation ID (same as trace ID for simplicity)"""
    return correlation_id_var.get() or get_current_trace_id()


class SpanManager:
    """Helper class for managing spans"""

    def __init__(self, tracer_name: str = "hotel-pms"):
        self.tracer = trace.get_tracer(tracer_name)

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Start a new span"""
        return self.tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes or {}
        )

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span"""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})

    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span"""
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)

    def set_error(self, exception: Exception):
        """Mark current span as error"""
        span = trace.get_current_span()
        if span:
            span.set_status(Status(StatusCode.ERROR, str(exception)))
            span.record_exception(exception)

    def set_success(self):
        """Mark current span as success"""
        span = trace.get_current_span()
        if span:
            span.set_status(Status(StatusCode.OK))


# Global span manager
span_manager = SpanManager()


def traced(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """Decorator to trace a function"""
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with span_manager.start_span(span_name, kind=kind, attributes=attributes):
                try:
                    result = await func(*args, **kwargs)
                    span_manager.set_success()
                    return result
                except Exception as e:
                    span_manager.set_error(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with span_manager.start_span(span_name, kind=kind, attributes=attributes):
                try:
                    result = func(*args, **kwargs)
                    span_manager.set_success()
                    return result
                except Exception as e:
                    span_manager.set_error(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
```

### 40.5 FastAPI Middleware Integration

```python
# shared/observability/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.propagate import extract
from .context import (
    trace_id_var, span_id_var, correlation_id_var,
    get_current_trace_id, get_current_span_id
)
import time
import logging

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and context propagation"""

    async def dispatch(self, request: Request, call_next):
        # Extract trace context from headers
        ctx = extract(request.headers)

        # Get or generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            request.headers.get("X-Request-ID")
        )

        tracer = trace.get_tracer("http-middleware")

        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=ctx,
            kind=trace.SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.host": request.headers.get("host", ""),
                "http.user_agent": request.headers.get("user-agent", ""),
                "http.client_ip": request.client.host if request.client else "",
            }
        ) as span:
            # Set context variables
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()

            trace_id_var.set(trace_id)
            span_id_var.set(span_id)
            correlation_id_var.set(correlation_id or trace_id)

            # Add tenant context if available
            if hasattr(request.state, "tenant_id"):
                span.set_attribute("tenant.id", request.state.tenant_id)

            # Add user context if available
            if hasattr(request.state, "user_id"):
                span.set_attribute("user.id", request.state.user_id)

            start_time = time.perf_counter()

            try:
                response = await call_next(request)

                # Record response attributes
                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(trace.Status(
                        trace.StatusCode.ERROR,
                        f"HTTP {response.status_code}"
                    ))
                else:
                    span.set_status(trace.Status(trace.StatusCode.OK))

                # Add trace headers to response
                response.headers["X-Trace-ID"] = trace_id or ""
                response.headers["X-Span-ID"] = span_id or ""
                response.headers["X-Correlation-ID"] = correlation_id_var.get() or ""

                return response

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(
                    trace.StatusCode.ERROR,
                    str(e)
                ))
                raise

            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                span.set_attribute("http.duration_ms", duration_ms)

                logger.info(
                    "Request completed",
                    extra={
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "correlation_id": correlation_id_var.get(),
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                    }
                )
```

### 40.6 Database Query Tracing

```python
# shared/observability/db_tracing.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
from opentelemetry import trace
from typing import Any
import time


def setup_sqlalchemy_tracing(engine: Engine):
    """Setup detailed SQLAlchemy query tracing"""

    tracer = trace.get_tracer("sqlalchemy")

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

        # Start span for query
        span = tracer.start_span(
            "db.query",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "db.system": "postgresql",
                "db.statement": statement[:1000],  # Truncate long queries
                "db.operation": statement.split()[0].upper() if statement else "UNKNOWN",
            }
        )
        conn.info.setdefault("query_span", []).append(span)

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        start_time = conn.info["query_start_time"].pop()
        span = conn.info["query_span"].pop()

        duration_ms = (time.perf_counter() - start_time) * 1000

        span.set_attribute("db.duration_ms", duration_ms)
        span.set_attribute("db.rows_affected", cursor.rowcount)
        span.set_status(trace.Status(trace.StatusCode.OK))
        span.end()

    @event.listens_for(engine, "handle_error")
    def handle_error(exception_context):
        if "query_span" in exception_context.connection.info:
            spans = exception_context.connection.info["query_span"]
            if spans:
                span = spans.pop()
                span.record_exception(exception_context.original_exception)
                span.set_status(trace.Status(
                    trace.StatusCode.ERROR,
                    str(exception_context.original_exception)
                ))
                span.end()
```

### 40.7 Celery Task Tracing

```python
# shared/observability/celery_tracing.py
from celery import signals
from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from .context import correlation_id_var, trace_id_var
from typing import Dict, Any


def setup_celery_tracing():
    """Setup Celery task tracing with context propagation"""

    tracer = trace.get_tracer("celery")

    @signals.before_task_publish.connect
    def before_task_publish(sender=None, headers=None, body=None, **kwargs):
        """Inject trace context into task headers"""
        if headers is not None:
            # Inject current trace context
            inject(headers)

            # Also inject correlation ID
            correlation_id = correlation_id_var.get()
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id

    @signals.task_prerun.connect
    def task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
        """Extract trace context and start span for task"""

        # Extract context from task request
        ctx = extract(task.request.headers or {})

        # Get correlation ID
        correlation_id = (task.request.headers or {}).get("X-Correlation-ID")
        if correlation_id:
            correlation_id_var.set(correlation_id)

        # Start task span
        span = tracer.start_span(
            f"celery.task.{sender.name}",
            context=ctx,
            kind=trace.SpanKind.CONSUMER,
            attributes={
                "celery.task_id": task_id,
                "celery.task_name": sender.name,
                "celery.queue": task.request.delivery_info.get("routing_key", "unknown"),
                "celery.retries": task.request.retries,
            }
        )

        # Store span for later
        task.request._otel_span = span

    @signals.task_postrun.connect
    def task_postrun(
        sender=None, task_id=None, task=None,
        args=None, kwargs=None, retval=None, state=None, **kw
    ):
        """End span after task completion"""
        span = getattr(task.request, "_otel_span", None)
        if span:
            span.set_attribute("celery.state", state)

            if state == "SUCCESS":
                span.set_status(trace.Status(trace.StatusCode.OK))
            else:
                span.set_status(trace.Status(
                    trace.StatusCode.ERROR,
                    f"Task failed with state: {state}"
                ))

            span.end()

    @signals.task_failure.connect
    def task_failure(
        sender=None, task_id=None, exception=None,
        args=None, kwargs=None, traceback=None, **kw
    ):
        """Record exception on task failure"""
        task = sender
        span = getattr(task.request, "_otel_span", None)
        if span:
            span.record_exception(exception)
```

### 40.8 HTTP Client Tracing

```python
# shared/observability/http_client.py
import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject
from .context import get_correlation_id
from typing import Optional, Dict, Any


class TracedHTTPClient:
    """HTTP client with automatic tracing"""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.tracer = trace.get_tracer("http-client")

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with tracing"""

        headers = headers or {}

        # Inject trace context
        inject(headers)

        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        full_url = f"{self.base_url}{url}" if self.base_url else url

        with self.tracer.start_as_current_span(
            f"HTTP {method}",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "http.method": method,
                "http.url": full_url,
            }
        ) as span:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method, full_url, headers=headers, **kwargs
                    )

                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(trace.Status(
                        trace.StatusCode.ERROR,
                        f"HTTP {response.status_code}"
                    ))
                else:
                    span.set_status(trace.Status(trace.StatusCode.OK))

                return response

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)
```

### 40.9 Application Setup

```python
# main.py
from fastapi import FastAPI
from shared.observability.tracing import setup_tracing, instrument_app
from shared.observability.middleware import TracingMiddleware
from shared.observability.db_tracing import setup_sqlalchemy_tracing
from shared.observability.celery_tracing import setup_celery_tracing
from shared.database import engine

app = FastAPI(title="Hotel PMS API")

# Setup tracing
tracer = setup_tracing(
    app_name="hotel-pms-api",
    app_version="1.0.0"
)

# Add tracing middleware
app.add_middleware(TracingMiddleware)

# Instrument app and dependencies
instrument_app(app, engine=engine)

# Setup database query tracing
setup_sqlalchemy_tracing(engine)

# Setup Celery tracing
setup_celery_tracing()


@app.on_event("startup")
async def startup():
    logger.info("Application started with OpenTelemetry tracing")
```

### 40.10 Docker Compose Configuration

```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./config/otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
    networks:
      - observability

  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger collector
    networks:
      - observability

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - observability

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - observability

networks:
  observability:
    driver: bridge

volumes:
  grafana-data:
```

### 40.11 OpenTelemetry Collector Configuration

```yaml
# config/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
    send_batch_max_size: 2000

  memory_limiter:
    check_interval: 1s
    limit_mib: 1000

  attributes:
    actions:
      - key: environment
        value: ${ENVIRONMENT}
        action: upsert

  filter:
    spans:
      exclude:
        match_type: regexp
        span_names:
          - "health.*"
          - "metrics.*"

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"

  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, attributes]
      exporters: [jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

### 40.12 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Meaningful Span Names | Use descriptive names: `db.query.get_user`, not `span_1` |
| 2 | Add Business Context | Include tenant_id, user_id, booking_id in spans |
| 3 | Propagate Context | Always propagate trace context to downstream services |
| 4 | Sample High Volume | Use sampling for high-traffic endpoints |
| 5 | Exclude Health Checks | Don't trace health/metrics endpoints |
| 6 | Set Status Correctly | Use ERROR status for failures, OK for success |
| 7 | Record Exceptions | Always record exceptions with stack trace |
| 8 | Keep Spans Short | Don't span entire request, create child spans |

---

## Standard #41: Secrets & Configuration Management

### 41.1 Overview

Secrets & Configuration Management memastikan credentials dan konfigurasi aplikasi dikelola dengan aman. Menggunakan kombinasi environment variables, encrypted files, dan secrets manager untuk berbagai environment.

### 41.2 Configuration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CONFIGURATION ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CONFIGURATION LAYERS                          │   │
│  │                                                                   │   │
│  │  Priority (High to Low):                                         │   │
│  │  1. Environment Variables (runtime override)                     │   │
│  │  2. Secrets Manager (HashiCorp Vault / AWS SSM)                 │   │
│  │  3. Config Files (.env.{environment})                           │   │
│  │  4. Default Values (in code)                                    │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SECRETS CATEGORIES                             │   │
│  │                                                                   │   │
│  │  CRITICAL (Vault/SSM):         SENSITIVE (Encrypted .env):       │   │
│  │  - Database credentials         - API keys (3rd party)           │   │
│  │  - JWT signing keys             - SMTP credentials               │   │
│  │  - Encryption keys              - Storage credentials             │   │
│  │  - Master passwords             - Service tokens                  │   │
│  │                                                                   │   │
│  │  CONFIGURATION (Plain .env):   DEFAULTS (Code):                  │   │
│  │  - Feature flags                - Timeouts                        │   │
│  │  - Service URLs                 - Retry counts                    │   │
│  │  - Log levels                   - Cache TTLs                      │   │
│  │  - Rate limits                  - Pagination limits               │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 41.3 Configuration Schema

```python
# shared/config/schema.py
from pydantic import BaseSettings, Field, validator, SecretStr
from typing import Optional, List
from enum import Enum
import os


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(..., env="DB_NAME")
    user: str = Field(..., env="DB_USER")
    password: SecretStr = Field(..., env="DB_PASSWORD")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"

    class Config:
        env_prefix = ""


class RedisConfig(BaseSettings):
    """Redis configuration"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    ssl: bool = Field(default=False, env="REDIS_SSL")

    @property
    def url(self) -> str:
        auth = f":{self.password.get_secret_value()}@" if self.password else ""
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = ""


class JWTConfig(BaseSettings):
    """JWT configuration"""
    secret_key: SecretStr = Field(..., env="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_EXPIRE_DAYS")

    class Config:
        env_prefix = ""


class StorageConfig(BaseSettings):
    """Object storage configuration"""
    provider: str = Field(default="r2", env="STORAGE_PROVIDER")  # r2, s3, local
    bucket: str = Field(..., env="STORAGE_BUCKET")
    access_key: SecretStr = Field(..., env="STORAGE_ACCESS_KEY")
    secret_key: SecretStr = Field(..., env="STORAGE_SECRET_KEY")
    endpoint_url: Optional[str] = Field(default=None, env="STORAGE_ENDPOINT_URL")
    public_url: Optional[str] = Field(default=None, env="STORAGE_PUBLIC_URL")

    class Config:
        env_prefix = ""


class EmailConfig(BaseSettings):
    """Email/SMTP configuration"""
    provider: str = Field(default="smtp", env="EMAIL_PROVIDER")  # smtp, sendgrid, ses
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[SecretStr] = Field(default=None, env="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    from_email: str = Field(..., env="EMAIL_FROM")
    from_name: str = Field(default="Hotel PMS", env="EMAIL_FROM_NAME")

    # SendGrid
    sendgrid_api_key: Optional[SecretStr] = Field(default=None, env="SENDGRID_API_KEY")

    class Config:
        env_prefix = ""


class AppConfig(BaseSettings):
    """Main application configuration"""

    # App info
    name: str = Field(default="Hotel PMS", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")

    # Security
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json, text

    # Feature flags
    feature_flags_enabled: bool = Field(default=True, env="FEATURE_FLAGS_ENABLED")

    # Observability
    otel_enabled: bool = Field(default=True, env="OTEL_ENABLED")
    otel_endpoint: str = Field(default="http://otel-collector:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")

    # Sub-configs
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JWTConfig = JWTConfig()
    storage: StorageConfig = StorageConfig()
    email: EmailConfig = EmailConfig()

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get application configuration (singleton)"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config():
    """Reload configuration (for testing)"""
    global _config
    _config = None
    return get_config()
```

### 41.4 Secrets Manager Integration

```python
# shared/config/secrets.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)


@dataclass
class Secret:
    """Secret value with metadata"""
    key: str
    value: str
    version: Optional[str] = None
    expires_at: Optional[str] = None


class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""

    @abstractmethod
    async def get_secret(self, key: str) -> Optional[Secret]:
        pass

    @abstractmethod
    async def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        pass

    @abstractmethod
    async def delete_secret(self, key: str) -> bool:
        pass

    @abstractmethod
    async def list_secrets(self, prefix: Optional[str] = None) -> list[str]:
        pass


class HashiCorpVaultProvider(SecretsProvider):
    """HashiCorp Vault secrets provider"""

    def __init__(
        self,
        vault_addr: str,
        vault_token: str,
        mount_path: str = "secret",
        namespace: Optional[str] = None
    ):
        self.vault_addr = vault_addr.rstrip("/")
        self.vault_token = vault_token
        self.mount_path = mount_path
        self.namespace = namespace
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"X-Vault-Token": self.vault_token}
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.vault_addr,
                headers=self.headers,
                timeout=30.0
            )
        return self._client

    async def get_secret(self, key: str) -> Optional[Secret]:
        """Get secret from Vault KV v2"""
        client = await self._get_client()

        try:
            response = await client.get(
                f"/v1/{self.mount_path}/data/{key}"
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            secret_data = data["data"]["data"]
            metadata = data["data"]["metadata"]

            # Assume secret has a "value" key
            return Secret(
                key=key,
                value=secret_data.get("value", json.dumps(secret_data)),
                version=str(metadata.get("version")),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None

    async def set_secret(
        self,
        key: str,
        value: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Set secret in Vault KV v2"""
        client = await self._get_client()

        try:
            response = await client.post(
                f"/v1/{self.mount_path}/data/{key}",
                json={
                    "data": {"value": value, **(metadata or {})}
                }
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False

    async def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault"""
        client = await self._get_client()

        try:
            response = await client.delete(
                f"/v1/{self.mount_path}/metadata/{key}"
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            return False

    async def list_secrets(self, prefix: Optional[str] = None) -> list[str]:
        """List secrets in Vault"""
        client = await self._get_client()
        path = f"/v1/{self.mount_path}/metadata/{prefix or ''}"

        try:
            response = await client.request("LIST", path)

            if response.status_code == 404:
                return []

            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("keys", [])

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list secrets: {e}")
            return []

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None


class EnvironmentSecretsProvider(SecretsProvider):
    """Environment variables secrets provider (for development)"""

    def __init__(self, prefix: str = "SECRET_"):
        self.prefix = prefix

    async def get_secret(self, key: str) -> Optional[Secret]:
        env_key = f"{self.prefix}{key.upper().replace('/', '_')}"
        value = os.environ.get(env_key)

        if value is None:
            return None

        return Secret(key=key, value=value)

    async def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        env_key = f"{self.prefix}{key.upper().replace('/', '_')}"
        os.environ[env_key] = value
        return True

    async def delete_secret(self, key: str) -> bool:
        env_key = f"{self.prefix}{key.upper().replace('/', '_')}"
        if env_key in os.environ:
            del os.environ[env_key]
            return True
        return False

    async def list_secrets(self, prefix: Optional[str] = None) -> list[str]:
        secrets = []
        search_prefix = f"{self.prefix}{prefix.upper().replace('/', '_')}" if prefix else self.prefix

        for key in os.environ:
            if key.startswith(search_prefix):
                secret_key = key[len(self.prefix):].lower().replace("_", "/")
                secrets.append(secret_key)

        return secrets


class SecretsManager:
    """Unified secrets manager with caching"""

    def __init__(self, provider: SecretsProvider, cache_ttl: int = 300):
        self.provider = provider
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Secret, float]] = {}

    async def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value with caching"""
        import time

        # Check cache
        if key in self._cache:
            secret, cached_at = self._cache[key]
            if time.time() - cached_at < self.cache_ttl:
                return secret.value

        # Fetch from provider
        secret = await self.provider.get_secret(key)

        if secret:
            self._cache[key] = (secret, time.time())
            return secret.value

        return default

    async def get_required(self, key: str) -> str:
        """Get required secret (raises if not found)"""
        value = await self.get(key)
        if value is None:
            raise ValueError(f"Required secret not found: {key}")
        return value

    async def set(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Set secret value"""
        success = await self.provider.set_secret(key, value, metadata)

        if success:
            # Invalidate cache
            self._cache.pop(key, None)

        return success

    async def delete(self, key: str) -> bool:
        """Delete secret"""
        success = await self.provider.delete_secret(key)

        if success:
            self._cache.pop(key, None)

        return success

    def invalidate_cache(self, key: Optional[str] = None):
        """Invalidate cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()


# Factory function
def create_secrets_manager() -> SecretsManager:
    """Create secrets manager based on environment"""

    env = os.getenv("APP_ENV", "development")

    if env == "production":
        # Use Vault in production
        provider = HashiCorpVaultProvider(
            vault_addr=os.getenv("VAULT_ADDR", "http://vault:8200"),
            vault_token=os.getenv("VAULT_TOKEN", ""),
            mount_path=os.getenv("VAULT_MOUNT_PATH", "secret"),
            namespace=os.getenv("VAULT_NAMESPACE"),
        )
    else:
        # Use environment variables in development
        provider = EnvironmentSecretsProvider()

    return SecretsManager(provider)
```

### 41.5 Environment Files Structure

```bash
# .env.example - Template for environment variables
# Copy to .env and fill in values

# ==================== APPLICATION ====================
APP_NAME=hotel-pms
APP_ENV=development  # development, staging, production
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000
WORKERS=4

# ==================== DATABASE ====================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hotel_pms
DB_USER=postgres
DB_PASSWORD=  # REQUIRED - set in secrets manager for production
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ==================== REDIS ====================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional
REDIS_DB=0
REDIS_SSL=false

# ==================== JWT ====================
JWT_SECRET_KEY=  # REQUIRED - generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# ==================== STORAGE (Cloudflare R2) ====================
STORAGE_PROVIDER=r2
STORAGE_BUCKET=hotel-pms-files
STORAGE_ACCESS_KEY=  # REQUIRED
STORAGE_SECRET_KEY=  # REQUIRED
STORAGE_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
STORAGE_PUBLIC_URL=https://files.example.com

# ==================== EMAIL ====================
EMAIL_PROVIDER=smtp  # smtp, sendgrid, ses
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=Hotel PMS

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_TLS=true

# SendGrid (alternative)
SENDGRID_API_KEY=

# ==================== CORS ====================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ALLOWED_HOSTS=*

# ==================== LOGGING ====================
LOG_LEVEL=INFO
LOG_FORMAT=json  # json, text

# ==================== OBSERVABILITY ====================
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# ==================== SECRETS MANAGER ====================
# For production - HashiCorp Vault
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=
VAULT_MOUNT_PATH=secret
VAULT_NAMESPACE=

# ==================== FEATURE FLAGS ====================
FEATURE_FLAGS_ENABLED=true
```

### 41.6 Docker Secrets Integration

```yaml
# docker-compose.yml with secrets
version: '3.8'

services:
  backend-api:
    image: hotel-pms-backend:latest
    environment:
      - APP_ENV=production
      - DB_HOST=postgres
      - DB_NAME=hotel_pms
      - DB_USER_FILE=/run/secrets/db_user
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
      - STORAGE_ACCESS_KEY_FILE=/run/secrets/storage_access_key
      - STORAGE_SECRET_KEY_FILE=/run/secrets/storage_secret_key
    secrets:
      - db_user
      - db_password
      - jwt_secret
      - storage_access_key
      - storage_secret_key
    deploy:
      replicas: 3

secrets:
  db_user:
    external: true
  db_password:
    external: true
  jwt_secret:
    external: true
  storage_access_key:
    external: true
  storage_secret_key:
    external: true
```

```python
# shared/config/docker_secrets.py
import os
from typing import Optional


def get_secret_from_file_or_env(
    env_var: str,
    file_env_var: Optional[str] = None,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Get secret from Docker secret file or environment variable.
    Docker secrets are mounted as files in /run/secrets/
    """

    # Try file first (Docker secrets)
    file_path = os.environ.get(file_env_var or f"{env_var}_FILE")

    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()

    # Fall back to environment variable
    return os.environ.get(env_var, default)


class DockerSecretsConfig:
    """Configuration loader that supports Docker secrets"""

    @staticmethod
    def get_db_password() -> str:
        return get_secret_from_file_or_env("DB_PASSWORD") or ""

    @staticmethod
    def get_jwt_secret() -> str:
        return get_secret_from_file_or_env("JWT_SECRET_KEY") or ""

    @staticmethod
    def get_storage_access_key() -> str:
        return get_secret_from_file_or_env("STORAGE_ACCESS_KEY") or ""

    @staticmethod
    def get_storage_secret_key() -> str:
        return get_secret_from_file_or_env("STORAGE_SECRET_KEY") or ""
```

### 41.7 Configuration Validation

```python
# shared/config/validation.py
from pydantic import ValidationError
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error"""

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__(f"Configuration validation failed: {errors}")


def validate_config_on_startup():
    """Validate configuration on application startup"""
    from .schema import AppConfig

    errors = []

    try:
        config = AppConfig()

        # Additional business validations
        if config.environment.value == "production":
            # Production-specific validations

            if config.debug:
                errors.append({
                    "field": "debug",
                    "error": "Debug mode should be disabled in production"
                })

            if not config.jwt.secret_key.get_secret_value() or \
               len(config.jwt.secret_key.get_secret_value()) < 32:
                errors.append({
                    "field": "jwt.secret_key",
                    "error": "JWT secret key must be at least 32 characters in production"
                })

            if "localhost" in config.cors_origins or "*" in config.cors_origins:
                errors.append({
                    "field": "cors_origins",
                    "error": "Wildcard or localhost CORS origins not allowed in production"
                })

            if not config.otel_enabled:
                logger.warning("OpenTelemetry is disabled in production")

        # Validate database connection
        # (This would actually try to connect)

        if errors:
            raise ConfigValidationError(errors)

        logger.info(f"Configuration validated successfully for {config.environment.value}")
        return config

    except ValidationError as e:
        errors = [
            {"field": ".".join(str(x) for x in err["loc"]), "error": err["msg"]}
            for err in e.errors()
        ]
        raise ConfigValidationError(errors)
```

### 41.8 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Never Commit Secrets | Use .gitignore for .env files |
| 2 | Use SecretStr | Pydantic SecretStr prevents accidental logging |
| 3 | Rotate Secrets | Regular rotation for production secrets |
| 4 | Least Privilege | Minimal permissions for service accounts |
| 5 | Encrypt at Rest | Use encrypted storage for secrets |
| 6 | Audit Access | Log all secret access in production |
| 7 | Separate Environments | Different secrets per environment |
| 8 | Validate on Startup | Fail fast if required config missing |

---

## Standard #42: Scheduled Tasks & Cron Management

### 42.1 Overview

Scheduled Tasks & Cron Management menyediakan sistem terpusat untuk mengelola tugas terjadwal dengan UI monitoring, logging, dan alerting. Melengkapi Celery Beat dengan fitur management dan visibility.

### 42.2 Scheduled Tasks Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULED TASKS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      TASK SCHEDULER                               │   │
│  │                                                                   │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │   │
│  │  │ Celery Beat  │───►│ Task Queue   │───►│   Workers    │       │   │
│  │  │ (Scheduler)  │    │  (RabbitMQ)  │    │  (Celery)    │       │   │
│  │  └──────────────┘    └──────────────┘    └──────────────┘       │   │
│  │         │                                        │                │   │
│  │         ▼                                        ▼                │   │
│  │  ┌──────────────┐                        ┌──────────────┐       │   │
│  │  │  Schedule    │                        │  Execution   │       │   │
│  │  │  Database    │                        │    Logs      │       │   │
│  │  └──────────────┘                        └──────────────┘       │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MANAGEMENT FEATURES                            │   │
│  │                                                                   │   │
│  │  - Enable/Disable tasks                                           │   │
│  │  - Manual trigger                                                 │   │
│  │  - View execution history                                         │   │
│  │  - Alert on failure                                               │   │
│  │  - Schedule modification                                          │   │
│  │  - Multi-tenant support                                           │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 42.3 Database Schema

```sql
-- Scheduled task definitions
CREATE TABLE scheduled_tasks (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system task

    -- Task identification
    code VARCHAR(100) NOT NULL,  -- unique task identifier
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,  -- system, report, cleanup, sync, notification

    -- Celery task reference
    task_name VARCHAR(200) NOT NULL,  -- celery task path: tasks.reports.generate_daily
    task_args JSONB DEFAULT '[]',
    task_kwargs JSONB DEFAULT '{}',

    -- Schedule configuration
    schedule_type VARCHAR(50) NOT NULL,  -- cron, interval, one_time
    cron_expression VARCHAR(100),  -- "0 2 * * *" (daily at 2 AM)
    interval_seconds INTEGER,  -- for interval type
    run_at TIMESTAMP WITH TIME ZONE,  -- for one_time type
    timezone VARCHAR(50) DEFAULT 'Asia/Jakarta',

    -- Execution settings
    queue VARCHAR(50) DEFAULT 'scheduled',
    priority INTEGER DEFAULT 5,  -- 1-10, lower = higher priority
    timeout_seconds INTEGER DEFAULT 3600,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,  -- system tasks cannot be deleted

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT valid_schedule_type CHECK (schedule_type IN ('cron', 'interval', 'one_time')),
    CONSTRAINT valid_category CHECK (category IN (
        'system', 'report', 'cleanup', 'sync', 'notification', 'backup', 'other'
    )),
    CONSTRAINT unique_task_code UNIQUE(organization_id, code)
);

-- Task execution history
CREATE TABLE scheduled_task_executions (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    task_id INTEGER NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,

    -- Execution info
    celery_task_id VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    trigger_type VARCHAR(50) NOT NULL DEFAULT 'scheduled',  -- scheduled, manual, retry

    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 3),

    -- Result
    result JSONB,
    error_message TEXT,
    error_traceback TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Context
    triggered_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    correlation_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'running', 'success', 'failed', 'cancelled', 'timeout', 'retrying'
    )),
    CONSTRAINT valid_trigger_type CHECK (trigger_type IN ('scheduled', 'manual', 'retry'))
);

-- Task execution statistics (aggregated)
CREATE TABLE scheduled_task_stats (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    task_id INTEGER NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,

    -- Period
    period_start DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,  -- daily, weekly, monthly

    -- Statistics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    timeout_executions INTEGER DEFAULT 0,

    avg_duration_seconds NUMERIC(10, 3),
    min_duration_seconds NUMERIC(10, 3),
    max_duration_seconds NUMERIC(10, 3),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_task_period UNIQUE(task_id, period_start, period_type)
);

-- Indexes
CREATE INDEX idx_scheduled_tasks_org ON scheduled_tasks(organization_id);
CREATE INDEX idx_scheduled_tasks_active ON scheduled_tasks(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_scheduled_tasks_category ON scheduled_tasks(category);

CREATE INDEX idx_task_executions_task ON scheduled_task_executions(task_id);
CREATE INDEX idx_task_executions_status ON scheduled_task_executions(status);
CREATE INDEX idx_task_executions_scheduled ON scheduled_task_executions(scheduled_at);
CREATE INDEX idx_task_executions_org ON scheduled_task_executions(organization_id);

CREATE INDEX idx_task_stats_task ON scheduled_task_stats(task_id);
CREATE INDEX idx_task_stats_period ON scheduled_task_stats(period_start, period_type);
```

### 42.4 Task Definition Models

```python
# services/scheduler/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from shared.database import Base
from datetime import datetime
from typing import Optional


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

    # Task identification
    code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)

    # Celery task reference
    task_name = Column(String(200), nullable=False)
    task_args = Column(JSONB, default=[])
    task_kwargs = Column(JSONB, default={})

    # Schedule configuration
    schedule_type = Column(String(50), nullable=False)  # cron, interval, one_time
    cron_expression = Column(String(100))
    interval_seconds = Column(Integer)
    run_at = Column(DateTime(timezone=True))
    timezone = Column(String(50), default="Asia/Jakarta")

    # Execution settings
    queue = Column(String(50), default="scheduled")
    priority = Column(Integer, default=5)
    timeout_seconds = Column(Integer, default=3600)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Relationships
    executions = relationship("ScheduledTaskExecution", back_populates="task")
    organization = relationship("Organization")
    created_by = relationship("User")


class ScheduledTaskExecution(Base):
    __tablename__ = "scheduled_task_executions"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

    # Execution info
    celery_task_id = Column(String(100))
    status = Column(String(50), nullable=False, default="pending")
    trigger_type = Column(String(50), nullable=False, default="scheduled")

    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Numeric(10, 3))

    # Result
    result = Column(JSONB)
    error_message = Column(Text)
    error_traceback = Column(Text)
    retry_count = Column(Integer, default=0)

    # Context
    triggered_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    correlation_id = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("ScheduledTask", back_populates="executions")
    triggered_by = relationship("User")
```

### 42.5 Scheduler Service

```python
# services/scheduler/service.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from croniter import croniter
import pytz
import logging

from .models import ScheduledTask, ScheduledTaskExecution
from .repository import ScheduledTaskRepository, TaskExecutionRepository
from shared.observability.context import traced, get_correlation_id

logger = logging.getLogger(__name__)


@dataclass
class TaskExecutionResult:
    success: bool
    execution_id: int
    celery_task_id: Optional[str] = None
    error: Optional[str] = None


class SchedulerService:
    """Service for managing scheduled tasks"""

    def __init__(
        self,
        task_repo: ScheduledTaskRepository,
        execution_repo: TaskExecutionRepository,
        celery_app
    ):
        self.task_repo = task_repo
        self.execution_repo = execution_repo
        self.celery_app = celery_app

    @traced(name="scheduler.create_task")
    async def create_task(
        self,
        code: str,
        name: str,
        task_name: str,
        category: str,
        schedule_type: str,
        organization_id: Optional[int] = None,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        run_at: Optional[datetime] = None,
        task_args: List[Any] = None,
        task_kwargs: Dict[str, Any] = None,
        **kwargs
    ) -> ScheduledTask:
        """Create a new scheduled task"""

        # Validate schedule
        self._validate_schedule(schedule_type, cron_expression, interval_seconds, run_at)

        task = await self.task_repo.create({
            "code": code,
            "name": name,
            "task_name": task_name,
            "category": category,
            "schedule_type": schedule_type,
            "organization_id": organization_id,
            "cron_expression": cron_expression,
            "interval_seconds": interval_seconds,
            "run_at": run_at,
            "task_args": task_args or [],
            "task_kwargs": task_kwargs or {},
            **kwargs
        })

        # Sync with Celery Beat
        await self._sync_celery_beat()

        logger.info(f"Created scheduled task: {code}")
        return task

    @traced(name="scheduler.trigger_task")
    async def trigger_task(
        self,
        task_id: int,
        user_id: Optional[int] = None,
        override_kwargs: Optional[Dict] = None
    ) -> TaskExecutionResult:
        """Manually trigger a scheduled task"""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if not task.is_active:
            raise ValueError(f"Task is not active: {task.code}")

        # Create execution record
        execution = await self.execution_repo.create({
            "task_id": task.id,
            "organization_id": task.organization_id,
            "scheduled_at": datetime.utcnow(),
            "trigger_type": "manual",
            "triggered_by_id": user_id,
            "correlation_id": get_correlation_id(),
            "status": "pending"
        })

        # Merge kwargs
        kwargs = {**task.task_kwargs, **(override_kwargs or {})}
        kwargs["_execution_id"] = execution.id
        kwargs["_correlation_id"] = get_correlation_id()

        try:
            # Send to Celery
            result = self.celery_app.send_task(
                task.task_name,
                args=task.task_args,
                kwargs=kwargs,
                queue=task.queue,
                priority=task.priority,
                soft_time_limit=task.timeout_seconds,
                time_limit=task.timeout_seconds + 60,
            )

            # Update execution with celery task ID
            await self.execution_repo.update(execution.id, {
                "celery_task_id": result.id,
                "status": "running",
                "started_at": datetime.utcnow()
            })

            logger.info(f"Triggered task {task.code}, celery_id={result.id}")

            return TaskExecutionResult(
                success=True,
                execution_id=execution.id,
                celery_task_id=result.id
            )

        except Exception as e:
            await self.execution_repo.update(execution.id, {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })

            return TaskExecutionResult(
                success=False,
                execution_id=execution.id,
                error=str(e)
            )

    @traced(name="scheduler.update_task")
    async def update_task(
        self,
        task_id: int,
        updates: Dict[str, Any]
    ) -> ScheduledTask:
        """Update scheduled task"""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.is_system:
            # System tasks have limited updateable fields
            allowed_fields = {"is_active", "cron_expression", "interval_seconds", "priority"}
            updates = {k: v for k, v in updates.items() if k in allowed_fields}

        # Validate schedule if changed
        schedule_type = updates.get("schedule_type", task.schedule_type)
        cron_expression = updates.get("cron_expression", task.cron_expression)
        interval_seconds = updates.get("interval_seconds", task.interval_seconds)
        run_at = updates.get("run_at", task.run_at)

        self._validate_schedule(schedule_type, cron_expression, interval_seconds, run_at)

        task = await self.task_repo.update(task_id, updates)

        # Sync with Celery Beat
        await self._sync_celery_beat()

        return task

    @traced(name="scheduler.enable_task")
    async def enable_task(self, task_id: int) -> ScheduledTask:
        """Enable a scheduled task"""
        return await self.update_task(task_id, {"is_active": True})

    @traced(name="scheduler.disable_task")
    async def disable_task(self, task_id: int) -> ScheduledTask:
        """Disable a scheduled task"""
        return await self.update_task(task_id, {"is_active": False})

    @traced(name="scheduler.delete_task")
    async def delete_task(self, task_id: int) -> bool:
        """Delete a scheduled task"""

        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.is_system:
            raise ValueError("Cannot delete system tasks")

        await self.task_repo.delete(task_id)
        await self._sync_celery_beat()

        return True

    async def get_next_run_time(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate next run time for a task"""

        tz = pytz.timezone(task.timezone)
        now = datetime.now(tz)

        if task.schedule_type == "cron":
            cron = croniter(task.cron_expression, now)
            return cron.get_next(datetime)

        elif task.schedule_type == "interval":
            # Get last execution
            last_execution = await self.execution_repo.get_last_execution(task.id)

            if last_execution and last_execution.scheduled_at:
                return last_execution.scheduled_at + timedelta(seconds=task.interval_seconds)
            else:
                return now + timedelta(seconds=task.interval_seconds)

        elif task.schedule_type == "one_time":
            if task.run_at and task.run_at > now:
                return task.run_at
            return None

        return None

    async def get_execution_stats(
        self,
        task_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get execution statistics for a task"""

        since = datetime.utcnow() - timedelta(days=days)
        executions = await self.execution_repo.get_by_task(task_id, since=since)

        total = len(executions)
        successful = sum(1 for e in executions if e.status == "success")
        failed = sum(1 for e in executions if e.status == "failed")

        durations = [
            float(e.duration_seconds)
            for e in executions
            if e.duration_seconds is not None
        ]

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
        }

    def _validate_schedule(
        self,
        schedule_type: str,
        cron_expression: Optional[str],
        interval_seconds: Optional[int],
        run_at: Optional[datetime]
    ):
        """Validate schedule configuration"""

        if schedule_type == "cron":
            if not cron_expression:
                raise ValueError("cron_expression required for cron schedule type")
            try:
                croniter(cron_expression)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")

        elif schedule_type == "interval":
            if not interval_seconds or interval_seconds < 60:
                raise ValueError("interval_seconds must be at least 60 for interval schedule type")

        elif schedule_type == "one_time":
            if not run_at:
                raise ValueError("run_at required for one_time schedule type")
            if run_at <= datetime.utcnow():
                raise ValueError("run_at must be in the future")

    async def _sync_celery_beat(self):
        """Sync task schedules with Celery Beat database"""
        # This would update the Celery Beat database scheduler
        # Implementation depends on Celery Beat backend (database, redis, etc.)
        pass
```

### 42.6 Task Execution Handler

```python
# services/scheduler/task_handler.py
from celery import shared_task, Task
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
import logging

from shared.database import get_db_sync
from .repository import TaskExecutionRepository

logger = logging.getLogger(__name__)


class ScheduledTaskBase(Task):
    """Base class for scheduled tasks with automatic tracking"""

    def before_start(self, task_id, args, kwargs):
        """Called before task starts"""
        execution_id = kwargs.pop("_execution_id", None)
        correlation_id = kwargs.pop("_correlation_id", None)

        self.execution_id = execution_id
        self.correlation_id = correlation_id
        self.start_time = datetime.utcnow()

        if execution_id:
            with get_db_sync() as db:
                repo = TaskExecutionRepository(db)
                repo.update_sync(execution_id, {
                    "status": "running",
                    "started_at": self.start_time,
                    "celery_task_id": task_id
                })

    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success"""
        if hasattr(self, "execution_id") and self.execution_id:
            duration = (datetime.utcnow() - self.start_time).total_seconds()

            with get_db_sync() as db:
                repo = TaskExecutionRepository(db)
                repo.update_sync(self.execution_id, {
                    "status": "success",
                    "completed_at": datetime.utcnow(),
                    "duration_seconds": duration,
                    "result": retval if isinstance(retval, dict) else {"result": str(retval)}
                })

            logger.info(f"Task {self.name} completed successfully in {duration:.2f}s")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        if hasattr(self, "execution_id") and self.execution_id:
            duration = (datetime.utcnow() - self.start_time).total_seconds()

            with get_db_sync() as db:
                repo = TaskExecutionRepository(db)
                repo.update_sync(self.execution_id, {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "duration_seconds": duration,
                    "error_message": str(exc),
                    "error_traceback": traceback.format_exc(),
                    "retry_count": self.request.retries
                })

            logger.error(f"Task {self.name} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called on task retry"""
        if hasattr(self, "execution_id") and self.execution_id:
            with get_db_sync() as db:
                repo = TaskExecutionRepository(db)
                repo.update_sync(self.execution_id, {
                    "status": "retrying",
                    "retry_count": self.request.retries,
                    "error_message": str(exc)
                })

            logger.warning(f"Task {self.name} retrying (attempt {self.request.retries}): {exc}")


# Example scheduled tasks
@shared_task(
    bind=True,
    base=ScheduledTaskBase,
    name="scheduled.cleanup_expired_sessions",
    queue="scheduled",
    max_retries=3
)
def cleanup_expired_sessions(self):
    """Clean up expired user sessions"""
    from services.auth.service import AuthService

    with get_db_sync() as db:
        service = AuthService(db)
        deleted_count = service.cleanup_expired_sessions_sync()

    return {"deleted_sessions": deleted_count}


@shared_task(
    bind=True,
    base=ScheduledTaskBase,
    name="scheduled.generate_daily_reports",
    queue="scheduled",
    max_retries=3
)
def generate_daily_reports(self, organization_id: int = None):
    """Generate daily reports for all or specific organization"""
    from services.reports.service import ReportService

    with get_db_sync() as db:
        service = ReportService(db)

        if organization_id:
            reports = service.generate_daily_sync(organization_id)
        else:
            reports = service.generate_daily_all_sync()

    return {"generated_reports": len(reports)}


@shared_task(
    bind=True,
    base=ScheduledTaskBase,
    name="scheduled.sync_external_rates",
    queue="scheduled",
    max_retries=3
)
def sync_external_rates(self, organization_id: int):
    """Sync room rates from external channel manager"""
    from services.rates.service import RatesService

    with get_db_sync() as db:
        service = RatesService(db)
        result = service.sync_external_sync(organization_id)

    return result
```

### 42.7 API Endpoints

```python
# services/scheduler/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from shared.auth.dependencies import get_current_user, require_permission
from .service import SchedulerService
from .schemas import (
    ScheduledTaskCreate, ScheduledTaskUpdate, ScheduledTaskResponse,
    TaskExecutionResponse, TaskStatsResponse, TriggerTaskRequest
)

router = APIRouter(prefix="/admin/scheduled-tasks", tags=["Scheduled Tasks"])


@router.get("", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    organization_id: Optional[int] = None,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.view")),
    scheduler: SchedulerService = Depends()
):
    """List all scheduled tasks"""
    tasks = await scheduler.task_repo.list(
        category=category,
        is_active=is_active,
        organization_id=organization_id
    )

    # Enrich with next run time
    result = []
    for task in tasks:
        task_dict = ScheduledTaskResponse.from_orm(task).dict()
        task_dict["next_run_at"] = await scheduler.get_next_run_time(task)
        result.append(task_dict)

    return result


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.view")),
    scheduler: SchedulerService = Depends()
):
    """Get scheduled task details"""
    task = await scheduler.task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(404, "Task not found")

    response = ScheduledTaskResponse.from_orm(task)
    response.next_run_at = await scheduler.get_next_run_time(task)

    return response


@router.post("", response_model=ScheduledTaskResponse)
async def create_scheduled_task(
    request: ScheduledTaskCreate,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.create")),
    scheduler: SchedulerService = Depends()
):
    """Create a new scheduled task"""
    task = await scheduler.create_task(
        **request.dict(),
        created_by_id=current_user.id
    )

    return ScheduledTaskResponse.from_orm(task)


@router.patch("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    request: ScheduledTaskUpdate,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.update")),
    scheduler: SchedulerService = Depends()
):
    """Update scheduled task"""
    task = await scheduler.update_task(
        task_id,
        request.dict(exclude_unset=True)
    )

    return ScheduledTaskResponse.from_orm(task)


@router.post("/{task_id}/enable")
async def enable_task(
    task_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.update")),
    scheduler: SchedulerService = Depends()
):
    """Enable a scheduled task"""
    await scheduler.enable_task(task_id)
    return {"success": True, "message": "Task enabled"}


@router.post("/{task_id}/disable")
async def disable_task(
    task_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.update")),
    scheduler: SchedulerService = Depends()
):
    """Disable a scheduled task"""
    await scheduler.disable_task(task_id)
    return {"success": True, "message": "Task disabled"}


@router.post("/{task_id}/trigger")
async def trigger_task(
    task_id: int,
    request: Optional[TriggerTaskRequest] = None,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.trigger")),
    scheduler: SchedulerService = Depends()
):
    """Manually trigger a scheduled task"""
    result = await scheduler.trigger_task(
        task_id,
        user_id=current_user.id,
        override_kwargs=request.kwargs if request else None
    )

    if not result.success:
        raise HTTPException(500, f"Failed to trigger task: {result.error}")

    return {
        "success": True,
        "execution_id": result.execution_id,
        "celery_task_id": result.celery_task_id
    }


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.delete")),
    scheduler: SchedulerService = Depends()
):
    """Delete a scheduled task"""
    await scheduler.delete_task(task_id)
    return {"success": True, "message": "Task deleted"}


@router.get("/{task_id}/executions", response_model=List[TaskExecutionResponse])
async def get_task_executions(
    task_id: int,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.view")),
    scheduler: SchedulerService = Depends()
):
    """Get task execution history"""
    executions = await scheduler.execution_repo.get_by_task(
        task_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return [TaskExecutionResponse.from_orm(e) for e in executions]


@router.get("/{task_id}/stats", response_model=TaskStatsResponse)
async def get_task_stats(
    task_id: int,
    days: int = Query(30, le=90),
    current_user = Depends(get_current_user),
    _: None = Depends(require_permission("admin.scheduled_tasks.view")),
    scheduler: SchedulerService = Depends()
):
    """Get task execution statistics"""
    stats = await scheduler.get_execution_stats(task_id, days=days)
    return TaskStatsResponse(**stats)
```

### 42.8 Predefined System Tasks

```python
# services/scheduler/system_tasks.py
"""Predefined system scheduled tasks"""

SYSTEM_TASKS = [
    {
        "code": "cleanup_expired_sessions",
        "name": "Cleanup Expired Sessions",
        "description": "Remove expired user sessions from database",
        "category": "cleanup",
        "task_name": "scheduled.cleanup_expired_sessions",
        "schedule_type": "cron",
        "cron_expression": "0 */6 * * *",  # Every 6 hours
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "cleanup_temp_files",
        "name": "Cleanup Temporary Files",
        "description": "Remove temporary files older than 24 hours",
        "category": "cleanup",
        "task_name": "scheduled.cleanup_temp_files",
        "schedule_type": "cron",
        "cron_expression": "0 3 * * *",  # Daily at 3 AM
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "generate_daily_reports",
        "name": "Generate Daily Reports",
        "description": "Generate daily operational reports for all organizations",
        "category": "report",
        "task_name": "scheduled.generate_daily_reports",
        "schedule_type": "cron",
        "cron_expression": "0 6 * * *",  # Daily at 6 AM
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "backup_database",
        "name": "Daily Database Backup",
        "description": "Create daily database backup",
        "category": "backup",
        "task_name": "scheduled.backup_database",
        "schedule_type": "cron",
        "cron_expression": "0 2 * * *",  # Daily at 2 AM
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "archive_old_data",
        "name": "Archive Old Data",
        "description": "Archive data older than retention period",
        "category": "cleanup",
        "task_name": "scheduled.archive_old_data",
        "schedule_type": "cron",
        "cron_expression": "0 4 * * 0",  # Weekly on Sunday at 4 AM
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "send_scheduled_notifications",
        "name": "Send Scheduled Notifications",
        "description": "Process and send scheduled notifications",
        "category": "notification",
        "task_name": "scheduled.send_scheduled_notifications",
        "schedule_type": "interval",
        "interval_seconds": 300,  # Every 5 minutes
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "update_search_index",
        "name": "Update Search Index",
        "description": "Sync database changes to Meilisearch",
        "category": "sync",
        "task_name": "scheduled.update_search_index",
        "schedule_type": "interval",
        "interval_seconds": 60,  # Every minute
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "health_check_external",
        "name": "External Services Health Check",
        "description": "Check health of external services and APIs",
        "category": "system",
        "task_name": "scheduled.health_check_external",
        "schedule_type": "interval",
        "interval_seconds": 300,  # Every 5 minutes
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "calculate_statistics",
        "name": "Calculate Daily Statistics",
        "description": "Calculate and cache daily statistics",
        "category": "report",
        "task_name": "scheduled.calculate_statistics",
        "schedule_type": "cron",
        "cron_expression": "30 0 * * *",  # Daily at 00:30
        "is_system": True,
        "is_active": True,
    },
    {
        "code": "expire_rate_limits",
        "name": "Expire Rate Limit Counters",
        "description": "Clean up expired rate limit counters from Redis",
        "category": "cleanup",
        "task_name": "scheduled.expire_rate_limits",
        "schedule_type": "cron",
        "cron_expression": "*/15 * * * *",  # Every 15 minutes
        "is_system": True,
        "is_active": True,
    },
]


async def seed_system_tasks(scheduler_service):
    """Seed system tasks on application startup"""
    for task_def in SYSTEM_TASKS:
        existing = await scheduler_service.task_repo.get_by_code(task_def["code"])

        if not existing:
            await scheduler_service.create_task(**task_def)
```

### 42.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Idempotent Tasks | Tasks should be safe to run multiple times |
| 2 | Proper Timeouts | Set reasonable timeouts to prevent hanging |
| 3 | Monitor Execution | Track success/failure rates and duration |
| 4 | Alert on Failure | Set up alerts for critical task failures |
| 5 | Stagger Schedules | Avoid scheduling all tasks at same time |
| 6 | Use Appropriate Queue | Separate queue for scheduled tasks |
| 7 | Log Execution | Log start, completion, and errors |
| 8 | Handle Overlap | Prevent concurrent execution of same task |

---

## Summary

| Standard | Key Points |
|----------|------------|
| #40 Distributed Tracing | OpenTelemetry integration, context propagation, span management |
| #41 Secrets & Configuration | Pydantic settings, Vault integration, Docker secrets |
| #42 Scheduled Tasks | Celery Beat with UI, execution tracking, system tasks |

---

*Last Updated: 2025-12-09*
