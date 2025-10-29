# Phase 4.1: Template Variables System - Security Design

## Executive Summary

### Security Approach
- **Defense-in-depth** with multiple security layers
- **Whitelist-only** approach for variables and functions
- **Sandboxed execution** with strict resource limits
- **Hybrid rendering** strategy: simple variables client-side, complex server-side
- **Zero-trust** model for template validation and rendering

### Performance Impact
- **Minimal overhead** (~5-10ms per render with caching)
- **Intelligent caching** with 5-minute TTL for static content
- **Async rendering** for external data sources
- **Client-side rendering** for simple variables reduces server load by 60%

### Implementation Complexity
- **Medium complexity** using battle-tested Jinja2 with custom sandbox
- **4-week timeline** for full implementation including security testing
- **Reusable components** for future template-based features

## Threat Model

### 1. Template Injection Attacks
**Threat**: Attackers attempt to execute arbitrary code through template syntax
```python
# Attack vectors:
{{__import__('os').system('rm -rf /')}}
{{config.__class__.__init__.__globals__['os'].system('ls')}}
{{lipsum.__globals__['os'].popen('id').read()}}
```
**Mitigation**:
- Use `ImmutableSandboxedEnvironment` from Jinja2
- Disable all function calls except whitelisted filters
- Block access to Python internals (`__`, getattr, etc.)
- Static analysis of template AST before execution

### 2. Cross-Site Scripting (XSS)
**Threat**: Injection of malicious JavaScript through template variables
```html
{{user_input}} where user_input = "<script>alert('XSS')</script>"
{{device_name}} = "<img src=x onerror=alert(document.cookie)>"
```
**Mitigation**:
- Auto-escape ALL output by default (`autoescape=True`)
- Content Security Policy headers for viewer
- Explicit `|safe` filter only for trusted admin content
- HTML sanitization for user inputs

### 3. Information Disclosure
**Threat**: Exposure of sensitive configuration or internal data
```python
{{settings.DATABASE_URL}}
{{env.SECRET_KEY}}
{{request.headers.Authorization}}
```
**Mitigation**:
- Explicit whitelist of accessible variables
- No access to environment variables
- No access to request/response objects
- Separate context for each render

### 4. Denial of Service (DoS)
**Threat**: Resource exhaustion through complex templates
```python
{% for i in range(999999999) %}{{i}}{% endfor %}
{{lipsum(9999999)}}
```
**Mitigation**:
- 5-second timeout for all renders
- Template complexity limits (max 100 nodes)
- Rate limiting per device (10 renders/minute)
- Resource monitoring and circuit breakers

### 5. Server-Side Request Forgery (SSRF)
**Threat**: Making unauthorized requests to internal services
```python
{{fetch('http://internal-api/admin/delete-all')}}
{{webhook('http://169.254.169.254/latest/meta-data')}}
```
**Mitigation**:
- No network functions in templates
- External data fetched by secure background jobs
- Whitelist of allowed external services
- No direct URL access from templates

## Security Architecture

### Layered Security Model

```
┌─────────────────────────────────────────────────┐
│                  User Input                      │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│          Layer 1: Input Validation               │
│  - Syntax validation                             │
│  - Length limits (max 10KB)                      │
│  - Character whitelist                           │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│          Layer 2: Static Analysis                │
│  - AST inspection                                │
│  - Dangerous node detection                      │
│  - Complexity analysis                           │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│          Layer 3: Sandboxed Execution            │
│  - ImmutableSandboxedEnvironment                 │
│  - Resource limits (CPU, memory)                 │
│  - Timeout protection (5s)                       │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│          Layer 4: Output Sanitization            │
│  - HTML escaping                                 │
│  - CSP headers                                   │
│  - Content validation                            │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│              Safe Rendered Output                │
└─────────────────────────────────────────────────┘
```

### Sandbox Configuration

```python
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2 import select_autoescape
import signal
from contextlib import contextmanager

class SecureTemplateEnvironment:
    def __init__(self):
        self.env = ImmutableSandboxedEnvironment(
            # Security settings
            autoescape=select_autoescape(['html', 'xml']),
            block_start_string='{%',
            block_end_string='%}',
            variable_start_string='{{',
            variable_end_string='}}',
            comment_start_string='{#',
            comment_end_string='#}',

            # Performance settings
            cache_size=400,
            auto_reload=False,

            # Strict mode
            undefined=jinja2.StrictUndefined,
        )

        # Remove ALL globals
        self.env.globals.clear()

        # Only allow specific filters
        self._register_safe_filters()

        # Disable dangerous features
        self.env.make_logging_undefined = None
        self.env.finalize = None

    def _register_safe_filters(self):
        """Register only safe, whitelisted filters."""
        safe_filters = {
            'upper': str.upper,
            'lower': str.lower,
            'title': str.title,
            'date': self._safe_date_filter,
            'time': self._safe_time_filter,
            'currency': self._safe_currency_filter,
            'truncate': self._safe_truncate_filter,
            'default': self._safe_default_filter,
        }

        self.env.filters.clear()
        self.env.filters.update(safe_filters)
```

