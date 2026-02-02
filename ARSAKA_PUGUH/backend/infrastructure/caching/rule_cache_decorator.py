"""
Rule Cache Decorator

Wraps Phase 1 RuleRepository to add Redis caching WITHOUT modifying it.

CRITICAL CONSTRAINTS:
- Cache RULE DEFINITIONS only (not evaluation results)
- PostgreSQL remains source of truth
- Redis failures fallback to PostgreSQL
- Determinism MUST be preserved

Source: Phase 2 Design & Execution Plan - Section 4.1
"""

from typing import List, Optional
from uuid import UUID

from infrastructure.logging import get_logger
from infrastructure.metrics import core_rule_evaluations
from .redis_client import RedisClient


logger = get_logger(__name__)


class RuleCacheDecorator:
    """
    Wraps RuleRepository to add Redis caching

    Cache Strategy: Cache-Aside Pattern
    1. Check Redis cache for rules
    2. If cache miss, query PostgreSQL
    3. Store result in Redis with TTL
    4. Return result

    Cache Key Format: "rules:tenant:{tenant_id}:active"

    TTL: 300 seconds (5 minutes)

    Example:
        # Phase 1 repository (UNCHANGED)
        rule_repo = RuleRepository(session)

        # Phase 2: Wrap with caching
        redis = get_redis_client()
        await redis.connect()
        cached_repo = RuleCacheDecorator(rule_repo, redis)

        # Use cached version (same interface as original)
        rules = await cached_repo.find_active_rules(tenant_id, decision_type)
    """

    def __init__(
        self,
        repository,  # IRuleRepository from Phase 1
        redis_client: RedisClient,
        ttl: int = 300  # 5 minutes default TTL
    ):
        """
        Initialize rule cache decorator

        Args:
            repository: Original Phase 1 RuleRepository instance
            redis_client: Redis client for caching
            ttl: Cache TTL in seconds (default: 300)
        """
        self._repository = repository
        self._redis = redis_client
        self._ttl = ttl

    async def find_active_rules(
        self,
        tenant_id: UUID,
        decision_type: str
    ) -> List:  # Returns List[Rule] from Phase 1 domain
        """
        Find active rules with Redis caching

        Args:
            tenant_id: Tenant UUID
            decision_type: Decision type for filtering

        Returns:
            List of Rule domain objects (from Phase 1)

        Cache Strategy:
        1. Check Redis for cached rules
        2. If cache hit: deserialize and return
        3. If cache miss: query PostgreSQL, cache result, return
        """
        cache_key = self._build_cache_key(tenant_id, decision_type)

        # Try cache first (cache-aside pattern)
        cached_rules = await self._get_from_cache(cache_key)

        if cached_rules is not None:
            logger.debug(
                "Rule cache HIT",
                extra={
                    "tenant_id": str(tenant_id),
                    "decision_type": decision_type,
                    "cache_key": cache_key,
                    "rules_count": len(cached_rules)
                }
            )
            return self._deserialize_rules(cached_rules)

        # Cache miss - query PostgreSQL (Phase 1 repository UNCHANGED)
        logger.debug(
            "Rule cache MISS - querying PostgreSQL",
            extra={
                "tenant_id": str(tenant_id),
                "decision_type": decision_type,
                "cache_key": cache_key
            }
        )

        rules = await self._repository.find_active_rules(tenant_id, decision_type)

        # Store in cache for next time
        await self._store_in_cache(cache_key, rules)

        return rules

    async def find_by_id(
        self,
        rule_id: UUID,
        tenant_id: UUID
    ):  # Returns Optional[Rule] from Phase 1 domain
        """
        Find rule by ID

        Note: NOT cached (individual rule lookups are rare)
        Delegates directly to Phase 1 repository.

        Args:
            rule_id: Rule UUID
            tenant_id: Tenant UUID

        Returns:
            Rule domain object or None
        """
        # No caching for individual rule lookups (rare operation)
        return await self._repository.find_by_id(rule_id, tenant_id)

    def _build_cache_key(self, tenant_id: UUID, decision_type: str) -> str:
        """
        Build Redis cache key

        Format: "rules:tenant:{tenant_id}:type:{decision_type}:active"

        Args:
            tenant_id: Tenant UUID
            decision_type: Decision type

        Returns:
            Cache key string
        """
        return f"rules:tenant:{tenant_id}:type:{decision_type}:active"

    async def _get_from_cache(self, cache_key: str) -> Optional[List[dict]]:
        """
        Get rules from Redis cache

        Args:
            cache_key: Cache key

        Returns:
            List of rule dictionaries or None if not found/error
        """
        try:
            cached_data = await self._redis.get(cache_key)

            if cached_data is None:
                return None

            # Cached data is list of rule dictionaries
            if not isinstance(cached_data, list):
                logger.warning(
                    "Invalid cached data format",
                    extra={"cache_key": cache_key, "type": type(cached_data).__name__}
                )
                return None

            return cached_data

        except Exception as e:
            logger.warning(
                "Cache read error - falling back to PostgreSQL",
                extra={"cache_key": cache_key, "error": str(e)}
            )
            return None

    async def _store_in_cache(self, cache_key: str, rules: List) -> bool:
        """
        Store rules in Redis cache

        Args:
            cache_key: Cache key
            rules: List of Rule domain objects from Phase 1

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Serialize rules to dictionaries
            serialized_rules = [self._serialize_rule(rule) for rule in rules]

            # Store in Redis with TTL
            success = await self._redis.set(
                cache_key,
                serialized_rules,
                ttl=self._ttl
            )

            if success:
                logger.debug(
                    "Rules cached successfully",
                    extra={
                        "cache_key": cache_key,
                        "rules_count": len(rules),
                        "ttl": self._ttl
                    }
                )

            return success

        except Exception as e:
            logger.warning(
                "Cache write error - continuing without cache",
                extra={"cache_key": cache_key, "error": str(e)}
            )
            return False

    def _serialize_rule(self, rule) -> dict:
        """
        Serialize Rule domain object to dictionary

        Args:
            rule: Rule domain object from Phase 1

        Returns:
            Dictionary representation

        Note: Serializes ONLY the fields needed for evaluation.
        Does NOT cache evaluation results (preserves determinism).
        """
        return {
            "rule_id": str(rule.rule_id.value),
            "tenant_id": str(rule.tenant_id.value),
            "rule_name": rule.rule_name,
            "evaluation_sequence": rule.evaluation_sequence,
            "conditions": rule.conditions,
            "action": rule.action,
            "version": rule.version,
            "is_active": rule.is_active,
        }

    def _deserialize_rules(self, serialized_rules: List[dict]) -> List:
        """
        Deserialize cached rules back to domain objects

        Args:
            serialized_rules: List of rule dictionaries

        Returns:
            List of Rule domain objects

        Note: Reconstructs Phase 1 Rule objects from cache.
        """
        from uuid import UUID as PyUUID
        from core.domain.value_objects import RuleId, TenantId

        # Import Phase 1 domain Rule class
        # This is safe because we're just reconstructing from cached data
        from core.repositories.models import RuleModel

        rules = []
        for data in serialized_rules:
            try:
                # Reconstruct Rule domain object
                # Note: This uses Phase 1's repository mapping logic
                rule = RuleModel(
                    rule_id=PyUUID(data["rule_id"]),
                    tenant_id=PyUUID(data["tenant_id"]),
                    rule_name=data["rule_name"],
                    evaluation_sequence=data["evaluation_sequence"],
                    conditions=data["conditions"],
                    action=data["action"],
                    version=data["version"],
                    is_active=data["is_active"],
                )
                rules.append(rule)

            except Exception as e:
                logger.warning(
                    "Failed to deserialize cached rule",
                    extra={"rule_id": data.get("rule_id"), "error": str(e)}
                )
                continue

        return rules

    async def invalidate_cache(self, tenant_id: UUID, decision_type: str) -> bool:
        """
        Invalidate cache for specific tenant and decision type

        Args:
            tenant_id: Tenant UUID
            decision_type: Decision type

        Returns:
            True if invalidated, False otherwise

        Use Case: Call this when rules are updated (future Phase 3 CMS)
        """
        cache_key = self._build_cache_key(tenant_id, decision_type)

        deleted = await self._redis.delete(cache_key)

        if deleted:
            logger.info(
                "Rule cache invalidated",
                extra={
                    "tenant_id": str(tenant_id),
                    "decision_type": decision_type,
                    "cache_key": cache_key
                }
            )

        return deleted
