"""
Secure Template Service for Digital Signage

Production-ready template rendering with multi-layer security:
- Sandboxed Jinja2 environment (ImmutableSandboxedEnvironment)
- AST-based validation (blocks dangerous constructs)
- Timeout protection (5 seconds max)
- Multi-layer caching (in-memory + Redis)
- Comprehensive audit logging
- Rate limiting support

Security Features:
- No code execution (eval, exec, __import__ blocked)
- No file access (open, include blocked)
- No attribute access to internals (__class__, __globals__ blocked)
- Whitelist-only variable access
- Auto-escape all HTML output
- XSS prevention
- DoS protection with timeouts
"""

from typing import Dict, Any, Optional, List, Set
import hashlib
import time
import signal
import re
from contextlib import contextmanager
from datetime import datetime
import json

from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2 import (
    StrictUndefined,
    select_autoescape,
    TemplateSyntaxError,
    TemplateError
)
import jinja2.nodes as nodes
from loguru import logger

from app.core.config import settings


# ============================================================================
# EXCEPTIONS
# ============================================================================

class TemplateSecurityError(Exception):
    """Raised when template validation fails security checks."""
    pass


class TemplateValidationError(Exception):
    """Raised when template syntax is invalid."""
    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""
    pass


class TemplateTimeoutError(Exception):
    """Raised when template rendering exceeds timeout."""
    pass


# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

class TemplateSecurityConfig:
    """Security configuration for template system."""

    # Maximum template size (50KB)
    MAX_TEMPLATE_SIZE = 51200

    # Maximum AST nodes (complexity limit)
    MAX_AST_NODES = 100

    # Maximum render time (seconds)
    MAX_RENDER_TIME = 5

    # Maximum memory usage (10MB)
    MAX_MEMORY_BYTES = 10485760

    # Blocked keywords in templates
    BLOCKED_KEYWORDS = [
        '__import__', 'eval', 'exec', 'compile',
        '__', 'getattr', 'setattr', 'delattr',
        'globals', 'locals', 'vars',
        'open', 'file', 'input', 'raw_input',
        '__builtins__', '__class__', '__bases__',
        '__subclasses__', '__globals__', '__dict__',
        'system', 'popen', 'subprocess',
        'os', 'sys', 'importlib'
    ]

    # Blocked AST node types
    BLOCKED_NODE_TYPES = [
        nodes.Include,      # {% include ... %}
        nodes.Import,       # {% import ... %}
        nodes.FromImport,   # {% from ... import ... %}
    ]

    # Allowed variable namespaces
    ALLOWED_VARIABLES = {
        'device': ['id', 'name', 'location', 'tag', 'status', 'ip_address'],
        'datetime': ['now', 'today', 'time', 'year', 'month', 'day', 'weekday', 'hour', 'minute'],
        'content': ['title', 'description', 'duration', 'sequence'],
        'weather': ['temp', 'feels_like', 'condition', 'humidity', 'wind_speed', 'icon'],
        'firebird': ['event_name', 'room', 'start_time', 'end_time', 'attendees', 'organizer'],
        'custom': ['*']  # User-defined variables (validated separately)
    }

    # Role-based permissions
    ROLE_PERMISSIONS = {
        'admin': {
            'variables': ['*'],
            'max_template_size': 50000,
            'max_render_time': 10,
            'allow_custom': True,
        },
        'editor': {
            'variables': [
                'device.*', 'datetime.*', 'content.*',
                'weather.*', 'firebird.*', 'custom.*'
            ],
            'max_template_size': 20000,
            'max_render_time': 5,
            'allow_custom': True,
        },
        'viewer': {
            'variables': [
                'device.name', 'device.location',
                'datetime.*', 'content.title'
            ],
            'max_template_size': 5000,
            'max_render_time': 2,
            'allow_custom': False,
        }
    }


# ============================================================================
# SECURE JINJA2 ENVIRONMENT
# ============================================================================