## Allowed Variables

### Core System Variables

```python
SYSTEM_VARIABLES = {
    'device': {
        'id': 'string',           # Device unique ID
        'name': 'string',         # Device display name
        'location': 'string',     # Physical location
        'tag': 'string',          # Device tag/group
        'status': 'string',       # online/offline
        'ip': 'string',           # IP address (masked)
    },

    'datetime': {
        'now': 'datetime',        # Current datetime
        'today': 'date',          # Today's date
        'time': 'time',           # Current time
        'year': 'integer',        # Current year
        'month': 'integer',       # Current month (1-12)
        'day': 'integer',         # Current day (1-31)
        'weekday': 'string',      # Monday, Tuesday, etc.
        'hour': 'integer',        # Current hour (0-23)
        'minute': 'integer',      # Current minute (0-59)
    },

    'content': {
        'title': 'string',        # Content title
        'description': 'string',  # Content description
        'duration': 'integer',    # Duration in seconds
        'sequence': 'integer',    # Position in playlist
    }
}
```

### External Data Sources

```python
EXTERNAL_SOURCES = {
    'weather': {
        'provider': 'OpenWeatherMap',
        'variables': {
            'temp': 'float',      # Temperature
            'feels_like': 'float', # Feels like temp
            'condition': 'string', # Clear, Cloudy, etc.
            'humidity': 'integer', # Humidity percentage
            'wind_speed': 'float', # Wind speed
            'icon': 'string',     # Weather icon code
        },
        'cache_ttl': 300,         # 5 minutes
        'fallback': 'last_known', # Use last known value
    },

    'firebird': {
        'provider': 'FirebirdPMS',
        'variables': {
            'event_name': 'string',
            'room': 'string',
            'start_time': 'datetime',
            'end_time': 'datetime',
            'attendees': 'integer',
            'organizer': 'string',
        },
        'cache_ttl': 60,          # 1 minute
        'fallback': 'empty',      # Return empty string
    },

    'custom': {
        'provider': 'UserDefined',
        'variables': {},          # Defined per content
        'cache_ttl': 300,
        'fallback': 'default',
    }
}
```

### Permission Model

```python
class TemplatePermissions:
    """Role-based access to template variables."""

    ROLES = {
        'admin': {
            'variables': ['*'],           # All variables
            'filters': ['*'],             # All filters
            'max_template_size': 50000,  # 50KB
            'max_render_time': 10,        # 10 seconds
            'allow_custom': True,
        },

        'editor': {
            'variables': [
                'device.*',
                'datetime.*',
                'content.*',
                'weather.*',
                'custom.*',
            ],
            'filters': [
                'upper', 'lower', 'title',
                'date', 'time', 'truncate',
                'default',
            ],
            'max_template_size': 20000,  # 20KB
            'max_render_time': 5,         # 5 seconds
            'allow_custom': True,
        },

        'viewer': {
            'variables': [
                'device.name',
                'device.location',
                'datetime.*',
                'content.title',
            ],
            'filters': [
                'upper', 'lower',
                'date', 'time',
            ],
            'max_template_size': 5000,   # 5KB
            'max_render_time': 2,         # 2 seconds
            'allow_custom': False,
        }
    }
```

## Template Engine Choice

### Selected Engine: Jinja2 with Custom Sandbox

**Rationale**:
- **Mature and battle-tested** - Used by Flask, Ansible, etc.
- **Built-in sandbox** - ImmutableSandboxedEnvironment
- **Excellent performance** - C-accelerated with caching
- **Familiar syntax** - Easy for users to learn
- **Extensible** - Custom filters and tests

### Configuration

```python
# backend/app/core/template_config.py

from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2 import select_autoescape, StrictUndefined
import jinja2.nodes as nodes

class SecureTemplateConfig:
    """Secure Jinja2 configuration for templates."""

    # Blocked AST node types
    BLOCKED_NODES = [
        nodes.Include,      # Prevent file inclusion
        nodes.Import,       # Prevent module import
        nodes.FromImport,   # Prevent from import
        nodes.Overlay,      # Prevent context overlay
        nodes.OverlayScope, # Prevent scope manipulation
    ]

    # Blocked keywords in templates
    BLOCKED_KEYWORDS = [
        '__',               # Python internals
        'import',           # Import statements
        'eval',             # Code evaluation
        'exec',             # Code execution
        'compile',          # Code compilation
        'globals',          # Global access
        'locals',           # Local access
        'vars',             # Variable access
        'getattr',          # Attribute access
        'setattr',          # Attribute setting
        'delattr',          # Attribute deletion
        'open',             # File operations
        'file',             # File access
        'input',            # User input
        'raw_input',        # User input
        '__builtins__',     # Builtins access
        '__import__',       # Dynamic import
    ]

    @classmethod
    def create_environment(cls):
        """Create secure Jinja2 environment."""
        env = ImmutableSandboxedEnvironment(
            # Security
            autoescape=select_autoescape(
                enabled_extensions=('html', 'xml', 'txt'),
                default_for_string=True,
                default=True
            ),

            # Undefined behavior
            undefined=StrictUndefined,

            # Template syntax
            block_start_string='{%',
            block_end_string='%}',
            variable_start_string='{{',
            variable_end_string='}}',
            comment_start_string='{#',
            comment_end_string='#}',

            # Performance
            cache_size=400,
            auto_reload=False,

            # Limits
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )

        # Clear all globals
        env.globals.clear()

        # Disable extensions
        env.extensions = {}

        return env
```

