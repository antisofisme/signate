"""
Security Infrastructure

Provides security features like rate limiting.
Uses middleware pattern to wrap Phase 1 WITHOUT modifying it.

Source: Phase 2 Design & Execution Plan - Section 4.3
"""

from .rate_limiter import RateLimiter, RateLimitMiddleware

__all__ = [
    "RateLimiter",
    "RateLimitMiddleware",
]
