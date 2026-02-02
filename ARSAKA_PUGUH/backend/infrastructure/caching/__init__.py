"""
Caching Infrastructure (Redis)

Provides Redis-based caching with graceful fallback to PostgreSQL.
Uses cache-aside pattern to wrap Phase 1 WITHOUT modifying it.

CRITICAL: Redis is OPTIONAL. All failures fallback to PostgreSQL.

Source: Phase 2 Design & Execution Plan - Week 2
"""

from .redis_client import RedisClient, get_redis_client
from .cache_decorator import CacheDecorator
from .rule_cache_decorator import RuleCacheDecorator
from .idempotency_cache_decorator import IdempotencyCacheDecorator

__all__ = [
    "RedisClient",
    "get_redis_client",
    "CacheDecorator",
    "RuleCacheDecorator",
    "IdempotencyCacheDecorator",
]