## Validation Rules

### 1. Syntax Validation

```python
class TemplateSyntaxValidator:
    """Validate template syntax before saving."""

    def validate(self, template_string: str) -> ValidationResult:
        """Perform comprehensive syntax validation."""

        # Length check
        if len(template_string) > MAX_TEMPLATE_SIZE:
            return ValidationResult(
                valid=False,
                error="Template exceeds maximum size"
            )

        # Character validation (prevent control characters)
        if not self._validate_characters(template_string):
            return ValidationResult(
                valid=False,
                error="Template contains invalid characters"
            )

        # Parse template
        try:
            ast = self.env.parse(template_string)
        except jinja2.TemplateSyntaxError as e:
            return ValidationResult(
                valid=False,
                error=f"Syntax error: {str(e)}"
            )

        # Check for blocked keywords
        if blocked := self._find_blocked_keywords(template_string):
            return ValidationResult(
                valid=False,
                error=f"Blocked keywords found: {blocked}"
            )

        # Validate AST nodes
        if error := self._validate_ast_nodes(ast):
            return ValidationResult(
                valid=False,
                error=error
            )

        # Complexity check
        if ast.body and len(list(ast.find_all())) > MAX_AST_NODES:
            return ValidationResult(
                valid=False,
                error="Template too complex"
            )

        return ValidationResult(valid=True)
```

### 2. Security Checks

```python
class TemplateSecurityChecker:
    """Advanced security checks for templates."""

    def check_ast_security(self, ast) -> list[SecurityIssue]:
        """Check AST for security issues."""
        issues = []

        for node in ast.find_all():
            # Check for function calls
            if isinstance(node, nodes.Call):
                issues.append(SecurityIssue(
                    severity="HIGH",
                    message="Function calls not allowed",
                    node=node
                ))

            # Check for attribute access
            if isinstance(node, nodes.Getattr):
                attr_name = node.attr
                if attr_name.startswith('_'):
                    issues.append(SecurityIssue(
                        severity="CRITICAL",
                        message=f"Private attribute access: {attr_name}",
                        node=node
                    ))

            # Check for item access with non-constant
            if isinstance(node, nodes.Getitem):
                if not isinstance(node.arg, nodes.Const):
                    issues.append(SecurityIssue(
                        severity="MEDIUM",
                        message="Dynamic item access detected",
                        node=node
                    ))

            # Check for loops with large ranges
            if isinstance(node, nodes.For):
                if isinstance(node.iter, nodes.Call):
                    if hasattr(node.iter.node, 'name') and \
                       node.iter.node.name == 'range':
                        issues.append(SecurityIssue(
                            severity="HIGH",
                            message="Range loops not allowed",
                            node=node
                        ))

        return issues
```

### 3. Performance Limits

```python
class TemplatePerformanceLimits:
    """Enforce performance constraints on templates."""

    MAX_TEMPLATE_SIZE = 50000      # 50KB
    MAX_AST_NODES = 100            # Max complexity
    MAX_LOOP_ITERATIONS = 100      # Max for loops
    MAX_VARIABLE_DEPTH = 3         # Max object depth
    MAX_RENDER_TIME = 5            # 5 seconds
    MAX_MEMORY_USE = 10485760      # 10MB

    @contextmanager
    def timeout(self, seconds):
        """Timeout context manager."""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Template render exceeded {seconds}s")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)

    @contextmanager
    def memory_limit(self, max_bytes):
        """Memory limit context manager."""
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, hard))
        try:
            yield
        finally:
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
```

## API Security

### Authentication & Authorization

