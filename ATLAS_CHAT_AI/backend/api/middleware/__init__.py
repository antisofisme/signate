"""
API Middleware.

Middleware stack (applied in reverse order):
Request → RequestId → RateLimit → Tenant → Auth → Audit → Handler
"""

from .tenant import TenantMiddleware
from .error_handler import error_handler_middleware, ErrorHandlerMiddleware
from .rate_limit import RateLimitMiddleware, RateLimiter, RateLimitExceeded
from .auth import AuthMiddleware, create_jwt_token, decode_jwt_token
from .audit import AuditMiddleware, RequestIdMiddleware

__all__ = [
    # Error handling
    "error_handler_middleware",
    "ErrorHandlerMiddleware",
    # Request tracking
    "RequestIdMiddleware",
    # Rate limiting
    "RateLimitMiddleware",
    "RateLimiter",
    "RateLimitExceeded",
    # Tenant resolution
    "TenantMiddleware",
    # Authentication
    "AuthMiddleware",
    "create_jwt_token",
    "decode_jwt_token",
    # Audit logging
    "AuditMiddleware",
]
