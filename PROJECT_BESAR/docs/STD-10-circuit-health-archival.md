# Development Standards V10

> Standards #37-39: Circuit Breaker & Resilience, Health Checks & Readiness, Data Archival & Retention

---

## Table of Contents

- [Standard #37: Circuit Breaker & Resilience](#standard-37-circuit-breaker--resilience)
- [Standard #38: Health Checks & Readiness](#standard-38-health-checks--readiness)
- [Standard #39: Data Archival & Retention](#standard-39-data-archival--retention)

---

## Standard #37: Circuit Breaker & Resilience

### 37.1 Overview

Circuit Breaker adalah pattern untuk mencegah cascade failure ketika external service atau dependency mengalami masalah. Seperti circuit breaker listrik, pattern ini "memutus" koneksi sementara untuk mencegah kerusakan lebih lanjut.

### 37.2 Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         ┌──────────────┐                                │
│                         │    CLOSED    │                                │
│                         │  (Normal)    │                                │
│                         └──────┬───────┘                                │
│                                │                                         │
│                    Failure threshold reached                            │
│                                │                                         │
│                                ▼                                         │
│                         ┌──────────────┐                                │
│         ┌───────────────│     OPEN     │                                │
│         │               │  (Blocking)  │                                │
│         │               └──────┬───────┘                                │
│         │                      │                                         │
│         │          Timeout expires (recovery time)                      │
│         │                      │                                         │
│         │                      ▼                                         │
│         │               ┌──────────────┐                                │
│         │               │  HALF-OPEN   │                                │
│         │               │  (Testing)   │                                │
│         │               └──────┬───────┘                                │
│         │                      │                                         │
│         │          ┌───────────┴───────────┐                            │
│         │          │                       │                            │
│         │    Success                    Failure                         │
│         │          │                       │                            │
│         │          ▼                       │                            │
│         │   ┌──────────────┐               │                            │
│         │   │    CLOSED    │               │                            │
│         │   │  (Recovered) │               │                            │
│         │   └──────────────┘               │                            │
│         │                                  │                            │
│         └──────────────────────────────────┘                            │
│                                                                          │
│  Legend:                                                                 │
│  CLOSED   = Normal operation, requests pass through                     │
│  OPEN     = Failure detected, requests blocked immediately              │
│  HALF-OPEN = Testing if service recovered, limited requests allowed     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 37.3 Circuit Breaker Implementation

```python
# shared/resilience/circuit_breaker.py
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, TypeVar, Optional, Any
from dataclasses import dataclass, field
import functools
import logging

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout: int = 30                   # Seconds to wait before half-open
    half_open_max_calls: int = 3        # Max calls allowed in half-open state
    excluded_exceptions: tuple = ()     # Exceptions that don't count as failures

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    half_open_calls: int = 0
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0

class CircuitBreakerError(Exception):
    """Raised when circuit is open"""
    def __init__(self, circuit_name: str, retry_after: int):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(f"Circuit '{circuit_name}' is open. Retry after {retry_after}s")

class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback = fallback
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self.stats.state

    @property
    def is_closed(self) -> bool:
        return self.stats.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.stats.state == CircuitState.OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self.is_open:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    retry_after = self._get_retry_after()
                    if self.fallback:
                        return await self._execute_fallback(*args, **kwargs)
                    raise CircuitBreakerError(self.name, retry_after)

            # Check half-open call limit
            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.half_open_calls >= self.config.half_open_max_calls:
                    if self.fallback:
                        return await self._execute_fallback(*args, **kwargs)
                    raise CircuitBreakerError(self.name, self.config.timeout)
                self.stats.half_open_calls += 1

        # Execute the function
        try:
            self.stats.total_calls += 1
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except self.config.excluded_exceptions:
            # Don't count excluded exceptions as failures
            raise
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = datetime.utcnow()
            self.stats.failure_count = 0

            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()

    async def _on_failure(self, error: Exception):
        """Handle failed call"""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = datetime.utcnow()
            self.stats.success_count = 0

            logger.warning(
                f"Circuit '{self.name}' failure #{self.stats.failure_count}: {error}"
            )

            if self.stats.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.stats.failure_count >= self.config.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Open the circuit"""
        self.stats.state = CircuitState.OPEN
        self.stats.opened_at = datetime.utcnow()
        self.stats.half_open_calls = 0
        logger.warning(f"Circuit '{self.name}' OPENED after {self.stats.failure_count} failures")

    def _transition_to_half_open(self):
        """Move to half-open state"""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.success_count = 0
        self.stats.failure_count = 0
        self.stats.half_open_calls = 0
        logger.info(f"Circuit '{self.name}' moved to HALF-OPEN")

    def _transition_to_closed(self):
        """Close the circuit (recovered)"""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.opened_at = None
        logger.info(f"Circuit '{self.name}' CLOSED (recovered)")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again"""
        if not self.stats.opened_at:
            return True
        elapsed = (datetime.utcnow() - self.stats.opened_at).total_seconds()
        return elapsed >= self.config.timeout

    def _get_retry_after(self) -> int:
        """Get seconds until retry is allowed"""
        if not self.stats.opened_at:
            return 0
        elapsed = (datetime.utcnow() - self.stats.opened_at).total_seconds()
        return max(0, int(self.config.timeout - elapsed))

    async def _execute_fallback(self, *args, **kwargs) -> Any:
        """Execute fallback function"""
        if asyncio.iscoroutinefunction(self.fallback):
            return await self.fallback(*args, **kwargs)
        return self.fallback(*args, **kwargs)

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "last_failure": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "opened_at": self.stats.opened_at.isoformat() if self.stats.opened_at else None,
        }


# Decorator version
def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 30,
    fallback: Optional[Callable] = None
):
    """Decorator for circuit breaker protection"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout
    )
    cb = CircuitBreaker(name, config, fallback)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        wrapper.circuit_breaker = cb
        return wrapper

    return decorator


# Circuit breaker registry
class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def register(cls, name: str, breaker: CircuitBreaker):
        cls._breakers[name] = breaker

    @classmethod
    def get(cls, name: str) -> Optional[CircuitBreaker]:
        return cls._breakers.get(name)

    @classmethod
    def get_all_stats(cls) -> list[dict]:
        return [b.get_stats() for b in cls._breakers.values()]

    @classmethod
    def reset(cls, name: str):
        breaker = cls._breakers.get(name)
        if breaker:
            breaker._transition_to_closed()
```

### 37.4 Retry Pattern

```python
# shared/resilience/retry.py
import asyncio
import random
from typing import Callable, TypeVar, Optional, Type, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt (exponential backoff with jitter)"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def should_retry(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        if isinstance(exception, self.non_retryable_exceptions):
            return False
        return isinstance(exception, self.retryable_exceptions)


async def retry_async(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """Execute async function with retry logic"""
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if not config.should_retry(e):
                logger.warning(f"Non-retryable exception: {e}")
                raise

            if attempt >= config.max_retries:
                logger.error(f"Max retries ({config.max_retries}) exceeded: {e}")
                raise

            delay = config.get_delay(attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s"
            )
            await asyncio.sleep(delay)

    raise last_exception


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retry with exponential backoff"""
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions
    )

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)
        return wrapper

    return decorator
```

### 37.5 Bulkhead Pattern

```python
# shared/resilience/bulkhead.py
import asyncio
from typing import Callable, TypeVar, Optional
from functools import wraps
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class BulkheadConfig:
    """Configuration for bulkhead"""
    max_concurrent: int = 10        # Max concurrent executions
    max_wait_time: float = 30.0     # Max time to wait for slot (seconds)

class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity"""
    pass

class Bulkhead:
    """
    Bulkhead pattern implementation.
    Limits concurrent executions to prevent resource exhaustion.
    """

    def __init__(self, name: str, config: Optional[BulkheadConfig] = None):
        self.name = name
        self.config = config or BulkheadConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._active_count = 0
        self._waiting_count = 0

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function within bulkhead constraints"""
        self._waiting_count += 1

        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.config.max_wait_time
            )
        except asyncio.TimeoutError:
            self._waiting_count -= 1
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full. "
                f"Active: {self._active_count}, Waiting: {self._waiting_count}"
            )

        self._waiting_count -= 1
        self._active_count += 1

        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        finally:
            self._active_count -= 1
            self._semaphore.release()

    def get_stats(self) -> dict:
        """Get bulkhead statistics"""
        return {
            "name": self.name,
            "max_concurrent": self.config.max_concurrent,
            "active_count": self._active_count,
            "waiting_count": self._waiting_count,
            "available_slots": self.config.max_concurrent - self._active_count
        }


def bulkhead(name: str, max_concurrent: int = 10, max_wait_time: float = 30.0):
    """Decorator for bulkhead protection"""
    config = BulkheadConfig(max_concurrent=max_concurrent, max_wait_time=max_wait_time)
    bh = Bulkhead(name, config)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await bh.execute(func, *args, **kwargs)
        wrapper.bulkhead = bh
        return wrapper

    return decorator
```

### 37.6 Timeout Pattern

```python
# shared/resilience/timeout.py
import asyncio
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')

class TimeoutError(Exception):
    """Raised when operation times out"""
    pass

async def with_timeout(
    func: Callable[..., T],
    timeout_seconds: float,
    *args,
    **kwargs
) -> T:
    """Execute function with timeout"""
    try:
        return await asyncio.wait_for(
            func(*args, **kwargs),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")


def timeout(seconds: float):
    """Decorator for timeout protection"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_timeout(func, seconds, *args, **kwargs)
        return wrapper
    return decorator
```

### 37.7 Usage Examples

```python
# services/payment/gateway.py
from shared.resilience.circuit_breaker import circuit_breaker, CircuitBreaker
from shared.resilience.retry import retry
from shared.resilience.bulkhead import bulkhead
from shared.resilience.timeout import timeout

# Combined resilience patterns
class PaymentGateway:
    """Payment gateway with resilience patterns"""

    def __init__(self):
        # Circuit breaker for external payment API
        self.circuit_breaker = CircuitBreaker(
            name="payment_gateway",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                timeout=60,
                success_threshold=2
            ),
            fallback=self._fallback_payment
        )

        # Bulkhead to limit concurrent payments
        self.bulkhead = Bulkhead(
            name="payment_processing",
            config=BulkheadConfig(max_concurrent=20)
        )

    @timeout(30)  # 30 second timeout
    @retry(max_retries=2, base_delay=1.0)  # Retry twice
    async def process_payment(self, payment_data: dict) -> dict:
        """Process payment with full resilience"""

        # Execute within bulkhead and circuit breaker
        async def _process():
            return await self.circuit_breaker.call(
                self._call_payment_api,
                payment_data
            )

        return await self.bulkhead.execute(_process)

    async def _call_payment_api(self, payment_data: dict) -> dict:
        """Actual API call to payment provider"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://payment-api.example.com/charge",
                json=payment_data,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def _fallback_payment(self, payment_data: dict) -> dict:
        """Fallback when circuit is open"""
        # Queue for later processing
        await self._queue_payment(payment_data)
        return {
            "status": "queued",
            "message": "Payment queued for processing. Will be processed shortly."
        }

    def get_health(self) -> dict:
        """Get health status"""
        return {
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "bulkhead": self.bulkhead.get_stats()
        }


# Using decorators
@circuit_breaker(name="email_service", failure_threshold=5, timeout=30)
@retry(max_retries=3, base_delay=2.0)
@bulkhead(name="email_sending", max_concurrent=10)
async def send_email(to: str, subject: str, body: str):
    """Send email with resilience"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://email-api.example.com/send",
            json={"to": to, "subject": subject, "body": body}
        )
        response.raise_for_status()
```

### 37.8 Monitoring & Alerting

```python
# shared/resilience/monitoring.py
from prometheus_client import Counter, Gauge, Histogram

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Current state of circuit breaker (0=closed, 1=open, 2=half-open)',
    ['circuit_name']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['circuit_name']
)

circuit_breaker_successes = Counter(
    'circuit_breaker_successes_total',
    'Total circuit breaker successes',
    ['circuit_name']
)

circuit_breaker_opens = Counter(
    'circuit_breaker_opens_total',
    'Total times circuit breaker opened',
    ['circuit_name']
)

# Retry metrics
retry_attempts = Counter(
    'retry_attempts_total',
    'Total retry attempts',
    ['operation']
)

retry_successes = Counter(
    'retry_successes_total',
    'Successful operations after retry',
    ['operation']
)

# Bulkhead metrics
bulkhead_active = Gauge(
    'bulkhead_active_count',
    'Current active executions in bulkhead',
    ['bulkhead_name']
)

bulkhead_waiting = Gauge(
    'bulkhead_waiting_count',
    'Current waiting executions in bulkhead',
    ['bulkhead_name']
)

bulkhead_rejected = Counter(
    'bulkhead_rejected_total',
    'Total rejected executions due to full bulkhead',
    ['bulkhead_name']
)
```

### 37.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Tune Thresholds | Adjust thresholds based on service characteristics |
| 2 | Provide Fallbacks | Always have fallback for critical operations |
| 3 | Monitor States | Monitor circuit breaker states actively |
| 4 | Combine Patterns | Use multiple patterns together |
| 5 | Test Failure Modes | Chaos engineering untuk test resilience |
| 6 | Graceful Degradation | Degrade gracefully, don't fail completely |
| 7 | Timeout Everything | Set timeouts on all external calls |
| 8 | Isolate Dependencies | Use bulkheads to isolate dependencies |

---

## Standard #38: Health Checks & Readiness

### 38.1 Overview

Health Checks memverifikasi status aplikasi dan dependencies-nya. Digunakan oleh load balancers, orchestrators (Docker/Kubernetes), dan monitoring systems untuk menentukan apakah instance dapat menerima traffic.

### 38.2 Health Check Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       HEALTH CHECK TYPES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. LIVENESS CHECK (/health/live)                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  "Is the application running?"                                   │   │
│  │                                                                   │   │
│  │  Checks:                                                          │   │
│  │  - Application process is running                                 │   │
│  │  - Not in deadlock                                                │   │
│  │  - Not in infinite loop                                           │   │
│  │                                                                   │   │
│  │  If fails: Container should be RESTARTED                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  2. READINESS CHECK (/health/ready)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  "Is the application ready to receive traffic?"                  │   │
│  │                                                                   │   │
│  │  Checks:                                                          │   │
│  │  - All dependencies connected (DB, Redis, etc)                   │   │
│  │  - Initialization complete                                        │   │
│  │  - Warmup done                                                    │   │
│  │                                                                   │   │
│  │  If fails: STOP sending traffic (but don't restart)              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  3. STARTUP CHECK (/health/startup)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  "Has the application finished starting up?"                     │   │
│  │                                                                   │   │
│  │  Checks:                                                          │   │
│  │  - Initial data loaded                                            │   │
│  │  - Migrations complete                                            │   │
│  │  - Caches warmed                                                  │   │
│  │                                                                   │   │
│  │  If fails during startup: Allow more time before restart         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  4. DEEP HEALTH CHECK (/health/deep)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  "Detailed health of all components"                             │   │
│  │                                                                   │   │
│  │  Checks all dependencies with details:                           │   │
│  │  - Database (connection, query latency)                          │   │
│  │  - Redis (connection, memory)                                     │   │
│  │  - External APIs (availability)                                   │   │
│  │  - Disk space                                                     │   │
│  │  - Memory usage                                                   │   │
│  │                                                                   │   │
│  │  Use for: Debugging, monitoring dashboards                       │   │
│  │  NOT for: Load balancer checks (too slow)                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 38.3 Health Check Implementation

```python
# shared/health/checks.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio
import psutil

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class OverallHealth:
    """Overall health status"""
    status: HealthStatus
    checks: List[HealthCheckResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "message": check.message,
                    "latency_ms": check.latency_ms,
                    "details": check.details
                }
                for check in self.checks
            }
        }


class HealthCheck(ABC):
    """Base class for health checks"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        pass


class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    @property
    def name(self) -> str:
        return "database"

    async def check(self) -> HealthCheckResult:
        start = datetime.utcnow()
        try:
            async with self.db_session_factory() as session:
                # Simple query to check connection
                result = await session.execute("SELECT 1")
                result.scalar()

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            # Check if latency is acceptable
            if latency > 1000:  # > 1 second
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"High latency: {latency:.0f}ms",
                    latency_ms=latency
                )

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(datetime.utcnow() - start).total_seconds() * 1000
            )


class RedisHealthCheck(HealthCheck):
    """Check Redis connectivity"""

    def __init__(self, redis_client):
        self.redis = redis_client

    @property
    def name(self) -> str:
        return "redis"

    async def check(self) -> HealthCheckResult:
        start = datetime.utcnow()
        try:
            # Ping Redis
            await self.redis.ping()

            # Get memory info
            info = await self.redis.info("memory")
            used_memory = info.get("used_memory_human", "unknown")

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={"used_memory": used_memory}
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(datetime.utcnow() - start).total_seconds() * 1000
            )


class DiskHealthCheck(HealthCheck):
    """Check disk space"""

    def __init__(self, path: str = "/", threshold_percent: float = 90):
        self.path = path
        self.threshold = threshold_percent

    @property
    def name(self) -> str:
        return "disk"

    async def check(self) -> HealthCheckResult:
        try:
            disk = psutil.disk_usage(self.path)
            used_percent = disk.percent

            if used_percent >= self.threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage critical: {used_percent}%"
            elif used_percent >= self.threshold - 10:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high: {used_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = None

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": used_percent
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )


class MemoryHealthCheck(HealthCheck):
    """Check memory usage"""

    def __init__(self, threshold_percent: float = 90):
        self.threshold = threshold_percent

    @property
    def name(self) -> str:
        return "memory"

    async def check(self) -> HealthCheckResult:
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent

            if used_percent >= self.threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical: {used_percent}%"
            elif used_percent >= self.threshold - 10:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high: {used_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = None

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": used_percent
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )


class ExternalServiceHealthCheck(HealthCheck):
    """Check external service availability"""

    def __init__(self, name: str, url: str, timeout: float = 5.0):
        self._name = name
        self.url = url
        self.timeout = timeout

    @property
    def name(self) -> str:
        return self._name

    async def check(self) -> HealthCheckResult:
        import httpx
        start = datetime.utcnow()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, timeout=self.timeout)
                latency = (datetime.utcnow() - start).total_seconds() * 1000

                if response.status_code < 400:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={"status_code": response.status_code}
                    )
                else:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.DEGRADED,
                        message=f"HTTP {response.status_code}",
                        latency_ms=latency
                    )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(datetime.utcnow() - start).total_seconds() * 1000
            )
```

### 38.4 Health Service

```python
# shared/health/service.py
from typing import List, Optional
from .checks import (
    HealthCheck, HealthCheckResult, OverallHealth, HealthStatus
)
import asyncio

class HealthService:
    """Service for managing health checks"""

    def __init__(self):
        self._checks: List[HealthCheck] = []
        self._startup_complete = False

    def register(self, check: HealthCheck):
        """Register a health check"""
        self._checks.append(check)

    def mark_startup_complete(self):
        """Mark application startup as complete"""
        self._startup_complete = True

    async def check_liveness(self) -> OverallHealth:
        """
        Liveness check - is the application running?
        Should be fast and only check application is alive.
        """
        # Basic check - if this code runs, we're alive
        return OverallHealth(
            status=HealthStatus.HEALTHY,
            checks=[]
        )

    async def check_readiness(self) -> OverallHealth:
        """
        Readiness check - can we accept traffic?
        Checks critical dependencies only.
        """
        critical_checks = ["database", "redis"]
        results = await self._run_checks(
            [c for c in self._checks if c.name in critical_checks]
        )
        return self._aggregate_results(results)

    async def check_startup(self) -> OverallHealth:
        """
        Startup check - has the application finished starting?
        """
        if not self._startup_complete:
            return OverallHealth(
                status=HealthStatus.UNHEALTHY,
                checks=[HealthCheckResult(
                    name="startup",
                    status=HealthStatus.UNHEALTHY,
                    message="Application still starting"
                )]
            )

        return await self.check_readiness()

    async def check_deep(self) -> OverallHealth:
        """
        Deep health check - detailed status of all components.
        Slower, use for debugging/dashboards only.
        """
        results = await self._run_checks(self._checks)
        return self._aggregate_results(results)

    async def _run_checks(
        self,
        checks: List[HealthCheck],
        timeout: float = 10.0
    ) -> List[HealthCheckResult]:
        """Run health checks concurrently with timeout"""
        async def run_with_timeout(check: HealthCheck) -> HealthCheckResult:
            try:
                return await asyncio.wait_for(
                    check.check(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return HealthCheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check timed out after {timeout}s"
                )

        tasks = [run_with_timeout(c) for c in checks]
        return await asyncio.gather(*tasks)

    def _aggregate_results(self, results: List[HealthCheckResult]) -> OverallHealth:
        """Aggregate individual results into overall health"""
        if not results:
            return OverallHealth(status=HealthStatus.HEALTHY, checks=[])

        # Determine overall status
        statuses = [r.status for r in results]

        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return OverallHealth(status=overall, checks=results)
```

### 38.5 Health Endpoints

```python
# shared/health/routes.py
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from .service import HealthService
from .checks import HealthStatus

router = APIRouter(prefix="/health", tags=["Health"])

# Singleton health service
health_service = HealthService()

@router.get("/live")
async def liveness():
    """
    Liveness probe - is the application running?
    Used by: Kubernetes livenessProbe, Docker HEALTHCHECK
    """
    health = await health_service.check_liveness()
    status_code = 200 if health.status == HealthStatus.HEALTHY else 503
    return JSONResponse(
        content={"status": health.status.value},
        status_code=status_code
    )

@router.get("/ready")
async def readiness():
    """
    Readiness probe - is the application ready for traffic?
    Used by: Kubernetes readinessProbe, Load balancer health checks
    """
    health = await health_service.check_readiness()
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
    return JSONResponse(
        content=health.to_dict(),
        status_code=status_code
    )

@router.get("/startup")
async def startup():
    """
    Startup probe - has the application finished starting?
    Used by: Kubernetes startupProbe
    """
    health = await health_service.check_startup()
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
    return JSONResponse(
        content=health.to_dict(),
        status_code=status_code
    )

@router.get("/deep")
async def deep_health():
    """
    Deep health check - detailed status of all components.
    Used by: Monitoring dashboards, debugging
    NOT for: Load balancer health checks (too slow)
    """
    health = await health_service.check_deep()
    status_code = 200 if health.status != HealthStatus.UNHEALTHY else 503
    return JSONResponse(
        content=health.to_dict(),
        status_code=status_code
    )

@router.get("")
async def health():
    """Default health check - alias for readiness"""
    return await readiness()
```

### 38.6 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# ... other instructions ...

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health/live || exit 1
```

```yaml
# docker-compose.yml
services:
  backend-api:
    image: hotel-pms-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 38.7 Kubernetes Configuration

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hotel-pms-backend
spec:
  template:
    spec:
      containers:
        - name: backend
          image: hotel-pms-backend:latest
          ports:
            - containerPort: 8001

          # Liveness probe - restart if fails
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8001
            initialDelaySeconds: 10
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3

          # Readiness probe - stop traffic if fails
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8001
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 2

          # Startup probe - allow slow startup
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8001
            initialDelaySeconds: 0
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 30  # 30 * 5s = 150s max startup time
```

### 38.8 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Fast Liveness | Liveness check harus sangat cepat |
| 2 | Separate Checks | Bedakan liveness dan readiness |
| 3 | No Auth | Health endpoints tidak perlu authentication |
| 4 | Timeout | Set timeout pada setiap check |
| 5 | Cache Results | Cache hasil untuk avoid thundering herd |
| 6 | Include Version | Sertakan version info di response |
| 7 | Monitor | Alert ketika health degraded |
| 8 | Graceful Shutdown | Handle SIGTERM dengan graceful shutdown |

---

## Standard #39: Data Archival & Retention

### 39.1 Overview

Data Archival & Retention mengelola lifecycle data dari active use hingga archival/deletion. Penting untuk compliance, performance, dan storage cost management.

### 39.2 Data Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LIFECYCLE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  ACTIVE  │───►│   WARM   │───►│   COLD   │───►│ ARCHIVED │         │
│  │          │    │          │    │          │    │          │         │
│  │ Hot data │    │ Less     │    │ Rarely   │    │ Long-term│         │
│  │ Frequent │    │ frequent │    │ accessed │    │ storage  │         │
│  │ access   │    │ access   │    │          │    │          │         │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘         │
│       │               │               │               │                │
│       │               │               │               │                │
│       ▼               ▼               ▼               ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ Primary  │    │Partitioned│   │ Archive  │    │  Object  │         │
│  │ Database │    │ Tables   │    │ Database │    │ Storage  │         │
│  │(SSD/Fast)│    │          │    │(HDD/Slow)│    │(S3/R2)   │         │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘         │
│                                                                          │
│  Retention Examples:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Data Type       │ Active │  Warm  │  Cold  │ Archive │ Delete  │   │
│  │─────────────────────────────────────────────────────────────────│   │
│  │  Audit Logs      │ 30 days│ 90 days│ 1 year │ 7 years │ After   │   │
│  │  Transactions    │ 90 days│ 1 year │ 3 years│ 10 years│ Never   │   │
│  │  Session Data    │ 7 days │   -    │   -    │    -    │ 7 days  │   │
│  │  Temp Files      │ 1 day  │   -    │   -    │    -    │ 1 day   │   │
│  │  Bookings        │ 1 year │ 3 years│ 7 years│ Forever │ Never   │   │
│  │  Guest Profiles  │ Active │ 3 years│ 7 years│ On req. │ GDPR    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 39.3 Database Schema

```sql
-- Retention policy definitions
CREATE TABLE retention_policies (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Policy info
    name VARCHAR(200) NOT NULL,
    description TEXT,
    entity_type VARCHAR(100) NOT NULL,  -- bookings, audit_logs, sessions
    table_name VARCHAR(100) NOT NULL,

    -- Retention periods (in days, -1 = forever)
    active_period_days INTEGER NOT NULL,
    warm_period_days INTEGER DEFAULT -1,
    cold_period_days INTEGER DEFAULT -1,
    archive_period_days INTEGER DEFAULT -1,

    -- Archive settings
    archive_enabled BOOLEAN DEFAULT FALSE,
    archive_format VARCHAR(20) DEFAULT 'parquet',  -- parquet, csv, json
    archive_compression VARCHAR(20) DEFAULT 'gzip',
    archive_storage_path VARCHAR(500),

    -- Delete settings
    delete_enabled BOOLEAN DEFAULT FALSE,
    soft_delete BOOLEAN DEFAULT TRUE,

    -- Filter conditions (SQL WHERE clause)
    filter_condition TEXT,  -- e.g., "status = 'COMPLETED'"

    -- Schedule
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    cron_expression VARCHAR(100) DEFAULT '0 2 * * *',  -- Daily at 2 AM

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(entity_type)
);

-- Archive job tracking
CREATE TABLE archive_jobs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    policy_id INTEGER NOT NULL REFERENCES retention_policies(id),

    -- Job info
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    job_type VARCHAR(50) NOT NULL,  -- archive, delete, move_to_cold

    -- Scope
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    filter_condition TEXT,

    -- Progress
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    archived_rows INTEGER DEFAULT 0,
    deleted_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,

    -- Archive output
    archive_file_path VARCHAR(500),
    archive_file_size_bytes BIGINT,
    archive_checksum VARCHAR(64),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message TEXT,

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'processing', 'completed', 'failed', 'cancelled'
    ))
);

-- Archive metadata (for restore purposes)
CREATE TABLE archive_metadata (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_id INTEGER NOT NULL REFERENCES archive_jobs(id),

    -- Archive info
    entity_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    date_range_from DATE NOT NULL,
    date_range_to DATE NOT NULL,

    -- File info
    file_path VARCHAR(500) NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    row_count INTEGER NOT NULL,
    checksum VARCHAR(64) NOT NULL,

    -- Schema snapshot (for future restore)
    table_schema JSONB NOT NULL,

    -- Timestamps
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,  -- When archive can be deleted

    CONSTRAINT unique_archive UNIQUE(entity_type, date_range_from, date_range_to)
);

-- Indexes
CREATE INDEX idx_archive_jobs_policy ON archive_jobs(policy_id);
CREATE INDEX idx_archive_jobs_status ON archive_jobs(status);
CREATE INDEX idx_archive_metadata_entity ON archive_metadata(entity_type);
CREATE INDEX idx_archive_metadata_date ON archive_metadata(date_range_from, date_range_to);
```

### 39.4 Retention Policy Configuration

```python
# services/archival/policies.py
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class ArchiveFormat(str, Enum):
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"

@dataclass
class RetentionPolicy:
    """Retention policy definition"""
    entity_type: str
    table_name: str
    name: str

    # Retention periods (days)
    active_period: int           # Keep in primary table
    warm_period: int = -1        # Move to partitioned/warm storage
    cold_period: int = -1        # Move to archive database
    archive_period: int = -1     # Move to object storage
    delete_after: int = -1       # Delete completely (-1 = never)

    # Archive settings
    archive_enabled: bool = True
    archive_format: ArchiveFormat = ArchiveFormat.PARQUET
    archive_compression: str = "gzip"

    # Delete settings
    delete_enabled: bool = False
    soft_delete: bool = True

    # Date column for retention
    date_column: str = "created_at"

    # Additional filter
    filter_condition: Optional[str] = None

    # Related tables to archive together
    related_tables: List[str] = None


# Predefined policies
RETENTION_POLICIES = {
    "bookings": RetentionPolicy(
        entity_type="bookings",
        table_name="bookings",
        name="Booking Retention",
        active_period=365,      # 1 year active
        warm_period=1095,       # 3 years warm
        cold_period=2555,       # 7 years cold
        archive_period=-1,      # Keep forever in archive
        delete_after=-1,        # Never delete
        date_column="created_at",
        related_tables=["booking_items", "booking_payments", "booking_state_history"]
    ),

    "audit_logs": RetentionPolicy(
        entity_type="audit_logs",
        table_name="audit_logs",
        name="Audit Log Retention",
        active_period=30,       # 30 days active
        warm_period=90,         # 90 days warm
        cold_period=365,        # 1 year cold
        archive_period=2555,    # 7 years archive (compliance)
        delete_after=2920,      # Delete after 8 years
        date_column="created_at"
    ),

    "sessions": RetentionPolicy(
        entity_type="sessions",
        table_name="user_sessions",
        name="Session Retention",
        active_period=7,        # 7 days active
        delete_after=7,         # Delete after 7 days
        delete_enabled=True,
        archive_enabled=False   # Don't archive sessions
    ),

    "email_logs": RetentionPolicy(
        entity_type="email_logs",
        table_name="email_logs",
        name="Email Log Retention",
        active_period=90,       # 90 days active
        warm_period=365,        # 1 year warm
        archive_period=1095,    # 3 years archive
        delete_after=1460,      # Delete after 4 years
        date_column="created_at"
    ),

    "temp_files": RetentionPolicy(
        entity_type="temp_files",
        table_name="temporary_files",
        name="Temp File Cleanup",
        active_period=1,        # 1 day
        delete_after=1,         # Delete after 1 day
        delete_enabled=True,
        archive_enabled=False
    ),

    "transactions": RetentionPolicy(
        entity_type="transactions",
        table_name="transactions",
        name="Transaction Retention",
        active_period=90,       # 90 days active
        warm_period=365,        # 1 year warm
        cold_period=1095,       # 3 years cold
        archive_period=3650,    # 10 years archive (tax compliance)
        delete_after=-1,        # Never delete
        date_column="transaction_date",
        related_tables=["transaction_items", "transaction_payments"]
    ),
}
```

### 39.5 Archival Service

```python
# services/archival/service.py
from datetime import datetime, date, timedelta
from typing import Optional, List
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
import gzip
import hashlib

class ArchivalService:
    """Service for data archival and retention"""

    def __init__(
        self,
        db,
        policy_repo,
        job_repo,
        metadata_repo,
        storage_service
    ):
        self.db = db
        self.policy_repo = policy_repo
        self.job_repo = job_repo
        self.metadata_repo = metadata_repo
        self.storage = storage_service

    async def run_policy(self, policy_name: str) -> dict:
        """Run a specific retention policy"""
        policy = RETENTION_POLICIES.get(policy_name)
        if not policy:
            raise ValueError(f"Unknown policy: {policy_name}")

        results = {
            "policy": policy_name,
            "archived": 0,
            "deleted": 0,
            "errors": []
        }

        # Archive old data
        if policy.archive_enabled and policy.archive_period > 0:
            archive_before = date.today() - timedelta(days=policy.active_period)
            archive_result = await self._archive_data(policy, archive_before)
            results["archived"] = archive_result.get("rows", 0)

        # Delete expired data
        if policy.delete_enabled and policy.delete_after > 0:
            delete_before = date.today() - timedelta(days=policy.delete_after)
            delete_result = await self._delete_data(policy, delete_before)
            results["deleted"] = delete_result.get("rows", 0)

        return results

    async def _archive_data(
        self,
        policy: RetentionPolicy,
        before_date: date
    ) -> dict:
        """Archive data older than specified date"""
        # Create job record
        job = await self.job_repo.create({
            "policy_id": policy.entity_type,
            "job_type": "archive",
            "date_to": before_date,
            "status": "processing"
        })

        try:
            # Query data to archive
            query = f"""
                SELECT * FROM {policy.table_name}
                WHERE {policy.date_column} < :before_date
                AND NOT is_archived
            """
            if policy.filter_condition:
                query += f" AND {policy.filter_condition}"

            result = await self.db.execute(query, {"before_date": before_date})
            rows = result.fetchall()
            columns = result.keys()

            if not rows:
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                await self.job_repo.update(job)
                return {"rows": 0}

            # Convert to Arrow table
            data = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
            table = pa.table(data)

            # Write to Parquet
            buffer = BytesIO()
            pq.write_table(table, buffer, compression='gzip')
            parquet_bytes = buffer.getvalue()

            # Calculate checksum
            checksum = hashlib.sha256(parquet_bytes).hexdigest()

            # Upload to storage
            archive_path = self._get_archive_path(policy, before_date)
            await self.storage.upload(
                parquet_bytes,
                archive_path,
                content_type="application/octet-stream"
            )

            # Save metadata
            await self.metadata_repo.create({
                "job_id": job.id,
                "entity_type": policy.entity_type,
                "table_name": policy.table_name,
                "date_range_to": before_date,
                "file_path": archive_path,
                "file_format": "parquet",
                "file_size_bytes": len(parquet_bytes),
                "row_count": len(rows),
                "checksum": checksum,
                "table_schema": self._get_table_schema(policy.table_name)
            })

            # Mark rows as archived (or delete from main table)
            await self.db.execute(f"""
                UPDATE {policy.table_name}
                SET is_archived = TRUE, archived_at = NOW()
                WHERE {policy.date_column} < :before_date
            """, {"before_date": before_date})

            # Update job
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.archived_rows = len(rows)
            job.archive_file_path = archive_path
            job.archive_checksum = checksum
            await self.job_repo.update(job)

            return {"rows": len(rows), "path": archive_path}

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            await self.job_repo.update(job)
            raise

    async def _delete_data(
        self,
        policy: RetentionPolicy,
        before_date: date
    ) -> dict:
        """Delete data older than specified date"""
        # Verify data is archived before deletion (if archiving enabled)
        if policy.archive_enabled:
            archived = await self._verify_archived(policy, before_date)
            if not archived:
                raise ValueError("Data must be archived before deletion")

        if policy.soft_delete:
            # Soft delete
            query = f"""
                UPDATE {policy.table_name}
                SET is_deleted = TRUE, deleted_at = NOW()
                WHERE {policy.date_column} < :before_date
                AND is_deleted = FALSE
            """
        else:
            # Hard delete
            query = f"""
                DELETE FROM {policy.table_name}
                WHERE {policy.date_column} < :before_date
            """

        if policy.filter_condition:
            query = query.replace(
                "WHERE",
                f"WHERE {policy.filter_condition} AND"
            )

        result = await self.db.execute(query, {"before_date": before_date})
        return {"rows": result.rowcount}

    async def restore_from_archive(
        self,
        entity_type: str,
        date_from: date,
        date_to: date
    ) -> dict:
        """Restore data from archive"""
        # Find archive metadata
        archives = await self.metadata_repo.get_for_range(
            entity_type=entity_type,
            date_from=date_from,
            date_to=date_to
        )

        if not archives:
            raise ValueError("No archives found for specified range")

        restored_count = 0

        for archive in archives:
            # Download archive file
            file_bytes = await self.storage.download(archive.file_path)

            # Verify checksum
            checksum = hashlib.sha256(file_bytes).hexdigest()
            if checksum != archive.checksum:
                raise ValueError(f"Checksum mismatch for {archive.file_path}")

            # Read Parquet
            buffer = BytesIO(file_bytes)
            table = pq.read_table(buffer)
            df = table.to_pandas()

            # Insert back to database
            # Note: May need schema migration if structure changed
            for _, row in df.iterrows():
                await self._insert_row(archive.table_name, row.to_dict())
                restored_count += 1

        return {"restored": restored_count}

    def _get_archive_path(self, policy: RetentionPolicy, before_date: date) -> str:
        """Generate archive file path"""
        year = before_date.year
        month = before_date.month
        return f"archives/{policy.entity_type}/{year}/{month:02d}/{policy.table_name}_{before_date.isoformat()}.parquet.gz"

    async def _get_table_schema(self, table_name: str) -> dict:
        """Get table schema for archive metadata"""
        result = await self.db.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """, {"table_name": table_name})

        return {
            row["column_name"]: {
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES"
            }
            for row in result.fetchall()
        }
```

### 39.6 Scheduled Jobs

```python
# services/archival/scheduler.py
from celery import shared_task
from celery.schedules import crontab

# Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'run-archival-daily': {
        'task': 'services.archival.tasks.run_all_policies',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'cleanup-temp-files': {
        'task': 'services.archival.tasks.cleanup_temp_files',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

@shared_task
def run_all_policies():
    """Run all active retention policies"""
    from shared.database import get_db_sync

    with get_db_sync() as db:
        service = ArchivalService(db, ...)

        results = []
        for policy_name in RETENTION_POLICIES:
            try:
                result = service.run_policy(policy_name)
                results.append({"policy": policy_name, "success": True, **result})
            except Exception as e:
                results.append({
                    "policy": policy_name,
                    "success": False,
                    "error": str(e)
                })

        return results

@shared_task
def run_single_policy(policy_name: str):
    """Run a specific retention policy"""
    from shared.database import get_db_sync

    with get_db_sync() as db:
        service = ArchivalService(db, ...)
        return service.run_policy(policy_name)

@shared_task
def cleanup_temp_files():
    """Cleanup temporary files"""
    return run_single_policy("temp_files")
```

### 39.7 GDPR Compliance

```python
# services/archival/gdpr.py
from datetime import datetime
from typing import List

class GDPRService:
    """Handle GDPR data requests"""

    def __init__(self, db, archive_service, storage):
        self.db = db
        self.archive_service = archive_service
        self.storage = storage

    async def export_user_data(self, user_id: int) -> str:
        """
        GDPR Article 20: Data Portability
        Export all user data in machine-readable format
        """
        user_data = {}

        # Collect from all tables
        tables_with_user_data = [
            ("users", "id"),
            ("bookings", "guest_id"),
            ("transactions", "guest_id"),
            ("audit_logs", "user_id"),
            ("email_logs", "to_email"),
        ]

        for table, column in tables_with_user_data:
            result = await self.db.execute(
                f"SELECT * FROM {table} WHERE {column} = :user_id",
                {"user_id": user_id}
            )
            user_data[table] = [dict(row) for row in result.fetchall()]

        # Check archives
        archived_data = await self._search_archives(user_id)
        user_data["archived"] = archived_data

        # Generate export file
        export_path = await self._create_export_file(user_id, user_data)
        return export_path

    async def delete_user_data(
        self,
        user_id: int,
        retain_for_legal: bool = True
    ) -> dict:
        """
        GDPR Article 17: Right to Erasure
        Delete or anonymize user data
        """
        results = {
            "deleted": [],
            "anonymized": [],
            "retained": []
        }

        # Tables that can be fully deleted
        deletable_tables = ["user_sessions", "user_preferences"]

        # Tables that need anonymization (legal retention)
        anonymize_tables = ["bookings", "transactions"] if retain_for_legal else []

        # Delete from deletable tables
        for table in deletable_tables:
            await self.db.execute(
                f"DELETE FROM {table} WHERE user_id = :user_id",
                {"user_id": user_id}
            )
            results["deleted"].append(table)

        # Anonymize data in retained tables
        for table in anonymize_tables:
            await self._anonymize_table(table, user_id)
            results["anonymized"].append(table)

        # Anonymize user record
        await self.db.execute("""
            UPDATE users SET
                email = CONCAT('deleted_', id, '@anonymized.local'),
                name = 'Deleted User',
                phone = NULL,
                address = NULL,
                id_number = NULL,
                is_deleted = TRUE,
                deleted_at = NOW()
            WHERE id = :user_id
        """, {"user_id": user_id})

        # Mark archives for deletion
        await self._mark_archives_for_deletion(user_id)

        return results

    async def _anonymize_table(self, table: str, user_id: int):
        """Anonymize user data in a table while retaining for legal purposes"""
        # Replace personal data with anonymous values
        await self.db.execute(f"""
            UPDATE {table} SET
                guest_name = 'Anonymous',
                guest_email = NULL,
                guest_phone = NULL,
                notes = NULL
            WHERE guest_id = :user_id
        """, {"user_id": user_id})
```

### 39.8 API Endpoints

```python
# services/archival/routes.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/admin/archival", tags=["Archival"])

@router.get("/policies")
async def list_policies(
    current_user = Depends(require_admin)
):
    """List all retention policies"""
    return [
        {
            "name": name,
            "entity_type": p.entity_type,
            "active_period_days": p.active_period,
            "archive_enabled": p.archive_enabled,
            "delete_enabled": p.delete_enabled
        }
        for name, p in RETENTION_POLICIES.items()
    ]

@router.post("/policies/{policy_name}/run")
async def run_policy(
    policy_name: str,
    current_user = Depends(require_admin),
    archival_service: ArchivalService = Depends()
):
    """Manually run a retention policy"""
    result = await archival_service.run_policy(policy_name)
    return result

@router.get("/archives")
async def list_archives(
    entity_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user = Depends(require_admin),
    metadata_repo = Depends()
):
    """List archived data"""
    return await metadata_repo.search(
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to
    )

@router.post("/archives/restore")
async def restore_archive(
    request: RestoreArchiveRequest,
    current_user = Depends(require_admin),
    archival_service: ArchivalService = Depends()
):
    """Restore data from archive"""
    result = await archival_service.restore_from_archive(
        entity_type=request.entity_type,
        date_from=request.date_from,
        date_to=request.date_to
    )
    return result

@router.get("/jobs")
async def list_archive_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    current_user = Depends(require_admin),
    job_repo = Depends()
):
    """List archival jobs"""
    return await job_repo.list(status=status, limit=limit)
```

### 39.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Define Policies | Define clear retention policies per data type |
| 2 | Archive Before Delete | Always archive before permanent deletion |
| 3 | Verify Archives | Verify archive integrity with checksums |
| 4 | Test Restore | Regularly test archive restoration |
| 5 | Compliance First | Design for compliance requirements (GDPR, tax) |
| 6 | Audit Trail | Log all archival and deletion operations |
| 7 | Schema Versioning | Store schema with archives for future restore |
| 8 | Partitioning | Use table partitioning for large tables |

---

## Summary

| Standard | Key Points |
|----------|------------|
| #37 Circuit Breaker & Resilience | Prevent cascade failures, retry with backoff, bulkhead isolation |
| #38 Health Checks & Readiness | Separate liveness/readiness, fast checks, graceful degradation |
| #39 Data Archival & Retention | Lifecycle management, compliance, archive before delete |

---

*Last Updated: 2025-12-09*