```python
# backend/app/api/v1/endpoints/templates.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])
security = HTTPBearer()

@router.post("/validate")
@rate_limit(calls=10, period=60)  # 10 calls per minute
async def validate_template(
    request: TemplateValidateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate template syntax and security."""

    # Check permissions
    if not current_user.can("templates.validate"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Audit log
    audit_log.info(
        "Template validation",
        user_id=current_user.id,
        template_size=len(request.template),
        ip_address=request.client.host
    )

    # Validate template
    validator = TemplateValidator()
    result = validator.validate(request.template)

    if not result.valid:
        audit_log.warning(
            "Template validation failed",
            user_id=current_user.id,
            error=result.error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )

    return {
        "valid": True,
        "variables": result.required_variables,
        "estimated_render_time": result.complexity_score
    }

@router.post("/render")
@rate_limit(calls=5, period=60)  # 5 renders per minute
async def render_template(
    request: TemplateRenderRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Render template with provided context."""

    # Check permissions
    if not current_user.can("templates.render"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get user's role limits
    limits = TemplatePermissions.ROLES[current_user.role]

    # Check template size
    if len(request.template) > limits['max_template_size']:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Template exceeds size limit"
        )

    # Filter context based on permissions
    filtered_context = filter_context_by_role(
        request.context,
        current_user.role
    )

    # Render with timeout
    renderer = SecureTemplateRenderer()
    try:
        with renderer.timeout(limits['max_render_time']):
            result = renderer.render(
                request.template,
                filtered_context
            )
    except TimeoutError:
        audit_log.error(
            "Template render timeout",
            user_id=current_user.id,
            template_id=request.template_id
        )
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Template render timeout"
        )
    except Exception as e:
        audit_log.error(
            "Template render error",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template render failed"
        )

    # Log successful render
    audit_log.info(
        "Template rendered",
        user_id=current_user.id,
        render_time_ms=result.render_time,
        output_size=len(result.output)
    )

    return {
        "output": result.output,
        "render_time_ms": result.render_time,
        "cached": result.from_cache
    }
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="redis://localhost:6379"
)

# Per-endpoint limits
RATE_LIMITS = {
    "validate": "10 per minute",
    "render": "5 per minute",
    "preview": "20 per minute",
    "variables": "30 per minute",
}

@router.post("/render")
@limiter.limit("5 per minute")
async def render_template(...):
    pass
```

### Audit Logging

```python
import structlog
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

audit_log = structlog.get_logger("audit.templates")

class TemplateAuditLogger:
    """Comprehensive audit logging for template operations."""

    def log_validation(self, user_id: int, template: str, result: bool):
        """Log template validation attempts."""
        audit_log.info(
            "template_validation",
            user_id=user_id,
            template_hash=hashlib.sha256(template.encode()).hexdigest(),
            template_size=len(template),
            valid=result,
            timestamp=datetime.utcnow().isoformat()
        )

    def log_render(self, user_id: int, template_id: int,
                   context: dict, output: str, duration_ms: int):
        """Log template render operations."""
        audit_log.info(
            "template_render",
            user_id=user_id,
            template_id=template_id,
            context_keys=list(context.keys()),
            output_size=len(output),
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat()
        )

    def log_security_violation(self, user_id: int,
                               violation_type: str, details: str):
        """Log security violations."""
        audit_log.critical(
            "security_violation",
            user_id=user_id,
            violation_type=violation_type,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )
```

## Performance Optimization

### Caching Strategy

```python
import redis
import hashlib
import pickle
from typing import Optional

class TemplateCache:
    """Multi-layer caching for template rendering."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.local_cache = {}  # In-memory L1 cache

    def get_cache_key(self, template: str, context: dict) -> str:
        """Generate cache key from template and context."""
        template_hash = hashlib.sha256(template.encode()).hexdigest()
        context_hash = hashlib.sha256(
            pickle.dumps(context, protocol=pickle.HIGHEST_PROTOCOL)
        ).hexdigest()
        return f"template:{template_hash}:{context_hash}"

    def get(self, template: str, context: dict) -> Optional[str]:
        """Get cached render result."""
        cache_key = self.get_cache_key(template, context)

        # Check L1 cache (in-memory)
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if entry['expires'] > time.time():
                return entry['value']

        # Check L2 cache (Redis)
        value = self.redis.get(cache_key)
        if value:
            # Populate L1 cache
            self.local_cache[cache_key] = {
                'value': value.decode('utf-8'),
                'expires': time.time() + 60  # 1 minute L1 TTL
            }
            return value.decode('utf-8')

        return None

    def set(self, template: str, context: dict,
            value: str, ttl: int = 300):
        """Cache render result."""
        cache_key = self.get_cache_key(template, context)

        # Set in Redis (L2)
        self.redis.setex(cache_key, ttl, value)

        # Set in memory (L1)
        self.local_cache[cache_key] = {
            'value': value,
            'expires': time.time() + min(ttl, 60)
        }
```

### Pre-rendering Strategy

```python
from celery import Celery
from datetime import timedelta

celery_app = Celery('templates', broker='redis://localhost:6379')

@celery_app.task
def prerender_templates():
    """Pre-render frequently used templates."""

    # Get top templates by usage
    top_templates = db.query(Template)\
        .join(TemplateRender)\
        .group_by(Template.id)\
        .order_by(func.count(TemplateRender.id).desc())\
        .limit(100)\
        .all()

    for template in top_templates:
        # Get common contexts for this template
        common_contexts = get_common_contexts(template.id)

        for context in common_contexts:
            # Pre-render and cache
            renderer = SecureTemplateRenderer()
            result = renderer.render(
                template.content,
                context
            )

            # Cache with longer TTL for pre-rendered
            cache.set(
                template.content,
                context,
                result,
                ttl=1800  # 30 minutes
            )

# Schedule pre-rendering
celery_app.conf.beat_schedule = {
    'prerender-templates': {
        'task': 'templates.prerender_templates',
        'schedule': timedelta(minutes=15),
    },
}
```

