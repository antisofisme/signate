# Development Standards V17

> Standards #43 untuk Structured Logging & Observability

**Related Documents:**
- [STD-11: Distributed Tracing](./STD-11-tracing-secrets-tasks.md#standard-40-distributed-tracing-opentelemetry) - OpenTelemetry tracing
- [STD-10: Health & Monitoring](./STD-10-circuit-health-archival.md) - Health checks & monitoring
- [STD-01: Error Handling](./STD-01-core-naming-db-rbac-api.md#75-error-logging) - Error handling patterns

---

## Table of Contents

- [Standard #43: Structured Logging](#standard-43-structured-logging)
  - [43.1 Overview](#431-overview)
  - [43.2 Core Principles](#432-core-principles)
  - [43.3 Global Log Schema](#433-global-log-schema)
  - [43.4 Layer Logging](#434-layer-logging)
  - [43.5 Log Levels](#435-log-levels)
  - [43.6 Implementation](#436-implementation)
  - [43.7 Filtering & Querying](#437-filtering--querying)
  - [43.8 Retention & Security](#438-retention--security)
  - [43.9 Log vs Metric vs Trace](#439-log-vs-metric-vs-trace)
  - [43.10 Best Practices](#4310-best-practices)

---

## Standard #43: Structured Logging

### 43.1 Overview

**Purpose:**
Logging adalah **arsitektur fundamental** untuk observability, bukan fitur tambahan. Sistem logging yang baik memungkinkan:
1. **Debug operasional** - Kenapa fitur gagal
2. **Audit & compliance** - Siapa melakukan apa, kapan
3. **Tracing transaksi** - Follow flow lintas modul
4. **Alerting otomatis** - Deteksi anomali & error

**Key Insight:**
> Satu log boleh melayani >1 tujuan, **tapi desainnya harus sadar tujuan**.

**Architecture Principle:**
```
╔═══════════════════════════════════════════════════════════════════════════╗
║  LOGGING ARCHITECTURE PRINCIPLE                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  Logging bukan hanya error tracking                                      ║
║  Logging adalah sistem observability yang:                               ║
║  • Structured (parseable & queryable)                                    ║
║  • Contextual (tenant, user, request aware)                              ║
║  • Multi-purpose (debug, audit, trace, alert)                            ║
║  • Secure (no sensitive data)                                            ║
║  • Scalable (efficient storage & querying)                               ║
║                                                                           ║
║  Tool tidak menyelamatkan desain yang salah                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 43.2 Core Principles

**Aturan Keras (TIDAK BOLEH DILANGGAR):**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CORE LOGGING PRINCIPLES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. STRUCTURED LOGS ONLY (JSON)                                         │
│     ✅ logger.info("user_login", extra={"user_id": "123"})             │
│     ❌ logger.info("User 123 logged in")                               │
│                                                                         │
│  2. NO FREE-FORM STRING LOGS                                            │
│     ✅ Event-based with structured data                                │
│     ❌ Human-readable sentences without structure                      │
│                                                                         │
│  3. ALWAYS INCLUDE CONTEXT                                              │
│     ✅ tenant_id, user_id, request_id, trace_id                        │
│     ❌ Logs without context (siapa? di tenant mana?)                   │
│                                                                         │
│  4. NEVER LOG SENSITIVE DATA                                            │
│     ❌ Password, token, KTP, credit card, PAN                          │
│     ✅ Hashed/masked values if needed                                  │
│                                                                         │
│  5. NO print() / console.log()                                          │
│     ❌ print(f"Debug: {value}")                                        │
│     ❌ console.log("Something happened")                               │
│     ✅ Use proper logger with structure                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Consequence:**
> Jika prinsip ini dilanggar → observability rusak. Kode dianggap **salah meski berjalan**.

---

### 43.3 Global Log Schema

**Kontrak Wajib Semua Modul:**

Semua log di sistem **HARUS** mengikuti schema ini:

```json
{
  "timestamp": "2024-12-23T10:30:45.123Z",
  "level": "INFO",
  "env": "production",

  "module": "pms",
  "service": "pms-reservation",
  "version": "2.5.3",

  "tenant_id": "tenant_abc123",
  "user_id": "user_xyz789",
  "membership_id": "mem_456def",

  "request_id": "req_unique_123",
  "trace_id": "trace_abc123",
  "span_id": "span_456def",

  "event": "reservation_created",
  "action": "create_reservation",

  "entity": {
    "type": "reservation",
    "id": "rsv_789ghi"
  },

  "message": "Reservation created successfully",

  "error": {
    "code": "PMS_ROOM_OCCUPIED",
    "message": "Room already occupied for selected dates",
    "stack": "..."
  },

  "meta": {
    "source": "api",
    "ip": "hashed_ip_value",
    "user_agent": "PostmanRuntime/7.32.1",
    "duration_ms": 234
  }
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | ISO-8601 string | ✅ | Timestamp with timezone |
| `level` | Enum | ✅ | TRACE, DEBUG, INFO, WARN, ERROR, FATAL |
| `env` | String | ✅ | dev, staging, production |
| `module` | String | ✅ | Module code (pms, acc, inv, etc) |
| `service` | String | ✅ | Service name (microservice identifier) |
| `version` | String | ✅ | Service version (semver) |
| `tenant_id` | UUID/String | ⚠️ | Required if in tenant context |
| `user_id` | UUID/String | Optional | User performing action |
| `membership_id` | UUID/String | Optional | Membership ID if applicable |
| `request_id` | UUID | ⚠️ | Required for API requests |
| `trace_id` | UUID | ⚠️ | Required for distributed tracing |
| `span_id` | UUID | Optional | Span ID (from OpenTelemetry) |
| `event` | String | ✅ | Event name (snake_case) |
| `action` | String | Optional | Action being performed |
| `entity` | Object | Optional | Entity being operated on |
| `message` | String | ✅ | Short human-readable message |
| `error` | Object | Optional | Error details (if applicable) |
| `meta` | Object | Optional | Additional metadata |

**Field Rules:**
- ✅ Required = Must always be present
- ⚠️ Conditional = Required in certain contexts
- Optional = Nice to have

---

### 43.4 Layer Logging

Logging strategy berbeda per layer aplikasi.

#### 43.4.1 API / Request Layer

**Purpose:** Track semua request masuk & keluar

**Log Events:**
```python
# Request received
logger.info(
    "request_received",
    extra={
        "request_id": request_id,
        "method": "POST",
        "path": "/api/v1/reservations",
        "tenant_id": tenant_id,
        "user_id": user_id,
    }
)

# Request validation failed
logger.warning(
    "request_validation_failed",
    extra={
        "request_id": request_id,
        "errors": validation_errors,
        "payload": sanitized_payload  # No sensitive data!
    }
)

# Request completed
logger.info(
    "request_completed",
    extra={
        "request_id": request_id,
        "status_code": 200,
        "duration_ms": duration,
    }
)

# Unhandled exception
logger.error(
    "request_exception",
    extra={
        "request_id": request_id,
        "error": {
            "code": error_code,
            "message": str(exception),
            "stack": traceback.format_exc()
        }
    },
    exc_info=True
)
```

**Rules:**
- ✅ Selalu ada `request_id`
- ❌ Jangan log body mentah (bisa ada password/token)
- ✅ Sanitize payload sebelum log
- ✅ Log duration untuk performance monitoring

---

#### 43.4.2 Domain / Business Logic Layer

**Purpose:** Track state changes & keputusan bisnis

**Rules:**
- ✅ Hanya log **state change & keputusan bisnis penting**
- ❌ Tidak semua CRUD operation
- ✅ Log business rule violations

**Example (PMS Module):**
```python
# State change
logger.info(
    "reservation_created",
    extra={
        "tenant_id": tenant_id,
        "entity": {
            "type": "reservation",
            "id": reservation_id
        },
        "meta": {
            "room_type": room_type,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "total_amount": total_amount
        }
    }
)

# Business rule violation (warning)
logger.warning(
    "overbooking_attempt",
    extra={
        "tenant_id": tenant_id,
        "room_type": room_type,
        "requested_rooms": 5,
        "available_rooms": 3,
        "action_taken": "partial_booking"
    }
)

# Business operation failed
logger.error(
    "checkin_failed",
    extra={
        "tenant_id": tenant_id,
        "reservation_id": reservation_id,
        "error": {
            "code": "PMS_PAYMENT_PENDING",
            "message": "Cannot check-in with pending payment"
        }
    }
)
```

**Example (Accounting Module):**
```python
# Journal entry created
logger.info(
    "journal_entry_created",
    extra={
        "tenant_id": tenant_id,
        "entity": {
            "type": "journal_entry",
            "id": journal_id
        },
        "meta": {
            "period": period,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": True
        }
    }
)

# Period closing
logger.info(
    "accounting_period_closed",
    extra={
        "tenant_id": tenant_id,
        "period": period,
        "closed_by": user_id,
        "final_balance": final_balance
    }
)
```

---

#### 43.4.3 Event-Driven / Async Layer

**Purpose:** Track event publishing & consumption

Karena sistem event-driven, **wajib** log:
- Event published
- Event consumed
- Event handler success/failure

**Rules:**
- ✅ Setiap event log wajib membawa `trace_id`
- ✅ Log sebelum & sesudah handler execution
- ✅ Log retry attempts

**Example:**
```python
# Event published
logger.info(
    "event_published",
    extra={
        "trace_id": trace_id,
        "event_type": "reservation.created",
        "event_id": event_id,
        "payload": {
            "reservation_id": reservation_id,
            "tenant_id": tenant_id
        },
        "destination": "reservation_events_topic"
    }
)

# Event consumed
logger.info(
    "event_consumed",
    extra={
        "trace_id": trace_id,
        "event_type": "reservation.created",
        "event_id": event_id,
        "consumer": "accounting_service",
        "attempt": 1
    }
)

# Event handler executed successfully
logger.info(
    "event_handler_success",
    extra={
        "trace_id": trace_id,
        "event_id": event_id,
        "handler": "create_invoice_from_reservation",
        "duration_ms": duration
    }
)

# Event handler failed
logger.error(
    "event_handler_failed",
    extra={
        "trace_id": trace_id,
        "event_id": event_id,
        "handler": "create_invoice_from_reservation",
        "attempt": 2,
        "max_retries": 3,
        "error": {
            "code": "ACC_PERIOD_CLOSED",
            "message": "Cannot create invoice in closed period"
        }
    }
)
```

**Integration with Distributed Tracing:**
```python
# Use trace context from STD-11
from shared.observability.context import get_trace_context

trace_context = get_trace_context()

logger.info(
    "event_published",
    extra={
        "trace_id": trace_context.trace_id,
        "span_id": trace_context.span_id,
        # ... other fields
    }
)
```

---

#### 43.4.4 Accounting Layer (Special & Critical)

**Purpose:** Audit trail untuk compliance & legal

**Rules:**
- ✅ Accounting log = **audit trail hukum**
- ✅ Tidak boleh dihapus (long retention)
- ✅ ERROR di Accounting = **CRITICAL alert**
- ✅ Tambahan context: journal_id, period, is_reversal

**Example:**
```python
# Journal entry posted
logger.info(
    "journal_posted",
    extra={
        "tenant_id": tenant_id,
        "entity": {
            "type": "journal_entry",
            "id": journal_id
        },
        "meta": {
            "period": "2024-12",
            "journal_type": "general",
            "total_amount": 5000000,
            "posted_by": user_id,
            "posted_at": datetime.now().isoformat(),
            "is_reversal": False,
            "reference": reservation_id
        }
    }
)

# Period closed (CRITICAL event)
logger.info(
    "accounting_period_closed",
    extra={
        "tenant_id": tenant_id,
        "period": "2024-12",
        "closed_by": user_id,
        "closed_at": datetime.now().isoformat(),
        "final_trial_balance": trial_balance_summary,
        "alert_priority": "high"
    }
)

# Reversal entry (AUDIT critical)
logger.warning(
    "journal_reversed",
    extra={
        "tenant_id": tenant_id,
        "original_journal_id": original_journal_id,
        "reversal_journal_id": reversal_journal_id,
        "reversed_by": user_id,
        "reason": reversal_reason,
        "approval_id": approval_id  # Must have approval
    }
)

# Accounting error (CRITICAL)
logger.error(
    "accounting_integrity_error",
    extra={
        "tenant_id": tenant_id,
        "journal_id": journal_id,
        "error": {
            "code": "ACC_UNBALANCED_ENTRY",
            "message": "Debit and credit not balanced",
            "debit_total": debit_total,
            "credit_total": credit_total,
            "difference": abs(debit_total - credit_total)
        },
        "alert_priority": "critical"
    }
)
```

---

### 43.5 Log Levels

**Level Definitions & Rules:**

| Level | Severity | When to Use | Production? | Examples |
|-------|----------|-------------|-------------|----------|
| **TRACE** | Lowest | Granular detail (loop iterations, variable values) | ❌ Dev only | Variable assignments, function entry/exit |
| **DEBUG** | Low | Detailed logic flow, non-sensitive diagnostic info | ❌ Non-prod | Query parameters, intermediate calculations |
| **INFO** | Normal | State changes, successful operations | ✅ Yes | reservation_created, payment_completed |
| **WARN** | Elevated | Anomali tapi sistem masih jalan | ✅ Yes | overbooking_attempt, slow_query_detected |
| **ERROR** | High | Transaksi gagal, recoverable errors | ✅ Yes | payment_failed, checkin_failed |
| **FATAL** | Critical | Sistem harus dihentikan, unrecoverable | ✅ Yes | database_connection_lost, critical_service_down |

**Important Notes:**
- ❌ **ERROR ≠ Exception** - Not all exceptions are errors (e.g., validation failure = WARN)
- ❌ **WARN bukan sampah** - Use for genuine anomalies, not noise
- ✅ **Production logs** should be primarily INFO, WARN, ERROR, FATAL
- ✅ **FATAL** should trigger immediate alerts (PagerDuty, SMS, etc.)

**Level Selection Guide:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LOG LEVEL DECISION TREE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Question 1: Apakah sistem harus dihentikan?                            │
│     YES → FATAL                                                         │
│     NO  → Next question                                                 │
│                                                                         │
│  Question 2: Apakah transaksi/operasi gagal?                            │
│     YES → ERROR                                                         │
│     NO  → Next question                                                 │
│                                                                         │
│  Question 3: Apakah ada anomali/kondisi tidak ideal?                    │
│     YES → WARN                                                          │
│     NO  → Next question                                                 │
│                                                                         │
│  Question 4: Apakah ini state change/operasi penting?                   │
│     YES → INFO                                                          │
│     NO  → Next question                                                 │
│                                                                         │
│  Question 5: Apakah ini detail untuk debugging?                         │
│     YES → DEBUG (non-prod) atau TRACE (dev only)                       │
│     NO  → Jangan log (noise)                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 43.6 Implementation

#### 43.6.1 Backend (Python) Implementation

**Logger Setup:**
```python
# shared/logging/config.py
import logging
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that enforces global log schema.
    """
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Enforce timestamp format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add level
        log_record['level'] = record.levelname

        # Add environment
        log_record['env'] = os.getenv('ENVIRONMENT', 'development')

        # Ensure message exists
        if not log_record.get('message'):
            log_record['message'] = record.getMessage()

        # Move extra fields to root level (not nested under 'extra')
        if 'extra' in message_dict:
            for key, value in message_dict['extra'].items():
                log_record[key] = value

def setup_logging(
    module: str,
    service: str,
    version: str,
    level: str = "INFO"
) -> logging.Logger:
    """
    Setup structured logging for a service.

    Args:
        module: Module code (pms, acc, inv, etc)
        service: Service name
        version: Service version
        level: Log level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(service)
    logger.setLevel(getattr(logging, level.upper()))

    # JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(message)s',
        reserved_attrs=['name', 'args', 'created', 'filename', 'funcName',
                       'levelname', 'levelno', 'lineno', 'module', 'msecs',
                       'pathname', 'process', 'processName', 'relativeCreated',
                       'thread', 'threadName']
    )

    # Console handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add default context
    logger = logging.LoggerAdapter(logger, {
        'module': module,
        'service': service,
        'version': version
    })

    return logger

# Initialize logger per service
logger = setup_logging(
    module="pms",
    service="pms-reservation",
    version="2.5.3"
)
```

**Context Manager for Request Logging:**
```python
# shared/logging/context.py
from contextvars import ContextVar
from typing import Optional
import uuid

# Context variables
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_tenant_id: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

class LogContext:
    """Context manager for logging context."""

    @staticmethod
    def set_request_context(
        request_id: str = None,
        tenant_id: str = None,
        user_id: str = None,
        trace_id: str = None
    ):
        """Set logging context for current request."""
        if request_id:
            _request_id.set(request_id)
        if tenant_id:
            _tenant_id.set(tenant_id)
        if user_id:
            _user_id.set(user_id)
        if trace_id:
            _trace_id.set(trace_id)

    @staticmethod
    def get_context() -> dict:
        """Get current logging context."""
        return {
            'request_id': _request_id.get(),
            'tenant_id': _tenant_id.get(),
            'user_id': _user_id.get(),
            'trace_id': _trace_id.get()
        }

    @staticmethod
    def clear():
        """Clear logging context."""
        _request_id.set(None)
        _tenant_id.set(None)
        _user_id.set(None)
        _trace_id.set(None)

def get_logger_with_context(logger):
    """
    Get logger with current context automatically included.
    """
    context = LogContext.get_context()
    return logging.LoggerAdapter(logger, context)
```

**FastAPI Middleware:**
```python
# shared/logging/middleware.py
from fastapi import Request
import uuid
import time

async def logging_middleware(request: Request, call_next):
    """
    Middleware to add logging context to all requests.
    """
    # Generate request ID
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    # Extract tenant & user from request
    tenant_id = getattr(request.state, 'tenant_id', None)
    user_id = getattr(request.state, 'user_id', None)

    # Get or create trace ID
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))

    # Set logging context
    LogContext.set_request_context(
        request_id=request_id,
        tenant_id=tenant_id,
        user_id=user_id,
        trace_id=trace_id
    )

    # Log request received
    logger = get_logger_with_context(base_logger)
    logger.info(
        "request_received",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params)
        }
    )

    # Process request
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Log request completed
        logger.info(
            "request_completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }
        )

        # Add headers
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Trace-ID'] = trace_id

        return response

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        # Log exception
        logger.error(
            "request_exception",
            extra={
                "error": {
                    "code": getattr(e, 'code', 'INTERNAL_ERROR'),
                    "message": str(e)
                },
                "duration_ms": duration_ms
            },
            exc_info=True
        )
        raise

    finally:
        # Clear context
        LogContext.clear()
```

**Usage in Business Logic:**
```python
# services/pms/reservation_service.py
from shared.logging.config import logger
from shared.logging.context import get_logger_with_context

class ReservationService:
    def __init__(self):
        self.logger = get_logger_with_context(logger)

    def create_reservation(self, data: dict, tenant_id: str, user_id: str):
        """Create a new reservation."""

        # Business logic
        reservation = Reservation(**data)
        reservation.tenant_id = tenant_id

        # Validate availability
        if not self._check_availability(reservation):
            self.logger.warning(
                "overbooking_attempt",
                extra={
                    "room_type": reservation.room_type,
                    "requested_rooms": reservation.room_count,
                    "available_rooms": available_count
                }
            )
            raise BusinessError("ROOM_NOT_AVAILABLE")

        # Save reservation
        db.session.add(reservation)
        db.session.commit()

        # Log state change
        self.logger.info(
            "reservation_created",
            extra={
                "entity": {
                    "type": "reservation",
                    "id": str(reservation.id)
                },
                "meta": {
                    "room_type": reservation.room_type,
                    "check_in": reservation.check_in.isoformat(),
                    "check_out": reservation.check_out.isoformat(),
                    "total_amount": float(reservation.total_amount)
                }
            }
        )

        # Publish event
        self._publish_event("reservation.created", reservation)

        return reservation
```

#### 43.6.2 Frontend (TypeScript) Implementation

**Logger Setup:**
```typescript
// lib/logging/logger.ts
type LogLevel = 'TRACE' | 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  env: string;
  module: string;
  service: string;
  version: string;
  tenant_id?: string;
  user_id?: string;
  request_id?: string;
  trace_id?: string;
  event: string;
  message: string;
  meta?: Record<string, any>;
  error?: {
    code?: string;
    message: string;
    stack?: string;
  };
}

class Logger {
  private module: string;
  private service: string;
  private version: string;
  private context: Record<string, any> = {};

  constructor(module: string, service: string, version: string) {
    this.module = module;
    this.service = service;
    this.version = version;
  }

  setContext(context: Record<string, any>) {
    this.context = { ...this.context, ...context };
  }

  clearContext() {
    this.context = {};
  }

  private log(level: LogLevel, event: string, message: string, extra?: Record<string, any>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      env: process.env.NODE_ENV || 'development',
      module: this.module,
      service: this.service,
      version: this.version,
      event,
      message,
      ...this.context,
      ...extra,
    };

    // Send to logging service (e.g., Sentry, LogRocket, or custom endpoint)
    this.sendToLoggingService(entry);

    // Also log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(JSON.stringify(entry, null, 2));
    }
  }

  private sendToLoggingService(entry: LogEntry) {
    // Send to backend logging endpoint
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      fetch('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
        keepalive: true, // Ensure log is sent even if page unloads
      }).catch(() => {
        // Silently fail - don't break app if logging fails
      });
    }
  }

  trace(event: string, message: string, extra?: Record<string, any>) {
    this.log('TRACE', event, message, extra);
  }

  debug(event: string, message: string, extra?: Record<string, any>) {
    this.log('DEBUG', event, message, extra);
  }

  info(event: string, message: string, extra?: Record<string, any>) {
    this.log('INFO', event, message, extra);
  }

  warn(event: string, message: string, extra?: Record<string, any>) {
    this.log('WARN', event, message, extra);
  }

  error(event: string, message: string, error?: Error, extra?: Record<string, any>) {
    this.log('ERROR', event, message, {
      ...extra,
      error: {
        code: (error as any)?.code,
        message: error?.message || message,
        stack: error?.stack,
      },
    });
  }

  fatal(event: string, message: string, error?: Error, extra?: Record<string, any>) {
    this.log('FATAL', event, message, {
      ...extra,
      error: {
        code: (error as any)?.code,
        message: error?.message || message,
        stack: error?.stack,
      },
    });
  }
}

// Export singleton instance
export const logger = new Logger('pms', 'pms-frontend', '2.5.3');
```

**Usage in React:**
```typescript
// hooks/useLogger.ts
import { useEffect } from 'react';
import { logger } from '@/lib/logging/logger';
import { useAuth } from '@/contexts/AuthContext';

export function useLogger() {
  const { user, tenant } = useAuth();

  useEffect(() => {
    // Set context when user/tenant changes
    logger.setContext({
      tenant_id: tenant?.id,
      user_id: user?.id,
    });

    return () => {
      logger.clearContext();
    };
  }, [user, tenant]);

  return logger;
}

// components/ReservationForm.tsx
import { useLogger } from '@/hooks/useLogger';

export function ReservationForm() {
  const logger = useLogger();

  const handleSubmit = async (data: ReservationData) => {
    logger.info(
      'reservation_form_submitted',
      'User submitted reservation form',
      {
        meta: {
          room_type: data.roomType,
          nights: data.nights,
        },
      }
    );

    try {
      const result = await createReservation(data);

      logger.info(
        'reservation_created_success',
        'Reservation created successfully',
        {
          entity: {
            type: 'reservation',
            id: result.id,
          },
        }
      );

      toast.success('Reservation created!');
    } catch (error) {
      logger.error(
        'reservation_creation_failed',
        'Failed to create reservation',
        error as Error,
        {
          meta: {
            room_type: data.roomType,
          },
        }
      );

      toast.error('Failed to create reservation');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
    </form>
  );
}
```

---

### 43.7 Filtering & Querying

**Multi-Layer Filtering Strategy:**

**Use Case:** Masalah di PMS module untuk hotel X

**Filter Level 1: Module & Tenant**
```sql
-- Elasticsearch/Loki query
module = "pms"
AND tenant_id = "hotel_x_tenant_id"
AND level >= "ERROR"
```

**Filter Level 2: Narrow by Event**
```sql
-- Further narrow down
AND event IN ("night_audit_failed", "checkin_failed", "payment_failed")
```

**Filter Level 3: Time Range**
```sql
-- Last 24 hours
AND timestamp >= NOW() - INTERVAL '24 hours'
```

**Filter Level 4: Specific Entity**
```sql
-- Specific reservation
AND entity.type = "reservation"
AND entity.id = "rsv_abc123"
```

**Possible karena schema konsisten!**

**Example Queries:**

**1. All errors for a specific tenant today:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "tenant_id": "tenant_abc123" }},
        { "range": { "level_num": { "gte": 40 }}}, // ERROR and above
        { "range": { "timestamp": { "gte": "now-1d/d" }}}
      ]
    }
  },
  "sort": [{ "timestamp": "desc" }]
}
```

**2. Trace a specific request across services:**
```json
{
  "query": {
    "match": { "trace_id": "trace_xyz789" }
  },
  "sort": [{ "timestamp": "asc" }]
}
```

**3. Find slow operations:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "exists": { "field": "meta.duration_ms" }},
        { "range": { "meta.duration_ms": { "gte": 1000 }}} // > 1s
      ]
    }
  }
}
```

---

### 43.8 Retention & Security

#### 43.8.1 Retention Policy

| Log Level | Retention Period | Reason |
|-----------|------------------|--------|
| TRACE | Not in production | Development only |
| DEBUG | 7 days | Short-term debugging |
| INFO | 30-90 days | Operational history |
| WARN | 90-180 days | Anomaly tracking |
| ERROR | 6-12 months | Error analysis & trends |
| Accounting | 5-10 years | Legal compliance |

**Implementation:**
```python
# Retention policy configuration
RETENTION_POLICY = {
    'DEBUG': timedelta(days=7),
    'INFO': timedelta(days=90),
    'WARN': timedelta(days=180),
    'ERROR': timedelta(days=365),
}

# Special retention for accounting
ACCOUNTING_RETENTION = timedelta(days=3650)  # 10 years

def apply_retention_policy(log_entry):
    """Apply retention policy based on log level and module."""
    if log_entry['module'] == 'acc':
        return ACCOUNTING_RETENTION
    else:
        return RETENTION_POLICY.get(log_entry['level'], timedelta(days=30))
```

#### 43.8.2 Security

**Data Protection:**
- ✅ Encrypted at rest (AES-256)
- ✅ Encrypted in transit (TLS)
- ✅ Access control via RBAC
- ✅ Audit trail for log access

**Access Control Rules:**
```python
# Who can see what logs
LOG_ACCESS_RULES = {
    'developer': {
        'can_view': ['own_tenant', 'dev_environment'],
        'cannot_view': ['other_tenants', 'production']
    },
    'support': {
        'can_view': ['assigned_tenants', 'all_environments'],
        'cannot_view': ['other_tenants', 'sensitive_modules']
    },
    'admin': {
        'can_view': ['all'],
        'cannot_view': []
    },
    'auditor': {
        'can_view': ['accounting_logs', 'audit_logs'],
        'cannot_view': ['debug_logs']
    }
}
```

**Sensitive Data Masking:**
```python
# shared/logging/sanitizer.py
import re
from typing import Any, Dict

SENSITIVE_PATTERNS = {
    'password': r'password',
    'token': r'(token|jwt|bearer)',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'ktp': r'\b\d{16}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
}

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data before logging.
    """
    sanitized = {}

    for key, value in data.items():
        # Check if key is sensitive
        if any(pattern in key.lower() for pattern in ['password', 'token', 'secret', 'key']):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, str):
            # Mask credit cards, KTP, etc.
            sanitized[key] = mask_sensitive_strings(value)
        else:
            sanitized[key] = value

    return sanitized

def mask_sensitive_strings(text: str) -> str:
    """Mask sensitive patterns in strings."""
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if pattern_name == 'credit_card':
            text = re.sub(pattern, '****-****-****-****', text)
        elif pattern_name == 'ktp':
            text = re.sub(pattern, '****************', text)
        elif pattern_name == 'email':
            text = re.sub(pattern, lambda m: mask_email(m.group()), text)
    return text

def mask_email(email: str) -> str:
    """Mask email addresses (keep first char + domain)."""
    parts = email.split('@')
    if len(parts) == 2:
        return f"{parts[0][0]}***@{parts[1]}"
    return email
```

---

### 43.9 Log vs Metric vs Trace

**Tiga pilar observability - saling melengkapi, tidak saling menggantikan:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 LOG vs METRIC vs TRACE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LOG (Discrete Events)                                                  │
│  • What: Detail kejadian spesifik                                      │
│  • When: State change, error, audit trail                              │
│  • Example: "Reservation created for tenant X"                         │
│  • Tool: Elasticsearch, Loki, CloudWatch Logs                          │
│  • Query: "Show me all errors for tenant X"                            │
│                                                                         │
│  METRIC (Aggregated Data)                                               │
│  • What: Tren & agregat numerik                                        │
│  • When: Performance monitoring, capacity planning                     │
│  • Example: "Average response time: 234ms"                             │
│  • Tool: Prometheus, Grafana, CloudWatch Metrics                       │
│  • Query: "Show me avg response time over last hour"                   │
│                                                                         │
│  TRACE (Request Flow)                                                   │
│  • What: 1 transaksi lintas banyak service                             │
│  • When: Debugging distributed system                                  │
│  • Example: "Request flow: API → PMS → Accounting → Notification"     │
│  • Tool: Jaeger, Zipkin, OpenTelemetry                                 │
│  • Query: "Show me full trace for request req_abc123"                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Example Scenario:**

**Problem:** Slow reservation creation

**Log:** "What happened?"
```json
{
  "event": "reservation_created",
  "duration_ms": 3500,  // Slow!
  "message": "Reservation created but took longer than expected"
}
```

**Metric:** "How often? How bad?"
```
reservation_creation_duration_ms{quantile="0.95"} = 3200ms
reservation_creation_rate = 45/min
```

**Trace:** "Where is the bottleneck?"
```
Span 1: API Gateway (50ms)
Span 2: PMS Service (200ms)
Span 3: Database Query (2800ms)  ← Bottleneck!
Span 4: Event Publishing (150ms)
Span 5: Accounting Service (300ms)
Total: 3500ms
```

**Integration:**
```python
# Use all three together
from shared.logging.config import logger
from shared.observability.context import get_trace_context
from shared.metrics import metrics

# Start span (trace)
with tracer.start_as_current_span("create_reservation") as span:
    start_time = time.time()

    try:
        # Business logic
        reservation = create_reservation(data)

        # Log state change
        logger.info(
            "reservation_created",
            extra={
                "trace_id": get_trace_context().trace_id,
                "entity": {"type": "reservation", "id": reservation.id}
            }
        )

        # Record metric
        duration = time.time() - start_time
        metrics.histogram(
            "reservation_creation_duration_seconds",
            duration,
            tags={"status": "success"}
        )

    except Exception as e:
        # Log error
        logger.error(
            "reservation_creation_failed",
            extra={
                "trace_id": get_trace_context().trace_id,
                "error": {"code": e.code, "message": str(e)}
            }
        )

        # Record error metric
        metrics.increment(
            "reservation_creation_errors_total",
            tags={"error_type": e.code}
        )

        # Add span error
        span.set_status(Status(StatusCode.ERROR))
        span.record_exception(e)

        raise
```

---

### 43.10 Best Practices

#### 43.10.1 DO's ✅

**1. Always Use Structured Logging**
```python
# ✅ GOOD
logger.info(
    "user_login",
    extra={"user_id": user_id, "tenant_id": tenant_id}
)

# ❌ BAD
logger.info(f"User {user_id} logged in to tenant {tenant_id}")
```

**2. Include Context**
```python
# ✅ GOOD - Always include tenant_id, user_id, request_id
logger.error(
    "payment_failed",
    extra={
        "tenant_id": tenant_id,
        "user_id": user_id,
        "request_id": request_id,
        "payment_id": payment_id,
        "error": {"code": "PAYMENT_GATEWAY_ERROR"}
    }
)

# ❌ BAD - No context
logger.error("Payment failed")
```

**3. Use Appropriate Log Levels**
```python
# ✅ GOOD
logger.info("reservation_created", ...)  # State change
logger.warning("slow_query_detected", ...)  # Anomaly
logger.error("payment_failed", ...)  # Operation failed

# ❌ BAD
logger.info("Error: payment failed")  # Wrong level
logger.error("Processing reservation")  # Not an error
```

**4. Sanitize Sensitive Data**
```python
# ✅ GOOD
from shared.logging.sanitizer import sanitize_log_data

logger.info(
    "user_updated",
    extra=sanitize_log_data({
        "user_id": user_id,
        "changes": changes  # Sanitizer will mask passwords, etc.
    })
)

# ❌ BAD
logger.info("user_updated", extra={"password": new_password})
```

**5. Log State Changes, Not Every Operation**
```python
# ✅ GOOD - Log important state changes
logger.info("reservation_confirmed", ...)
logger.info("payment_completed", ...)
logger.info("invoice_generated", ...)

# ❌ BAD - Too verbose
logger.info("checking_availability", ...)
logger.info("availability_checked", ...)
logger.info("calculating_price", ...)
logger.info("price_calculated", ...)
logger.info("validating_data", ...)
logger.info("data_validated", ...)
```

#### 43.10.2 DON'Ts ❌

**1. Never Use print() or console.log()**
```python
# ❌ BAD
print("Debug: reservation created")
console.log("User logged in")

# ✅ GOOD
logger.debug("reservation_created", ...)
logger.info("user_login", ...)
```

**2. Never Log Sensitive Data**
```python
# ❌ BAD
logger.info("user_login", extra={
    "password": password,
    "token": auth_token,
    "credit_card": card_number
})

# ✅ GOOD
logger.info("user_login", extra={
    "user_id": user_id,
    # Sensitive fields omitted
})
```

**3. Don't Log Without Context**
```python
# ❌ BAD
logger.error("Database error")

# ✅ GOOD
logger.error(
    "database_connection_failed",
    extra={
        "tenant_id": tenant_id,
        "database": db_name,
        "error": {"code": "CONNECTION_TIMEOUT"}
    }
)
```

**4. Don't Swallow Exceptions Without Logging**
```python
# ❌ BAD
try:
    process_payment(payment)
except Exception:
    pass  # Silent failure!

# ✅ GOOD
try:
    process_payment(payment)
except Exception as e:
    logger.error(
        "payment_processing_failed",
        extra={"payment_id": payment_id},
        exc_info=True
    )
    raise
```

**5. Don't Create Log Noise**
```python
# ❌ BAD - Every loop iteration
for item in items:
    logger.info(f"Processing item {item.id}")

# ✅ GOOD - Summary after batch
logger.info(
    "batch_processed",
    extra={
        "total_items": len(items),
        "success_count": success_count,
        "error_count": error_count
    }
)
```

---

## Reference

**Related Standards:**
- [STD-11: Distributed Tracing](./STD-11-tracing-secrets-tasks.md#standard-40-distributed-tracing-opentelemetry)
- [STD-10: Health Monitoring](./STD-10-circuit-health-archival.md)
- [STD-01: Error Handling](./STD-01-core-naming-db-rbac-api.md#75-error-logging)

**External Resources:**
- Structured Logging: https://www.structlog.org/
- Python JSON Logger: https://github.com/madzak/python-json-logger
- OpenTelemetry Logging: https://opentelemetry.io/docs/specs/otel/logs/
- Elasticsearch Logging Best Practices: https://www.elastic.co/guide/

**Tools:**
- **Backend:** python-json-logger, structlog
- **Frontend:** LogRocket, Sentry, custom logging service
- **Aggregation:** Elasticsearch, Loki, CloudWatch Logs
- **Analysis:** Kibana, Grafana, CloudWatch Insights

---

**Last Updated:** 2024-12-23
**Status:** FINAL - Ready for Implementation
**Owner:** Engineering Team

---

## Appendix: Quick Reference

### Log Schema Checklist

```
✅ timestamp (ISO-8601)
✅ level (TRACE|DEBUG|INFO|WARN|ERROR|FATAL)
✅ env (dev|staging|production)
✅ module (pms|acc|inv|...)
✅ service (service name)
✅ version (semver)
✅ tenant_id (if applicable)
✅ user_id (if applicable)
✅ request_id (for API requests)
✅ trace_id (for distributed tracing)
✅ event (event name, snake_case)
✅ message (human-readable)
⚠️ error (if error occurred)
⚠️ entity (if operating on entity)
⚠️ meta (additional context)
```

### AI Coding Hard Rules

```
1. ❌ NO print() / console.log()
2. ✅ ALL logs must be structured JSON
3. ✅ ALL business logic must accept context (tenant_id, user_id, etc.)
4. ❌ NEVER log sensitive data (password, token, KTP, credit card)
5. ✅ Log levels must follow defined rules
6. ✅ Always sanitize before logging
7. ✅ Include trace_id for distributed operations
8. ✅ Log state changes, not every operation
```

**Violation = Code is WRONG even if it runs.**