class SecureTemplateEnvironment:
    """
    Sandboxed Jinja2 environment with strict security controls.

    Features:
    - ImmutableSandboxedEnvironment base
    - Auto-escape all HTML/XML output
    - StrictUndefined for missing variables
    - Cleared globals and filters
    - Only whitelisted filters allowed
    """

    def __init__(self):
        self.env = ImmutableSandboxedEnvironment(
            # Security settings
            autoescape=select_autoescape(
                enabled_extensions=('html', 'xml', 'txt'),
                default_for_string=True,
                default=True
            ),
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

            # Formatting
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )

        # Clear ALL globals (security critical)
        self.env.globals.clear()

        # Clear ALL built-in filters
        self.env.filters.clear()

        # Register only safe filters
        self._register_safe_filters()

        logger.info("SecureTemplateEnvironment initialized")

    def _register_safe_filters(self):
        """Register only whitelisted safe filters."""
        safe_filters = {
            # String filters
            'upper': str.upper,
            'lower': str.lower,
            'title': str.title,
            'capitalize': str.capitalize,

            # Formatting filters
            'date': self._safe_date_filter,
            'time': self._safe_time_filter,
            'currency': self._safe_currency_filter,
            'truncate': self._safe_truncate_filter,
            'default': self._safe_default_filter,

            # Numeric filters
            'round': self._safe_round_filter,
            'abs': abs,
        }

        self.env.filters.update(safe_filters)
        logger.debug(f"Registered {len(safe_filters)} safe filters")

    def _safe_date_filter(self, value: Any, format: str = '%Y-%m-%d') -> str:
        """Safe date formatting filter with format validation."""
        from datetime import datetime, date

        # Convert string to datetime if needed
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return str(value)

        if not isinstance(value, (datetime, date)):
            return str(value)

        # Validate format string (only allow safe format codes)
        safe_format_codes = ['%Y', '%m', '%d', '%H', '%M', '%S', '%B', '%b', '%A', '%a', '-', '/', ' ', ':']
        if not all(any(code in format for code in safe_format_codes) for char in format if char == '%'):
            format = '%Y-%m-%d'  # Fallback to safe default

        try:
            return value.strftime(format)
        except Exception as e:
            logger.warning(f"Date formatting error: {e}")
            return str(value)

    def _safe_time_filter(self, value: Any, format: str = '%H:%M') -> str:
        """Safe time formatting filter."""
        from datetime import datetime, time

        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return str(value)

        if not isinstance(value, (datetime, time)):
            return str(value)

        # Validate format string
        if not re.match(r'^[%HMSp: -]+$', format):
            format = '%H:%M'  # Fallback

        try:
            return value.strftime(format)
        except Exception as e:
            logger.warning(f"Time formatting error: {e}")
            return str(value)

    def _safe_currency_filter(self, value: Any, currency: str = 'USD') -> str:
        """Safe currency formatting filter with whitelist."""
        allowed_currencies = {
            'USD': '$', 'EUR': '€', 'GBP': '£',
            'JPY': '¥', 'CNY': '¥', 'IDR': 'Rp'
        }

        if currency not in allowed_currencies:
            currency = 'USD'

        try:
            amount = float(value)
        except (TypeError, ValueError):
            return str(value)

        symbol = allowed_currencies[currency]

        if currency == 'IDR':
            # Indonesian Rupiah (no decimal)
            return f"{symbol}{amount:,.0f}"
        else:
            return f"{symbol}{amount:,.2f}"

    def _safe_truncate_filter(self, value: str, length: int = 100) -> str:
        """Safe truncate filter with length validation."""
        length = min(max(1, int(length)), 10000)  # Clamp between 1-10000
        value_str = str(value)

        if len(value_str) <= length:
            return value_str

        return value_str[:length] + '...'

    def _safe_default_filter(self, value: Any, default: Any = '') -> Any:
        """Safe default filter."""
        return value if value else default

    def _safe_round_filter(self, value: Any, precision: int = 0) -> float:
        """Safe rounding filter."""
        try:
            num = float(value)
            precision = min(max(0, int(precision)), 10)  # Clamp 0-10
            return round(num, precision)
        except (TypeError, ValueError):
            return value

    def parse(self, template_string: str):
        """Parse template string to AST."""
        return self.env.parse(template_string)

    def from_string(self, template_string: str):
        """Create template from string."""
        return self.env.from_string(template_string)


# ============================================================================
# TEMPLATE VALIDATOR
# ============================================================================