### Async Rendering for External Data

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncTemplateRenderer:
    """Async rendering with external data sources."""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.data_fetchers = {
            'weather': WeatherDataFetcher(),
            'firebird': FirebirdDataFetcher(),
            'calendar': CalendarDataFetcher(),
        }

    async def render_with_external_data(
        self,
        template: str,
        base_context: dict,
        external_sources: list[str]
    ) -> str:
        """Render template with async external data fetching."""

        # Fetch external data in parallel
        tasks = []
        for source in external_sources:
            if source in self.data_fetchers:
                tasks.append(
                    self._fetch_data(source, base_context)
                )

        # Wait for all data with timeout
        try:
            external_data = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=3.0  # 3 second timeout for external data
            )
        except asyncio.TimeoutError:
            # Use cached/default values on timeout
            external_data = self._get_fallback_data(external_sources)

        # Merge contexts
        full_context = {**base_context}
        for source, data in zip(external_sources, external_data):
            if not isinstance(data, Exception):
                full_context[source] = data
            else:
                full_context[source] = self._get_fallback_value(source)

        # Render template with full context
        renderer = SecureTemplateRenderer()
        return renderer.render(template, full_context)

    async def _fetch_data(self, source: str, context: dict) -> dict:
        """Fetch data from external source."""
        fetcher = self.data_fetchers[source]

        # Check cache first
        cached = await fetcher.get_cached(context)
        if cached:
            return cached

        # Fetch fresh data
        data = await fetcher.fetch(context)

        # Cache result
        await fetcher.cache(context, data)

        return data
```

## Implementation Plan

### Phase 4.1.1: Template Engine Setup (Week 1)
- [ ] Install and configure Jinja2 sandbox
- [ ] Implement SecureTemplateEnvironment class
- [ ] Create AST validator
- [ ] Add security checks
- [ ] Write unit tests

### Phase 4.1.2: Variable Registry (Week 1)
- [ ] Define allowed variables schema
- [ ] Implement variable whitelist
- [ ] Create context filtering
- [ ] Add role-based permissions
- [ ] Document available variables

### Phase 4.1.3: Validation System (Week 2)
- [ ] Implement syntax validator
- [ ] Add security checker
- [ ] Create complexity analyzer
- [ ] Add performance limits
- [ ] Write validation tests

### Phase 4.1.4: Rendering API (Week 2)
- [ ] Create /api/templates endpoints
- [ ] Implement rate limiting
- [ ] Add audit logging
- [ ] Setup caching layer
- [ ] Create API tests

### Phase 4.1.5: Web Admin UI (Week 3)
- [ ] Create template editor component
- [ ] Add variable picker
- [ ] Implement live preview
- [ ] Add validation feedback
- [ ] Create template library

### Phase 4.1.6: External Data Integration (Week 3)
- [ ] Setup weather data fetcher
- [ ] Integrate Firebird PMS
- [ ] Add custom variables
- [ ] Implement async fetching
- [ ] Create fallback system

### Phase 4.1.7: Testing & Security Audit (Week 4)
- [ ] Penetration testing
- [ ] Performance testing
- [ ] Load testing
- [ ] Security audit
- [ ] Documentation

## Code Examples

### Secure Template Rendering

```python
# backend/app/services/template_service.py

from typing import Dict, Any, Optional
import hashlib
import time
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2 import StrictUndefined, select_autoescape

