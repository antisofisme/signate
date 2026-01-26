"""
Idempotency Cache Acceleration Decorator

Wraps Phase 1 IdempotencyRepository to add Redis acceleration WITHOUT modifying it.

CRITICAL CONSTRAINTS:
- PostgreSQL remains source of truth
- Redis is acceleration layer only (optional)
- Redis failures fallback to PostgreSQL
- Cache-aside pattern: check Redis first, fallback to PostgreSQL
- All writes go to PostgreSQL (Redis is read-through cache)

Source: Phase 2 Design & Execution Plan - Section 4.1
"""

from typing import Optional
from uuid import UUID

from infrastructure.logging import get_logger
from infrastructure.metrics import core_idempotency_hits, core_idempotency_conflicts
from .redis_client import RedisClient


logger = get_logger(__name__)


class IdempotencyCacheDecorator:
    """
    Wraps IdempotencyRepository to add Redis acceleration

    Cache Strategy: Read-Through Cache
    1. Check Redis for idempotency key
    2. If cache miss, query PostgreSQL
    3. Store result in Redis (TTL: 24 hours to match PostgreSQL)
    4. Return result

    Cache Key Format: "idempotency:tenant:{tenant_id}:key:{idempotency_key}"

    TTL: 86400 seconds (24 hours, matches Phase 1 PostgreSQL TTL)

    CRITICAL: All writes go to PostgreSQL first, then Redis.
    PostgreSQL is the authoritative source.

    Example:
        # Phase 1 repository (UNCHANGED)
        idempotency_repo = IdempotencyRepository(session)

        # Phase 2: Wrap with Redis acceleration
        redis = get_redis_client()
        await redis.connect()
        cached_repo = IdempotencyCacheDecorator(idempotency_repo, redis)

        # Use cached version (same interface as original)
        decision_id = await cached_repo.find(tenant_id, idempotency_key)
    """

    def __init__(
        self,
        repository,  # IIdempotencyRepository from Phase 1
        redis_client: RedisClient,
        ttl: int = 86400  # 24 hours (matches Phase 1 PostgreSQL)
    ):
        """
        Initialize idempotency cache decorator

        Args:
            repository: Original Phase 1 IdempotencyRepository instance
            redis_client: Redis client for caching
            ttl: Cache TTL in seconds (default: 86400 = 24 hours)
        """
        self._repository = repository
        self._redis = redis_client
        self._ttl = ttl

    async def find(
        self,
        tenant_id: UUID,
        idempotency_key: str
    ) -> Optional[UUID]:
        """
        Find decision ID by idempotency key with Redis acceleration

        Args:
            tenant_id: Tenant UUID
            idempotency_key: Idempotency key

        Returns:
            Decision ID (UUID) or None if not found

        Cache Strategy:
        1. Check Redis (fast path)
        2. If cache miss: query PostgreSQL (authoritative)
        3. Store result in Redis for next time
        """
        cache_key = self._build_cache_key(tenant_id, idempotency_key)

        # Try Redis first (fast path)
        cached_decision_id = await self._get_from_cache(cache_key)

        if cached_decision_id is not None:
            # Cache hit
            if core_idempotency_hits:
                core_idempotency_hits.labels(tenant_id=str(tenant_id)).inc()

            logger.debug(
                "Idempotency cache HIT (Redis)",
                extra={
                    "tenant_id": str(tenant_id),
                    "idempotency_key": idempotency_key,
                    "decision_id": str(cached_decision_id),
                    "cache_key": cache_key
                }
            )
            return cached_decision_id

        # Cache miss - query PostgreSQL (authoritative)
        logger.debug(
            "Idempotency cache MISS - querying PostgreSQL",
            extra={
                "tenant_id": str(tenant_id),
                "idempotency_key": idempotency_key,
                "cache_key": cache_key
            }
        )

        decision_id = await self._repository.find(tenant_id, idempotency_key)

        # If found in PostgreSQL, store in Redis for next time
        if decision_id is not None:
            await self._store_in_cache(cache_key, decision_id)

        return decision_id

    async def save(
        self,
        tenant_id: UUID,
        idempotency_key: str,
        decision_id: UUID,
        context_hash: str
    ):
        """
        Save idempotency entry

        CRITICAL: Writes go to PostgreSQL FIRST (authoritative),
        then optionally to Redis (acceleration).

        Args:
            tenant_id: Tenant UUID
            idempotency_key: Idempotency key
            decision_id: Decision ID
            context_hash: SHA-256 hash of context

        Returns:
            None
        """
        # Write to PostgreSQL FIRST (authoritative)
        await self._repository.save(tenant_id, idempotency_key, decision_id, context_hash)

        # Then write to Redis (acceleration, best-effort)
        cache_key = self._build_cache_key(tenant_id, idempotency_key)
        await self._store_in_cache(cache_key, decision_id)

        # Also cache context hash for conflict detection
        context_hash_key = self._build_context_hash_key(tenant_id, idempotency_key)
        await self._redis.set(context_hash_key, context_hash, ttl=self._ttl)

        logger.debug(
            "Idempotency entry saved to PostgreSQL + Redis",
            extra={
                "tenant_id": str(tenant_id),
                "idempotency_key": idempotency_key,
                "decision_id": str(decision_id)
            }
        )

    async def get_context_hash(
        self,
        tenant_id: UUID,
        idempotency_key: str
    ) -> Optional[str]:
        """
        Get context hash for conflict detection

        Args:
            tenant_id: Tenant UUID
            idempotency_key: Idempotency key

        Returns:
            Context hash (SHA-256) or None if not found

        Cache Strategy:
        1. Check Redis first
        2. If cache miss: query PostgreSQL
        3. Store result in Redis
        """
        context_hash_key = self._build_context_hash_key(tenant_id, idempotency_key)

        # Try Redis first
        cached_hash = await self._redis.get(context_hash_key)

        if cached_hash is not None:
            logger.debug(
                "Context hash cache HIT (Redis)",
                extra={
                    "tenant_id": str(tenant_id),
                    "idempotency_key": idempotency_key
                }
            )
            return cached_hash

        # Cache miss - query PostgreSQL
        context_hash = await self._repository.get_context_hash(tenant_id, idempotency_key)

        # Store in Redis for next time
        if context_hash is not None:
            await self._redis.set(context_hash_key, context_hash, ttl=self._ttl)

        return context_hash

    def _build_cache_key(self, tenant_id: UUID, idempotency_key: str) -> str:
        """
        Build Redis cache key for decision ID

        Format: "idempotency:tenant:{tenant_id}:key:{idempotency_key}"

        Args:
            tenant_id: Tenant UUID
            idempotency_key: Idempotency key

        Returns:
            Cache key string
        """
        return f"idempotency:tenant:{tenant_id}:key:{idempotency_key}"

    def _build_context_hash_key(self, tenant_id: UUID, idempotency_key: str) -> str:
        """
        Build Redis cache key for context hash

        Format: "idempotency:tenant:{tenant_id}:key:{idempotency_key}:hash"

        Args:
            tenant_id: Tenant UUID
            idempotency_key: Idempotency key

        Returns:
            Cache key string
        """
        return f"idempotency:tenant:{tenant_id}:key:{idempotency_key}:hash"

    async def _get_from_cache(self, cache_key: str) -> Optional[UUID]:
        """
        Get decision ID from Redis cache

        Args:
            cache_key: Cache key

        Returns:
            Decision ID (UUID) or None if not found/error
        """
        try:
            cached_value = await self._redis.get(cache_key)

            if cached_value is None:
                return None

            # Deserialize UUID
            if isinstance(cached_value, str):
                return UUID(cached_value)

            return None

        except Exception as e:
            logger.warning(
                "Idempotency cache read error - falling back to PostgreSQL",
                extra={"cache_key": cache_key, "error": str(e)}
            )
            return None

    async def _store_in_cache(self, cache_key: str, decision_id: UUID) -> bool:
        """
        Store decision ID in Redis cache

        Args:
            cache_key: Cache key
            decision_id: Decision ID (UUID)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Serialize UUID to string
            success = await self._redis.set(
                cache_key,
                str(decision_id),
                ttl=self._ttl
            )

            if success:
                logger.debug(
                    "Idempotency entry cached successfully",
                    extra={
                        "cache_key": cache_key,
                        "decision_id": str(decision_id),
                        "ttl": self._ttl
                    }
                )

            return success

        except Exception as e:
            logger.warning(
                "Idempotency cache write error - continuing without cache",
                extra={"cache_key": cache_key, "error": str(e)}
            )
            return False