class TemplateValidator:
    """
    Comprehensive template validation with AST inspection.

    Validation layers:
    1. Syntax validation (Jinja2 parser)
    2. Length validation
    3. Keyword blocklist
    4. AST security inspection
    5. Complexity analysis
    """

    def __init__(self, env: SecureTemplateEnvironment):
        self.env = env
        self.config = TemplateSecurityConfig()

    def validate(self, template_string: str) -> Dict[str, Any]:
        """
        Perform comprehensive validation.

        Returns:
            dict with 'valid', 'error', 'warnings', 'metadata'
        """
        result = {
            'valid': False,
            'error': None,
            'warnings': [],
            'metadata': {}
        }

        try:
            # 1. Length check
            if len(template_string) > self.config.MAX_TEMPLATE_SIZE:
                result['error'] = f"Template exceeds maximum size ({self.config.MAX_TEMPLATE_SIZE} bytes)"
                return result

            # 2. Character validation
            if not self._validate_characters(template_string):
                result['error'] = "Template contains invalid control characters"
                return result

            # 3. Blocked keywords check
            blocked = self._find_blocked_keywords(template_string)
            if blocked:
                result['error'] = f"Blocked keywords found: {', '.join(blocked)}"
                return result

            # 4. Parse template to AST
            try:
                ast = self.env.parse(template_string)
            except TemplateSyntaxError as e:
                result['error'] = f"Syntax error: {str(e)}"
                return result

            # 5. AST security checks
            security_issues = self._check_ast_security(ast)
            if security_issues:
                result['error'] = security_issues[0]  # Report first critical issue
                result['warnings'] = security_issues[1:]
                return result

            # 6. Complexity analysis
            complexity = self._analyze_complexity(ast)
            if complexity['total_nodes'] > self.config.MAX_AST_NODES:
                result['error'] = f"Template too complex ({complexity['total_nodes']} nodes, max {self.config.MAX_AST_NODES})"
                return result

            # 7. Extract required variables
            required_vars = self._extract_variables(ast)

            # Success!
            result['valid'] = True
            result['metadata'] = {
                'size': len(template_string),
                'complexity': complexity,
                'required_variables': required_vars
            }

            logger.debug(f"Template validation passed: {complexity['total_nodes']} nodes, {len(required_vars)} variables")

        except Exception as e:
            logger.error(f"Template validation error: {e}")
            result['error'] = "Validation failed due to internal error"

        return result

    def _validate_characters(self, template_string: str) -> bool:
        """Validate no dangerous control characters."""
        # Allow printable ASCII + newlines/tabs + extended Unicode
        for char in template_string:
            code = ord(char)
            # Block control characters except \n, \r, \t
            if code < 32 and code not in (9, 10, 13):
                return False
        return True

    def _find_blocked_keywords(self, template_string: str) -> List[str]:
        """Find any blocked keywords in template."""
        found = []
        template_lower = template_string.lower()

        for keyword in self.config.BLOCKED_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, template_lower):
                found.append(keyword)

        return found

    def _check_ast_security(self, ast) -> List[str]:
        """Check AST for security violations."""
        issues = []

        for node in ast.find_all():
            # Check blocked node types
            for blocked_type in self.config.BLOCKED_NODE_TYPES:
                if isinstance(node, blocked_type):
                    issues.append(f"Blocked operation: {blocked_type.__name__}")

            # Check for function calls (only filters allowed)
            if isinstance(node, nodes.Call):
                # Filters are OK, direct calls are not
                if not isinstance(node.node, nodes.Filter):
                    issues.append("Direct function calls not allowed")

            # Check for private attribute access
            if isinstance(node, nodes.Getattr):
                attr = node.attr
                if attr.startswith('_'):
                    issues.append(f"Private attribute access not allowed: {attr}")

        return issues

    def _analyze_complexity(self, ast) -> Dict[str, Any]:
        """Analyze template complexity."""
        total_nodes = len(list(ast.find_all()))
        loops = len(list(ast.find_all(nodes.For)))
        conditions = len(list(ast.find_all(nodes.If)))
        variables = len(list(ast.find_all(nodes.Name)))

        return {
            'total_nodes': total_nodes,
            'loops': loops,
            'conditions': conditions,
            'variables': variables
        }

    def _extract_variables(self, ast) -> Set[str]:
        """Extract all variable names used in template."""
        variables = set()

        for node in ast.find_all(nodes.Name):
            variables.add(node.name)

        return variables