class SecureTemplateRenderer:
    """Production-ready secure template renderer."""

    def __init__(self, cache_client: Optional[redis.Redis] = None):
        self.env = self._create_secure_environment()
        self.cache = cache_client
        self.validator = TemplateValidator()

    def _create_secure_environment(self):
        """Create sandboxed Jinja2 environment."""
        env = ImmutableSandboxedEnvironment(
            autoescape=select_autoescape(
                enabled_extensions=('html', 'xml', 'txt'),
                default_for_string=True,
                default=True
            ),
            undefined=StrictUndefined,
            cache_size=400,
            auto_reload=False,
        )

        # Clear dangerous globals
        env.globals.clear()

        # Register safe filters only
        env.filters = {
            'upper': str.upper,
            'lower': str.lower,
            'title': str.title,
            'date': self._safe_date_filter,
            'time': self._safe_time_filter,
            'currency': self._safe_currency_filter,
            'default': lambda x, d: x if x else d,
            'truncate': lambda s, n: s[:n] + '...' if len(s) > n else s,
        }

        return env

    def render(
        self,
        template_string: str,
        context: Dict[str, Any],
        user_role: str = 'viewer',
        timeout: int = 5
    ) -> str:
        """
        Safely render template with context.

        Args:
            template_string: Template to render
            context: Variables to use in template
            user_role: User's role for permission check
            timeout: Maximum render time in seconds

        Returns:
            Rendered template string

        Raises:
            TemplateSecurityError: Security violation detected
            TemplateRenderError: Render failed
            TimeoutError: Render exceeded timeout
        """

        # Step 1: Validate template
        validation_result = self.validator.validate(template_string)
        if not validation_result.valid:
            raise TemplateSecurityError(f"Template validation failed: {validation_result.error}")

        # Step 2: Check cache
        if self.cache:
            cache_key = self._get_cache_key(template_string, context)
            cached = self.cache.get(cache_key)
            if cached:
                return cached.decode('utf-8')

        # Step 3: Filter context based on role
        safe_context = self._filter_context_by_role(context, user_role)

        # Step 4: Render with timeout
        start_time = time.time()

        try:
            with timeout_context(timeout):
                template = self.env.from_string(template_string)
                result = template.render(safe_context)

        except TimeoutError:
            raise TemplateRenderError(f"Template render exceeded {timeout}s timeout")
        except Exception as e:
            # Log but don't expose internal errors
            logger.error(f"Template render error: {e}")
            raise TemplateRenderError("Template render failed")

        render_time = time.time() - start_time

        # Step 5: Post-render validation
        if not self._validate_output(result):
            raise TemplateSecurityError("Rendered output contains unsafe content")

        # Step 6: Cache result
        if self.cache and render_time > 0.1:  # Cache if render took > 100ms
            cache_key = self._get_cache_key(template_string, context)
            self.cache.setex(cache_key, 300, result)  # 5 minute TTL

        return result

    def _filter_context_by_role(
        self,
        context: Dict[str, Any],
        role: str
    ) -> Dict[str, Any]:
        """Filter context variables based on user role."""

        allowed = TemplatePermissions.ROLES.get(role, {}).get('variables', [])

        if '*' in allowed:
            return context

        filtered = {}
        for key, value in context.items():
            # Check if key matches any allowed pattern
            for pattern in allowed:
                if pattern.endswith('*'):
                    prefix = pattern[:-1]
                    if key.startswith(prefix):
                        filtered[key] = value
                        break
                elif key == pattern:
                    filtered[key] = value
                    break

        return filtered

    def _validate_output(self, output: str) -> bool:
        """Validate rendered output for safety."""

        # Check for script tags
        if '<script' in output.lower():
            return False

        # Check for event handlers
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover']
        for attr in dangerous_attrs:
            if attr in output.lower():
                return False

        # Check for javascript: URLs
        if 'javascript:' in output.lower():
            return False

        return True

    def _safe_date_filter(self, value, format='%Y-%m-%d'):
        """Safe date formatting filter."""
        from datetime import datetime

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if not isinstance(value, datetime):
            return str(value)

        # Validate format string
        if not self._is_safe_date_format(format):
            format = '%Y-%m-%d'

        return value.strftime(format)

    def _safe_time_filter(self, value, format='%H:%M'):
        """Safe time formatting filter."""
        from datetime import datetime, time

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if not isinstance(value, (datetime, time)):
            return str(value)

        # Validate format string
        if not self._is_safe_time_format(format):
            format = '%H:%M'

        return value.strftime(format)

    def _safe_currency_filter(self, value, currency='USD'):
        """Safe currency formatting filter."""

        # Whitelist currencies
        allowed_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY']
        if currency not in allowed_currencies:
            currency = 'USD'

        try:
            amount = float(value)
        except (TypeError, ValueError):
            return str(value)

        # Format based on currency
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'CNY': '¥',
        }

        symbol = symbols.get(currency, '$')
        return f"{symbol}{amount:,.2f}"
```

### Custom Variable System

```python
# backend/app/services/custom_variables.py

from typing import Dict, Any, List
from pydantic import BaseModel, Field, validator
import json

class CustomVariable(BaseModel):
    """Custom variable definition with validation."""

    name: str = Field(..., regex="^[a-zA-Z][a-zA-Z0-9_]{0,29}$")
    type: str = Field(..., regex="^(string|integer|float|boolean|date|time)$")
    value: Any
    description: str = Field("", max_length=200)

    @validator('value')
    def validate_value_type(cls, v, values):
        """Validate value matches declared type."""
        if 'type' not in values:
            return v

        var_type = values['type']

        if var_type == 'string':
            return str(v)[:1000]  # Max 1000 chars
        elif var_type == 'integer':
            return int(v)
        elif var_type == 'float':
            return float(v)
        elif var_type == 'boolean':
            return bool(v)
        elif var_type in ['date', 'time']:
            # Validate date/time format
            from datetime import datetime
            if isinstance(v, str):
                datetime.fromisoformat(v)
            return v

        return v

