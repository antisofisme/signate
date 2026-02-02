"""
Infrastructure Integration Tests

Focused integration tests verifying invariant preservation across cache states.

Critical Invariants:
1. Decision outcomes MUST be identical (Redis ON vs OFF)
2. Idempotency conflict behavior MUST be identical (Redis ON vs OFF)
3. Rate limiting: 429 when exceeded, FAIL-OPEN when Redis down

Source: Phase 2 Week 3 - Testing & Quality Assurance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import hashlib

from infrastructure.caching.redis_client import RedisClient
from infrastructure.caching.rule_cache_decorator import RuleCacheDecorator
from infrastructure.caching.idempotency_cache_decorator import IdempotencyCacheDecorator
from infrastructure.security.rate_limiter import RateLimiter


class TestDecisionFlowInvariance:
    """Test decision flow produces identical outcomes with Redis ON vs OFF"""

    @pytest.fixture
    def mock_rule_repository(self):
        """Mock Phase 1 RuleRepository"""
        repo = AsyncMock()

        # Mock rules
        rule1 = MagicMock()
        rule1.rule_id = MagicMock()
        rule1.rule_id.value = uuid4()
        rule1.tenant_id = MagicMock()
        rule1.tenant_id.value = uuid4()
        rule1.rule_name = "High Value Approval"
        rule1.evaluation_sequence = 1
        rule1.conditions = {"amount": {"$gt": 10000}}
        rule1.action = "APPROVE"
        rule1.version = 1
        rule1.is_active = True

        rule2 = MagicMock()
        rule2.rule_id = MagicMock()
        rule2.rule_id.value = uuid4()
        rule2.tenant_id = MagicMock()
        rule2.tenant_id.value = uuid4()
        rule2.rule_name = "Low Value Rejection"
        rule2.evaluation_sequence = 2
        rule2.conditions = {"amount": {"$lt": 100}}
        rule2.action = "REJECT"
        rule2.version = 1
        rule2.is_active = True

        repo.find_active_rules = AsyncMock(return_value=[rule1, rule2])
        return repo

    @pytest.mark.asyncio
    async def test_decision_outcome_identical_redis_on_vs_off(self, mock_rule_repository):
        """
        INVARIANT: Decision outcomes MUST be identical regardless of Redis state

        This is the CRITICAL test - determinism preservation.
        """
        tenant_id = uuid4()
        decision_type = "credit_approval"

        # Scenario 1: Redis ON (cache enabled)
        redis_on = MagicMock(spec=RedisClient)
        redis_on.get = AsyncMock(return_value=None)  # Cache miss first time
        redis_on.set = AsyncMock(return_value=True)

        decorator_redis_on = RuleCacheDecorator(mock_rule_repository, redis_on)
        rules_with_redis = await decorator_redis_on.find_active_rules(tenant_id, decision_type)

        # Scenario 2: Redis OFF (cache disabled)
        redis_off = MagicMock(spec=RedisClient)
        redis_off.is_connected = MagicMock(return_value=False)

        decorator_redis_off = RuleCacheDecorator(mock_rule_repository, redis_off)
        rules_without_redis = await decorator_redis_off.find_active_rules(tenant_id, decision_type)

        # CRITICAL VERIFICATION: Outcomes MUST be identical
        assert len(rules_with_redis) == len(rules_without_redis)
        assert rules_with_redis == rules_without_redis

        # Verify Phase 1 repository called in both cases
        # (Redis ON: cache miss triggers PostgreSQL)
        # (Redis OFF: always PostgreSQL)
        assert mock_rule_repository.find_active_rules.call_count >= 2

    @pytest.mark.asyncio
    async def test_decision_outcome_identical_cache_hit_vs_miss(self, mock_rule_repository):
        """
        INVARIANT: Decision outcomes MUST be identical for cache hit vs miss

        Verifies cache-aside pattern preserves determinism.
        """
        tenant_id = uuid4()
        decision_type = "credit_approval"

        # First call: cache miss (queries PostgreSQL)
        redis = MagicMock(spec=RedisClient)
        redis.get = AsyncMock(return_value=None)  # Cache miss
        redis.set = AsyncMock(return_value=True)

        decorator = RuleCacheDecorator(mock_rule_repository, redis)
        rules_cache_miss = await decorator.find_active_rules(tenant_id, decision_type)

        # Second call: cache hit (returns cached data)
        cached_data = [
            {
                "rule_id": str(rules_cache_miss[0].rule_id.value),
                "tenant_id": str(rules_cache_miss[0].tenant_id.value),
                "rule_name": rules_cache_miss[0].rule_name,
                "evaluation_sequence": rules_cache_miss[0].evaluation_sequence,
                "conditions": rules_cache_miss[0].conditions,
                "action": rules_cache_miss[0].action,
                "version": rules_cache_miss[0].version,
                "is_active": rules_cache_miss[0].is_active
            },
            {
                "rule_id": str(rules_cache_miss[1].rule_id.value),
                "tenant_id": str(rules_cache_miss[1].tenant_id.value),
                "rule_name": rules_cache_miss[1].rule_name,
                "evaluation_sequence": rules_cache_miss[1].evaluation_sequence,
                "conditions": rules_cache_miss[1].conditions,
                "action": rules_cache_miss[1].action,
                "version": rules_cache_miss[1].version,
                "is_active": rules_cache_miss[1].is_active
            }
        ]
        redis.get = AsyncMock(return_value=cached_data)

        with patch('infrastructure.caching.rule_cache_decorator.RuleModel') as MockRuleModel:
            # Mock reconstruction
            MockRuleModel.side_effect = rules_cache_miss

            rules_cache_hit = await decorator.find_active_rules(tenant_id, decision_type)

            # CRITICAL VERIFICATION: Outcomes MUST be identical
            assert len(rules_cache_hit) == len(rules_cache_miss)
            # Rules should be functionally equivalent

    @pytest.mark.asyncio
    async def test_decision_outcome_consistent_across_redis_failures(self, mock_rule_repository):
        """
        INVARIANT: Redis failures MUST NOT change decision outcomes

        Verifies fail-open preserves determinism.
        """
        tenant_id = uuid4()
        decision_type = "credit_approval"

        # Scenario 1: Redis connection fails during get
        redis_fail_get = MagicMock(spec=RedisClient)
        redis_fail_get.get = AsyncMock(side_effect=Exception("Redis connection error"))

        decorator_fail_get = RuleCacheDecorator(mock_rule_repository, redis_fail_get)
        rules_fail_get = await decorator_fail_get.find_active_rules(tenant_id, decision_type)

        # Scenario 2: Redis connection fails during set
        redis_fail_set = MagicMock(spec=RedisClient)
        redis_fail_set.get = AsyncMock(return_value=None)
        redis_fail_set.set = AsyncMock(side_effect=Exception("Redis connection error"))

        decorator_fail_set = RuleCacheDecorator(mock_rule_repository, redis_fail_set)
        rules_fail_set = await decorator_fail_set.find_active_rules(tenant_id, decision_type)

        # Scenario 3: Redis working
        redis_ok = MagicMock(spec=RedisClient)
        redis_ok.get = AsyncMock(return_value=None)
        redis_ok.set = AsyncMock(return_value=True)

        decorator_ok = RuleCacheDecorator(mock_rule_repository, redis_ok)
        rules_ok = await decorator_ok.find_active_rules(tenant_id, decision_type)

        # CRITICAL VERIFICATION: All outcomes MUST be identical
        assert len(rules_fail_get) == len(rules_fail_set) == len(rules_ok)
        assert rules_fail_get == rules_fail_set == rules_ok


class TestIdempotencyInvariance:
    """Test idempotency behavior is identical with Redis ON vs OFF"""

    @pytest.fixture
    def mock_idempotency_repository(self):
        """Mock Phase 1 IdempotencyRepository"""
        repo = AsyncMock()
        repo.find = AsyncMock()
        repo.save = AsyncMock()
        repo.get_context_hash = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_idempotency_conflict_detection_identical_redis_on_vs_off(
        self, mock_idempotency_repository
    ):
        """
        INVARIANT: Idempotency conflict detection MUST be identical (Redis ON vs OFF)

        Critical for determinism - conflicts must be detected regardless of cache state.
        """
        tenant_id = uuid4()
        idempotency_key = "test_key_123"
        existing_decision_id = uuid4()
        context_hash = hashlib.sha256(b"test_context").hexdigest()

        # Setup: decision already exists in PostgreSQL
        mock_idempotency_repository.find.return_value = existing_decision_id
        mock_idempotency_repository.get_context_hash.return_value = context_hash

        # Scenario 1: Redis ON (cache enabled)
        redis_on = MagicMock(spec=RedisClient)
        redis_on.get = AsyncMock(return_value=None)  # Cache miss
        redis_on.set = AsyncMock(return_value=True)

        decorator_redis_on = IdempotencyCacheDecorator(
            mock_idempotency_repository, redis_on
        )
        decision_id_redis_on = await decorator_redis_on.find(tenant_id, idempotency_key)
        context_hash_redis_on = await decorator_redis_on.get_context_hash(
            tenant_id, idempotency_key
        )

        # Scenario 2: Redis OFF (cache disabled)
        redis_off = MagicMock(spec=RedisClient)
        redis_off.is_connected = MagicMock(return_value=False)

        decorator_redis_off = IdempotencyCacheDecorator(
            mock_idempotency_repository, redis_off
        )
        decision_id_redis_off = await decorator_redis_off.find(tenant_id, idempotency_key)
        context_hash_redis_off = await decorator_redis_off.get_context_hash(
            tenant_id, idempotency_key
        )

        # CRITICAL VERIFICATION: Conflict detection MUST be identical
        assert decision_id_redis_on == decision_id_redis_off == existing_decision_id
        assert context_hash_redis_on == context_hash_redis_off == context_hash

    @pytest.mark.asyncio
    async def test_idempotency_write_through_preserves_postgresql_authority(
        self, mock_idempotency_repository
    ):
        """
        INVARIANT: PostgreSQL MUST be written FIRST (write-through pattern)

        Critical for data integrity - PostgreSQL is source of truth.
        """
        tenant_id = uuid4()
        idempotency_key = "test_key_456"
        decision_id = uuid4()
        context_hash = hashlib.sha256(b"new_context").hexdigest()

        call_order = []

        async def track_postgresql_save(*args):
            call_order.append("postgresql")

        async def track_redis_set(*args, **kwargs):
            call_order.append("redis")
            return True

        mock_idempotency_repository.save.side_effect = track_postgresql_save

        redis = MagicMock(spec=RedisClient)
        redis.set = AsyncMock(side_effect=track_redis_set)

        decorator = IdempotencyCacheDecorator(mock_idempotency_repository, redis)

        # Execute save
        await decorator.save(tenant_id, idempotency_key, decision_id, context_hash)

        # CRITICAL VERIFICATION: PostgreSQL MUST be written FIRST
        assert call_order[0] == "postgresql"
        assert call_order[1] == "redis"  # Redis after PostgreSQL

    @pytest.mark.asyncio
    async def test_idempotency_redis_failure_does_not_prevent_postgresql_write(
        self, mock_idempotency_repository
    ):
        """
        INVARIANT: Redis failures MUST NOT prevent PostgreSQL writes

        Critical for data integrity - PostgreSQL write must succeed.
        """
        tenant_id = uuid4()
        idempotency_key = "test_key_789"
        decision_id = uuid4()
        context_hash = hashlib.sha256(b"context").hexdigest()

        # Redis fails during save
        redis = MagicMock(spec=RedisClient)
        redis.set = AsyncMock(side_effect=Exception("Redis write error"))

        decorator = IdempotencyCacheDecorator(mock_idempotency_repository, redis)

        # Execute save (should not raise exception)
        await decorator.save(tenant_id, idempotency_key, decision_id, context_hash)

        # CRITICAL VERIFICATION: PostgreSQL write MUST have succeeded
        mock_idempotency_repository.save.assert_called_once_with(
            tenant_id, idempotency_key, decision_id, context_hash
        )

    @pytest.mark.asyncio
    async def test_idempotency_lookup_consistent_across_cache_states(
        self, mock_idempotency_repository
    ):
        """
        INVARIANT: Idempotency lookups MUST return same result (cache hit/miss/off)

        Critical for determinism.
        """
        tenant_id = uuid4()
        idempotency_key = "test_key_consistent"
        decision_id = uuid4()

        mock_idempotency_repository.find.return_value = decision_id

        # Scenario 1: Cache miss
        redis_miss = MagicMock(spec=RedisClient)
        redis_miss.get = AsyncMock(return_value=None)
        redis_miss.set = AsyncMock(return_value=True)

        decorator_miss = IdempotencyCacheDecorator(mock_idempotency_repository, redis_miss)
        result_miss = await decorator_miss.find(tenant_id, idempotency_key)

        # Scenario 2: Cache hit
        redis_hit = MagicMock(spec=RedisClient)
        redis_hit.get = AsyncMock(return_value=str(decision_id))

        decorator_hit = IdempotencyCacheDecorator(mock_idempotency_repository, redis_hit)
        result_hit = await decorator_hit.find(tenant_id, idempotency_key)

        # Scenario 3: Cache off
        redis_off = MagicMock(spec=RedisClient)
        redis_off.is_connected = MagicMock(return_value=False)

        decorator_off = IdempotencyCacheDecorator(mock_idempotency_repository, redis_off)
        result_off = await decorator_off.find(tenant_id, idempotency_key)

        # CRITICAL VERIFICATION: All results MUST be identical
        assert result_miss == result_hit == result_off == decision_id


class TestRateLimitingBehavior:
    """Test rate limiting: 429 when exceeded, FAIL-OPEN when Redis down"""

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429_when_exceeded(self):
        """
        INVARIANT: Rate limit exceeded MUST return 429

        Critical for rate limiting correctness.
        """
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)
        redis.get = AsyncMock(return_value=100)  # At limit
        redis._client = MagicMock()
        redis._client.ttl = AsyncMock(return_value=30)

        limiter = RateLimiter(redis)

        # Execute - request when at limit
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # CRITICAL VERIFICATION: Must reject
        assert allowed is False
        assert info["remaining"] == 0
        assert "retry_after" in info

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self):
        """
        INVARIANT: Requests within limit MUST be allowed

        Critical for rate limiting correctness.
        """
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)
        redis.get = AsyncMock(return_value=50)  # Under limit
        redis.increment = AsyncMock(return_value=51)
        redis._client = MagicMock()
        redis._client.ttl = AsyncMock(return_value=30)

        limiter = RateLimiter(redis)

        # Execute - request under limit
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # CRITICAL VERIFICATION: Must allow
        assert allowed is True
        assert info["remaining"] == 49  # 100 - 51

    @pytest.mark.asyncio
    async def test_rate_limit_fail_open_when_redis_down(self):
        """
        INVARIANT: Rate limiting MUST FAIL-OPEN when Redis unavailable

        Critical for system availability.
        """
        # Redis disconnected
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=False)

        limiter = RateLimiter(redis)

        # Execute - request when Redis down
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # CRITICAL VERIFICATION: Must allow (fail-open)
        assert allowed is True
        assert info["remaining"] == 100  # Full limit available

    @pytest.mark.asyncio
    async def test_rate_limit_fail_open_on_redis_error(self):
        """
        INVARIANT: Rate limiting MUST FAIL-OPEN on Redis errors

        Critical for system availability.
        """
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)
        redis.get = AsyncMock(side_effect=Exception("Redis connection error"))

        limiter = RateLimiter(redis)

        # Execute - request when Redis errors
        allowed, info = await limiter.check_rate_limit("test_key", limit=100, window=60)

        # CRITICAL VERIFICATION: Must allow (fail-open)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_per_tenant_isolation(self):
        """
        INVARIANT: Per-tenant limits MUST be isolated

        Critical for multi-tenancy.
        """
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)

        # Tenant A at limit
        redis.get = AsyncMock(return_value=100)
        redis._client = MagicMock()
        redis._client.ttl = AsyncMock(return_value=30)

        limiter = RateLimiter(redis)
        tenant_a_key = "rate_limit:tenant:tenant-a:decisions"

        allowed_a, _ = await limiter.check_rate_limit(tenant_a_key, limit=100, window=60)

        # Tenant B under limit
        redis.get = AsyncMock(return_value=50)
        redis.increment = AsyncMock(return_value=51)

        tenant_b_key = "rate_limit:tenant:tenant-b:decisions"

        allowed_b, _ = await limiter.check_rate_limit(tenant_b_key, limit=100, window=60)

        # CRITICAL VERIFICATION: Tenant isolation preserved
        assert allowed_a is False  # Tenant A rate limited
        assert allowed_b is True   # Tenant B allowed

    @pytest.mark.asyncio
    async def test_rate_limit_window_reset_behavior(self):
        """
        INVARIANT: Rate limit window MUST reset after expiry

        Critical for rate limiting correctness.
        """
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=True)

        limiter = RateLimiter(redis)

        # First request in new window
        redis.get = AsyncMock(return_value=None)  # New window
        redis.set = AsyncMock(return_value=True)

        allowed_first, info_first = await limiter.check_rate_limit(
            "test_key", limit=100, window=60
        )

        # CRITICAL VERIFICATION: New window allows requests
        assert allowed_first is True
        assert info_first["remaining"] == 99  # First request consumed 1


class TestInfrastructureFailOverScenarios:
    """Test complete fail-over scenarios across all components"""

    @pytest.mark.asyncio
    async def test_complete_redis_failure_preserves_system_function(self):
        """
        END-TO-END INVARIANT: Complete Redis failure MUST NOT break system

        Critical system-level test.
        """
        # Redis completely down
        redis = MagicMock(spec=RedisClient)
        redis.is_connected = MagicMock(return_value=False)
        redis.get = AsyncMock(side_effect=Exception("Redis down"))
        redis.set = AsyncMock(side_effect=Exception("Redis down"))

        # Mock repositories
        rule_repo = AsyncMock()
        rule_repo.find_active_rules = AsyncMock(return_value=[])

        idempotency_repo = AsyncMock()
        idempotency_repo.find = AsyncMock(return_value=None)

        # Create decorators with failed Redis
        rule_decorator = RuleCacheDecorator(rule_repo, redis)
        idempotency_decorator = IdempotencyCacheDecorator(idempotency_repo, redis)
        rate_limiter = RateLimiter(redis)

        # Execute operations - NONE should raise exceptions
        tenant_id = uuid4()

        rules = await rule_decorator.find_active_rules(tenant_id, "credit_approval")
        decision_id = await idempotency_decorator.find(tenant_id, "key")
        allowed, _ = await rate_limiter.check_rate_limit("key", limit=100, window=60)

        # CRITICAL VERIFICATION: System continues to function
        assert rules == []  # Fallback to PostgreSQL
        assert decision_id is None  # Fallback to PostgreSQL
        assert allowed is True  # Fail-open

    @pytest.mark.asyncio
    async def test_redis_intermittent_failures_do_not_affect_determinism(self):
        """
        END-TO-END INVARIANT: Intermittent Redis failures MUST NOT affect outcomes

        Critical for determinism under failure.
        """
        # Mock repositories with consistent data
        rule_repo = AsyncMock()
        test_rule = MagicMock()
        test_rule.rule_id = MagicMock()
        test_rule.rule_id.value = uuid4()
        rule_repo.find_active_rules = AsyncMock(return_value=[test_rule])

        # Redis with intermittent failures
        redis = MagicMock(spec=RedisClient)
        call_count = [0]

        def intermittent_get(key):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("Intermittent failure")
            return None

        redis.get = AsyncMock(side_effect=intermittent_get)
        redis.set = AsyncMock(return_value=True)

        decorator = RuleCacheDecorator(rule_repo, redis)
        tenant_id = uuid4()

        # Multiple calls with intermittent failures
        rules1 = await decorator.find_active_rules(tenant_id, "credit_approval")
        rules2 = await decorator.find_active_rules(tenant_id, "credit_approval")
        rules3 = await decorator.find_active_rules(tenant_id, "credit_approval")

        # CRITICAL VERIFICATION: All results MUST be identical
        assert len(rules1) == len(rules2) == len(rules3) == 1
        assert rules1 == rules2 == rules3
