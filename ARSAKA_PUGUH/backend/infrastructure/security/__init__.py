"""
Security Infrastructure

Provides enterprise security features:
- Rate limiting
- Security headers
- Security audit logging

Source: Phase 2 Design & Execution Plan - Section 4.3

NOTE: Redis-based rate limiting is OPTIONAL for Phase A.
If redis is not installed, only in-memory rate limiter is available.
"""

# Redis-based rate limiting
from .rate_limiter import RateLimiter, RateLimitMiddleware
REDIS_RATE_LIMITER_AVAILABLE = True

# In-memory rate limiting (always available)
from .memory_rate_limiter import InMemoryRateLimiter, InMemoryRateLimitMiddleware

# Security headers (always available)
from .headers import SecurityHeadersMiddleware

# CSRF protection (always available)
from .csrf import CSRFMiddleware

# Redirect validation (always available)
from .redirect_validator import (
    RedirectValidator,
    get_redirect_validator,
    validate_redirect_url,
    get_validated_redirect,
)

# Audit logging (always available)
from .audit_log import (
    SecurityAuditService,
    SecurityEvent,
    EventCategory,
    EventType,
    Severity,
    Status,
    get_security_audit_service,
)

__all__ = [
    # Availability flags
    "REDIS_RATE_LIMITER_AVAILABLE",
    # Rate Limiting (Redis-based - optional)
    "RateLimiter",
    "RateLimitMiddleware",
    # Rate Limiting (In-Memory - always available)
    "InMemoryRateLimiter",
    "InMemoryRateLimitMiddleware",
    # Security Headers
    "SecurityHeadersMiddleware",
    # CSRF Protection
    "CSRFMiddleware",
    # Redirect Validation
    "RedirectValidator",
    "get_redirect_validator",
    "validate_redirect_url",
    "get_validated_redirect",
    # Audit Logging
    "SecurityAuditService",
    "SecurityEvent",
    "EventCategory",
    "EventType",
    "Severity",
    "Status",
    "get_security_audit_service",
]