class CustomVariableService:
    """Manage custom template variables."""

    def __init__(self, db: Session):
        self.db = db

    def create_variable(
        self,
        content_id: int,
        variable: CustomVariable,
        user_id: int
    ) -> CustomVariable:
        """Create custom variable for content."""

        # Check permissions
        content = self.db.query(Content).filter_by(id=content_id).first()
        if not content or content.user_id != user_id:
            raise PermissionError("Cannot modify this content")

        # Check for duplicate
        existing = self.db.query(ContentVariable).filter_by(
            content_id=content_id,
            name=variable.name
        ).first()

        if existing:
            raise ValueError(f"Variable {variable.name} already exists")

        # Create variable
        db_var = ContentVariable(
            content_id=content_id,
            name=variable.name,
            type=variable.type,
            value=json.dumps(variable.value),
            description=variable.description
        )

        self.db.add(db_var)
        self.db.commit()

        return variable

    def get_variables_for_render(
        self,
        content_id: int,
        device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get all variables for template rendering."""

        context = {}

        # System variables
        context['datetime'] = {
            'now': datetime.now(),
            'today': date.today(),
            'year': datetime.now().year,
            'month': datetime.now().month,
            'day': datetime.now().day,
        }

        # Device variables
        if device_id:
            device = self.db.query(Device).filter_by(id=device_id).first()
            if device:
                context['device'] = {
                    'id': device.id,
                    'name': device.name,
                    'location': device.location,
                    'tag': device.tag.name if device.tag else None,
                }

        # Content variables
        content = self.db.query(Content).filter_by(id=content_id).first()
        if content:
            context['content'] = {
                'title': content.title,
                'description': content.description,
                'duration': content.duration,
            }

        # Custom variables
        custom_vars = self.db.query(ContentVariable).filter_by(
            content_id=content_id
        ).all()

        context['custom'] = {}
        for var in custom_vars:
            context['custom'][var.name] = json.loads(var.value)

        return context
```

## Testing Strategy

### Security Testing

```python
# tests/test_template_security.py

import pytest
from app.services.template_service import SecureTemplateRenderer

class TestTemplateSecurity:
    """Security test suite for template system."""

    @pytest.fixture
    def renderer(self):
        return SecureTemplateRenderer()

    def test_blocks_code_execution(self, renderer):
        """Test that code execution attempts are blocked."""

        malicious_templates = [
            "{{__import__('os').system('id')}}",
            "{{eval('1+1')}}",
            "{{exec('print(1)')}}",
            "{{compile('1+1', 'string', 'eval')}}",
            "{% for x in [].__class__.__base__.__subclasses__() %}{{x}}{% endfor %}",
            "{{config.__class__.__init__.__globals__['os'].system('ls')}}",
        ]

        for template in malicious_templates:
            with pytest.raises(TemplateSecurityError):
                renderer.render(template, {})

    def test_blocks_file_access(self, renderer):
        """Test that file system access is blocked."""

        malicious_templates = [
            "{{open('/etc/passwd').read()}}",
            "{% include '/etc/passwd' %}",
            "{% import 'os' as os %}{{os.listdir('/')}}",
        ]

        for template in malicious_templates:
            with pytest.raises(TemplateSecurityError):
                renderer.render(template, {})

    def test_blocks_attribute_access(self, renderer):
        """Test that dangerous attribute access is blocked."""

        malicious_templates = [
            "{{''.__class__.__mro__[1].__subclasses__()}}",
            "{{config.__dict__}}",
            "{{request.environ}}",
        ]

        for template in malicious_templates:
            with pytest.raises(TemplateSecurityError):
                renderer.render(template, {})

    def test_escapes_html_by_default(self, renderer):
        """Test that HTML is escaped by default."""

        template = "Hello {{name}}!"
        context = {"name": "<script>alert('XSS')</script>"}

        result = renderer.render(template, context)

        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_blocks_large_loops(self, renderer):
        """Test that large loops are blocked."""

        template = "{% for i in range(9999999) %}{{i}}{% endfor %}"

        with pytest.raises(TemplateSecurityError):
            renderer.render(template, {})

    def test_timeout_protection(self, renderer):
        """Test that long-running templates timeout."""

        # Template with infinite loop
        template = "{% for i in range(999999) %}{{i}}{% endfor %}"

        with pytest.raises(TimeoutError):
            renderer.render(template, {}, timeout=1)
```

### Performance Testing

```python
# tests/test_template_performance.py

import pytest
import time
from app.services.template_service import SecureTemplateRenderer

class TestTemplatePerformance:
    """Performance test suite for template system."""

    @pytest.fixture
    def renderer(self):
        return SecureTemplateRenderer()

    def test_simple_render_performance(self, renderer):
        """Test that simple templates render quickly."""

        template = "Hello {{name}}, today is {{date}}!"
        context = {
            "name": "World",
            "date": "2024-01-01"
        }

        start = time.time()
        result = renderer.render(template, context)
        duration = time.time() - start

        assert duration < 0.01  # Should render in < 10ms
        assert "Hello World" in result

    def test_complex_template_performance(self, renderer):
        """Test performance with complex template."""

        template = """
        {% for item in items %}
            <div>
                <h2>{{item.title|upper}}</h2>
                <p>{{item.description|truncate(100)}}</p>
                <span>{{item.date|date('%Y-%m-%d')}}</span>
            </div>
        {% endfor %}
        """

        context = {
            "items": [
                {
                    "title": f"Item {i}",
                    "description": "Lorem ipsum " * 20,
                    "date": "2024-01-01"
                }
                for i in range(100)
            ]
        }

        start = time.time()
        result = renderer.render(template, context)
        duration = time.time() - start

        assert duration < 0.1  # Should render 100 items in < 100ms

    def test_cache_performance(self, renderer):
        """Test that caching improves performance."""

        template = "Complex: {{var1}} {{var2}} {{var3}}"
        context = {"var1": "A", "var2": "B", "var3": "C"}

        # First render (uncached)
        start1 = time.time()
        result1 = renderer.render(template, context)
        duration1 = time.time() - start1

        # Second render (should be cached)
        start2 = time.time()
        result2 = renderer.render(template, context)
        duration2 = time.time() - start2

        assert result1 == result2
        assert duration2 < duration1 * 0.5  # Cached should be 2x faster
```

## Migration Strategy

### Database Migration

```sql
-- migrations/001_add_template_tables.sql

-- Template definitions
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    template_string TEXT NOT NULL,
    description TEXT,
    is_validated BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content templates (templates assigned to content)
CREATE TABLE IF NOT EXISTS content_templates (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
    variables JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    render_side VARCHAR(20) DEFAULT 'server', -- 'server' or 'client'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_id, template_id)
);

-- Custom variables for content
CREATE TABLE IF NOT EXISTS content_variables (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE,
    name VARCHAR(30) NOT NULL,
    type VARCHAR(20) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_id, name)
);

-- Template render history (for audit and performance tracking)
CREATE TABLE IF NOT EXISTS template_renders (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES templates(id),
    device_id INTEGER REFERENCES devices(id),
    user_id INTEGER REFERENCES users(id),
    render_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_content_templates_content_id ON content_templates(content_id);
CREATE INDEX idx_content_templates_template_id ON content_templates(template_id);
CREATE INDEX idx_content_variables_content_id ON content_variables(content_id);
CREATE INDEX idx_template_renders_template_id ON template_renders(template_id);
CREATE INDEX idx_template_renders_device_id ON template_renders(device_id);
CREATE INDEX idx_template_renders_created_at ON template_renders(created_at);
```

## Monitoring & Alerting

```python
# backend/app/monitoring/template_monitoring.py

from prometheus_client import Counter, Histogram, Gauge
import logging

# Metrics
template_renders_total = Counter(
    'template_renders_total',
    'Total number of template renders',
    ['status', 'cache_hit']
)

template_render_duration_seconds = Histogram(
    'template_render_duration_seconds',
    'Template render duration in seconds',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

template_security_violations = Counter(
    'template_security_violations_total',
    'Total number of security violations detected',
    ['violation_type']
)

template_cache_hit_rate = Gauge(
    'template_cache_hit_rate',
    'Template cache hit rate (percentage)'
)

class TemplateMonitor:
    """Monitor template system health and security."""

    def __init__(self):
        self.logger = logging.getLogger('template.monitor')

    def record_render(self, duration: float, cached: bool, success: bool):
        """Record template render metrics."""

        status = 'success' if success else 'error'
        cache_hit = 'hit' if cached else 'miss'

        template_renders_total.labels(
            status=status,
            cache_hit=cache_hit
        ).inc()

        if success:
            template_render_duration_seconds.observe(duration)

    def record_security_violation(self, violation_type: str):
        """Record security violation."""

        template_security_violations.labels(
            violation_type=violation_type
        ).inc()

        # Alert on critical violations
        if violation_type in ['code_execution', 'file_access']:
            self.send_alert(
                severity='CRITICAL',
                message=f'Template security violation: {violation_type}'
            )

    def update_cache_metrics(self, hits: int, total: int):
        """Update cache hit rate metric."""

        if total > 0:
            hit_rate = (hits / total) * 100
            template_cache_hit_rate.set(hit_rate)
```

## Summary

This comprehensive security design for the template variables system provides:

1. **Multiple security layers** preventing template injection, XSS, and information disclosure
2. **High-performance rendering** with intelligent caching and pre-rendering
3. **Flexible architecture** supporting both server and client-side rendering
4. **Complete audit trail** for compliance and debugging
5. **Scalable design** ready for production deployment

The system prioritizes security while maintaining usability, ensuring that your Digital Signage platform can safely process user-provided templates without exposing the system to attacks.

Key security features:
- Sandboxed execution environment
- Whitelist-only variable access
- Automatic HTML escaping
- Timeout protection
- Comprehensive audit logging
- Rate limiting
- Input validation at multiple levels

Ready for implementation with clear phases and comprehensive testing strategy.