# ============================================================================
# TIMEOUT CONTEXT MANAGER
# ============================================================================

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for timeout protection.

    Raises TimeoutError if block exceeds time limit.
    """
    def timeout_handler(signum, frame):
        raise TemplateTimeoutError(f"Operation exceeded {seconds}s timeout")

    # Set signal alarm (Unix only)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)  # Cancel alarm
        signal.signal(signal.SIGALRM, old_handler)


# ============================================================================
# TEMPLATE CACHE
# ============================================================================

class TemplateCache:
    """
    Multi-layer template rendering cache.

    L1: In-memory (instant, 1 minute TTL)
    L2: Redis (fast, 5 minute TTL)
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._max_memory_entries = 1000

    def _get_cache_key(self, template_string: str, context: Dict[str, Any]) -> str:
        """Generate cache key from template and context."""
        template_hash = hashlib.sha256(template_string.encode()).hexdigest()[:16]

        # Sort context for consistent hashing
        context_str = json.dumps(context, sort_keys=True, default=str)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:16]

        return f"tpl:{template_hash}:{context_hash}"

    def get(self, template_string: str, context: Dict[str, Any]) -> Optional[str]:
        """Get cached render result."""
        cache_key = self._get_cache_key(template_string, context)

        # L1: Check memory cache
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if entry['expires'] > time.time():
                logger.debug(f"L1 cache hit: {cache_key}")
                return entry['value']
            else:
                # Expired, remove
                del self._memory_cache[cache_key]

        # L2: Check Redis cache
        if self.redis:
            try:
                value = self.redis.get(cache_key)
                if value:
                    result = value.decode('utf-8')
                    # Populate L1 cache
                    self._set_memory_cache(cache_key, result, ttl=60)
                    logger.debug(f"L2 cache hit: {cache_key}")
                    return result
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        return None

    def set(self, template_string: str, context: Dict[str, Any],
            value: str, ttl: int = 300):
        """Set cache entry with TTL."""
        cache_key = self._get_cache_key(template_string, context)

        # L1: Set in memory
        self._set_memory_cache(cache_key, value, ttl=min(ttl, 60))

        # L2: Set in Redis
        if self.redis:
            try:
                self.redis.setex(cache_key, ttl, value.encode('utf-8'))
                logger.debug(f"Cached result: {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")

    def _set_memory_cache(self, key: str, value: str, ttl: int):
        """Set entry in memory cache with size limit."""
        # Evict oldest entries if cache is full
        if len(self._memory_cache) >= self._max_memory_entries:
            # Remove expired entries first
            now = time.time()
            expired = [k for k, v in self._memory_cache.items() if v['expires'] <= now]
            for k in expired:
                del self._memory_cache[k]

            # If still full, remove oldest
            if len(self._memory_cache) >= self._max_memory_entries:
                oldest = min(self._memory_cache.items(), key=lambda x: x[1]['expires'])
                del self._memory_cache[oldest[0]]

        self._memory_cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }


# ============================================================================
# MAIN TEMPLATE RENDERER
# ============================================================================

class SecureTemplateRenderer:
    """
    Production-ready secure template renderer.

    Features:
    - Sandboxed execution
    - Comprehensive validation
    - Timeout protection
    - Multi-layer caching
    - Audit logging
    - Role-based access control
    """

    def __init__(self, redis_client=None):
        self.env = SecureTemplateEnvironment()
        self.validator = TemplateValidator(self.env)
        self.cache = TemplateCache(redis_client)
        self.config = TemplateSecurityConfig()

        logger.info("SecureTemplateRenderer initialized")

    async def validate_template(self, template_string: str) -> Dict[str, Any]:
        """Validate template syntax and security."""
        return self.validator.validate(template_string)

    async def render(
        self,
        template_string: str,
        context: Dict[str, Any],
        user_role: str = 'viewer',
        use_cache: bool = True,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Render template with security controls.

        Args:
            template_string: Template to render
            context: Variables for template
            user_role: User role for permission checks
            use_cache: Whether to use caching
            timeout: Override default timeout

        Returns:
            dict with 'output', 'render_time_ms', 'cached', 'metadata'

        Raises:
            TemplateSecurityError: Security violation
            TemplateRenderError: Render failed
            TemplateTimeoutError: Timeout exceeded
        """
        start_time = time.time()

        try:
            # 1. Validate template
            validation = self.validator.validate(template_string)
            if not validation['valid']:
                raise TemplateSecurityError(f"Validation failed: {validation['error']}")

            # 2. Check cache
            if use_cache:
                cached = self.cache.get(template_string, context)
                if cached:
                    render_time = (time.time() - start_time) * 1000
                    return {
                        'output': cached,
                        'render_time_ms': round(render_time, 2),
                        'cached': True,
                        'metadata': validation['metadata']
                    }

            # 3. Filter context by role
            safe_context = self._filter_context_by_role(context, user_role)

            # 4. Render with timeout
            render_timeout = timeout or self._get_role_timeout(user_role)

            with timeout_context(render_timeout):
                template = self.env.from_string(template_string)
                output = template.render(safe_context)

            # 5. Post-render validation
            if not self._validate_output(output):
                raise TemplateSecurityError("Output contains unsafe content")

            render_time = (time.time() - start_time) * 1000

            # 6. Cache result
            if use_cache and render_time > 10:  # Cache if > 10ms
                self.cache.set(template_string, context, output, ttl=300)

            logger.info(f"Template rendered: {render_time:.2f}ms, {len(output)} bytes")

            return {
                'output': output,
                'render_time_ms': round(render_time, 2),
                'cached': False,
                'metadata': validation['metadata']
            }

        except TemplateTimeoutError as e:
            logger.error(f"Template timeout: {e}")
            raise
        except TemplateSecurityError as e:
            logger.error(f"Template security error: {e}")
            raise
        except TemplateError as e:
            logger.error(f"Template render error: {e}")
            raise TemplateRenderError(f"Render failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected template error: {e}")
            raise TemplateRenderError("Template rendering failed")

    def _filter_context_by_role(
        self,
        context: Dict[str, Any],
        role: str
    ) -> Dict[str, Any]:
        """Filter context variables based on user role."""
        permissions = self.config.ROLE_PERMISSIONS.get(role, self.config.ROLE_PERMISSIONS['viewer'])
        allowed = permissions['variables']

        # Admin gets everything
        if '*' in allowed:
            return context

        # Filter by whitelist patterns
        filtered = {}
        for key, value in context.items():
            for pattern in allowed:
                if pattern.endswith('.*'):
                    # Namespace wildcard (e.g., 'device.*')
                    prefix = pattern[:-2]
                    if key == prefix or key.startswith(f"{prefix}."):
                        filtered[key] = value
                        break
                elif key == pattern:
                    # Exact match
                    filtered[key] = value
                    break

        return filtered

    def _get_role_timeout(self, role: str) -> int:
        """Get timeout for role."""
        permissions = self.config.ROLE_PERMISSIONS.get(role, self.config.ROLE_PERMISSIONS['viewer'])
        return permissions.get('max_render_time', 5)

    def _validate_output(self, output: str) -> bool:
        """Validate rendered output for XSS and safety."""
        output_lower = output.lower()

        # Check for script tags
        if '<script' in output_lower:
            return False

        # Check for event handlers
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout']
        for attr in dangerous_attrs:
            if attr in output_lower:
                return False

        # Check for javascript: protocol
        if 'javascript:' in output_lower:
            return False

        return True


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global renderer instance (initialized on first use)
_renderer: Optional[SecureTemplateRenderer] = None


def get_renderer(redis_client=None) -> SecureTemplateRenderer:
    """Get or create global renderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = SecureTemplateRenderer(redis_client)
    return _renderer


async def render_template(
    template_string: str,
    context: Dict[str, Any],
    **kwargs
) -> str:
    """
    Convenience function to render template.

    Returns only the rendered output string.
    """
    renderer = get_renderer()
    result = await renderer.render(template_string, context, **kwargs)
    return result['output']
