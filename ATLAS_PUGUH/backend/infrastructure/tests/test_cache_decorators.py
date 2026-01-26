"""
Cache Decorator Unit Tests

Tests cache decorators (Rule, Idempotency) for hit/miss behavior and fallback.

Critical Test Cases:
1. RuleCacheDecorator: cache hit/miss, fallback to PostgreSQL
2. IdempotencyCacheDecorator: write-through pattern, cache acceleration
3. Graceful degradation when Redis unavailable

Source: Phase 2 Week 3 - Testing & Quality Assurance
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from infrastructure.caching.redis_client import RedisClient
from infrastructure.caching.rule_cache_decorator import RuleCacheDecorator
from infrastructure.caching.idempotency_cache_decorator import IdempotencyCacheDecorator


class TestRuleCacheDecorator:
    """Test RuleCacheDecorator behavior"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock(spec=RedisClient)
        redis.get = AsyncMock()
        redis.set = AsyncMock()
        redis.delete = AsyncMock()
        return redis

    @pytest.fixture
    def mock_repository(self):
        """Mock Phase 1 RuleRepository"""
        repo = AsyncMock()
        repo.find_active_rules = AsyncMock()
        repo.find_by_id = AsyncMock()
        return repo

    @pytest.fixture
    def sample_rules(self):
        """Sample rule data"""
        rule1 = MagicMock()
        rule1.rule_id = MagicMock()
        rule1.rule_id.value = uuid4()
        rule1.tenant_id = MagicMock()
        rule1.tenant_id.value = uuid4()
        rule1.rule_name = "Test Rule 1"
        rule1.evaluation_sequence = 1
        rule1.conditions = {"amount": {"$gt": 1000}}
        rule1.action = "APPROVE"
        rule1.version = 1
        rule1.is_active = True

        rule2 = MagicMock()
        rule2.rule_id = MagicMock()
        rule2.rule_id.value = uuid4()
        rule2.tenant_id = MagicMock()
        rule2.tenant_id.value = uuid4()
        rule2.rule_name = "Test Rule 2"
        rule2.evaluation_sequence = 2
        rule2.conditions = {"amount": {"$lt": 500}}
        rule2.action = "REJECT"
        rule2.version = 1
        rule2.is_active = True

        return [rule1, rule2]

    @pytest.mark.asyncio
    async def test_cache_miss_queries_postgresql(self, mock_redis, mock_repository, sample_rules):
        """Test cache miss triggers PostgreSQL query"""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        mock_repository.find_active_rules.return_value = sample_rules

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        result = await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify
        mock_redis.get.assert_called_once()  # Checked cache
        mock_repository.find_active_rules.assert_called_once_with(tenant_id, "credit_approval")  # Queried PostgreSQL
        mock_redis.set.assert_called_once()  # Stored in cache
        assert result == sample_rules

    @pytest.mark.asyncio
    async def test_cache_hit_skips_postgresql(self, mock_redis, mock_repository, sample_rules):
        """Test cache hit does NOT query PostgreSQL"""
        # Setup - simulate cache hit
        cached_data = [
            {
                "rule_id": str(sample_rules[0].rule_id.value),
                "tenant_id": str(sample_rules[0].tenant_id.value),
                "rule_name": "Test Rule 1",
                "evaluation_sequence": 1,
                "conditions": {"amount": {"$gt": 1000}},
                "action": "APPROVE",
                "version": 1,
                "is_active": True
            }
        ]
        mock_redis.get.return_value = cached_data

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        with patch('infrastructure.caching.rule_cache_decorator.RuleModel') as MockRuleModel:
            # Mock RuleModel construction
            mock_rule = MagicMock()
            MockRuleModel.return_value = mock_rule

            result = await decorator.find_active_rules(tenant_id, "credit_approval")

            # Verify
            mock_redis.get.assert_called_once()  # Checked cache
            mock_repository.find_active_rules.assert_not_called()  # Did NOT query PostgreSQL (cache hit)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_cache_read_error_falls_back_to_postgresql(self, mock_redis, mock_repository, sample_rules):
        """Test cache read error gracefully falls back to PostgreSQL"""
        # Setup - simulate cache error
        mock_redis.get.side_effect = Exception("Redis error")
        mock_repository.find_active_rules.return_value = sample_rules

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        result = await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify - should fallback to PostgreSQL
        mock_repository.find_active_rules.assert_called_once()
        assert result == sample_rules

    @pytest.mark.asyncio
    async def test_cache_write_error_does_not_affect_result(self, mock_redis, mock_repository, sample_rules):
        """Test cache write error does not prevent returning data"""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.set.side_effect = Exception("Redis write error")  # Cache write fails
        mock_repository.find_active_rules.return_value = sample_rules

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        result = await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify - data still returned despite cache write failure
        mock_repository.find_active_rules.assert_called_once()
        assert result == sample_rules

    @pytest.mark.asyncio
    async def test_find_by_id_not_cached(self, mock_redis, mock_repository):
        """Test find_by_id bypasses cache (rare operation)"""
        # Setup
        rule_id = uuid4()
        tenant_id = uuid4()
        mock_rule = MagicMock()
        mock_repository.find_by_id.return_value = mock_rule

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)

        # Execute
        result = await decorator.find_by_id(rule_id, tenant_id)

        # Verify - should NOT use cache
        mock_redis.get.assert_not_called()
        mock_repository.find_by_id.assert_called_once_with(rule_id, tenant_id)
        assert result == mock_rule

    @pytest.mark.asyncio
    async def test_cache_key_format(self, mock_redis, mock_repository, sample_rules):
        """Test cache key format is correct"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.find_active_rules.return_value = sample_rules

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()
        decision_type = "credit_approval"

        # Execute
        await decorator.find_active_rules(tenant_id, decision_type)

        # Verify cache key format
        expected_key = f"rules:tenant:{tenant_id}:type:{decision_type}:active"
        mock_redis.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_cache_ttl_passed_correctly(self, mock_redis, mock_repository, sample_rules):
        """Test cache TTL is passed to Redis"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.find_active_rules.return_value = sample_rules
        mock_redis.set.return_value = True

        custom_ttl = 600
        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=custom_ttl)
        tenant_id = uuid4()

        # Execute
        await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify TTL passed to Redis
        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs['ttl'] == custom_ttl

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_redis, mock_repository):
        """Test cache invalidation"""
        # Setup
        mock_redis.delete.return_value = True

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()
        decision_type = "credit_approval"

        # Execute
        result = await decorator.invalidate_cache(tenant_id, decision_type)

        # Verify
        expected_key = f"rules:tenant:{tenant_id}:type:{decision_type}:active"
        mock_redis.delete.assert_called_once_with(expected_key)
        assert result is True

    @pytest.mark.asyncio
    async def test_serialization_preserves_rule_fields(self, mock_redis, mock_repository, sample_rules):
        """Test rule serialization preserves all required fields"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.find_active_rules.return_value = sample_rules
        mock_redis.set.return_value = True

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify serialization
        call_args = mock_redis.set.call_args
        serialized_rules = call_args[0][1]

        # Check first rule serialization
        assert len(serialized_rules) == 2
        rule_data = serialized_rules[0]
        assert "rule_id" in rule_data
        assert "tenant_id" in rule_data
        assert "rule_name" in rule_data
        assert "evaluation_sequence" in rule_data
        assert "conditions" in rule_data
        assert "action" in rule_data
        assert "version" in rule_data
        assert "is_active" in rule_data

    @pytest.mark.asyncio
    async def test_deserialization_invalid_data_skipped(self, mock_redis, mock_repository):
        """Test deserialization skips invalid cached data"""
        # Setup - invalid cached data
        cached_data = [
            {"rule_id": "invalid-uuid"},  # Invalid UUID format
            {
                "rule_id": str(uuid4()),
                "tenant_id": str(uuid4()),
                "rule_name": "Valid Rule",
                "evaluation_sequence": 1,
                "conditions": {},
                "action": "APPROVE",
                "version": 1,
                "is_active": True
            }
        ]
        mock_redis.get.return_value = cached_data

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        with patch('infrastructure.caching.rule_cache_decorator.RuleModel') as MockRuleModel:
            # First construction fails, second succeeds
            MockRuleModel.side_effect = [Exception("Invalid data"), MagicMock()]

            result = await decorator.find_active_rules(tenant_id, "credit_approval")

            # Verify - should skip invalid and return valid rules only
            assert len(result) == 1


class TestIdempotencyCacheDecorator:
    """Test IdempotencyCacheDecorator behavior"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock(spec=RedisClient)
        redis.get = AsyncMock()
        redis.set = AsyncMock()
        return redis

    @pytest.fixture
    def mock_repository(self):
        """Mock Phase 1 IdempotencyRepository"""
        repo = AsyncMock()
        repo.find = AsyncMock()
        repo.save = AsyncMock()
        repo.get_context_hash = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_find_cache_miss_queries_postgresql(self, mock_redis, mock_repository):
        """Test cache miss triggers PostgreSQL query"""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        decision_id = uuid4()
        mock_repository.find.return_value = decision_id

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        result = await decorator.find(tenant_id, idempotency_key)

        # Verify
        mock_redis.get.assert_called_once()  # Checked cache
        mock_repository.find.assert_called_once_with(tenant_id, idempotency_key)  # Queried PostgreSQL
        mock_redis.set.assert_called_once()  # Stored in cache
        assert result == decision_id

    @pytest.mark.asyncio
    async def test_find_cache_hit_skips_postgresql(self, mock_redis, mock_repository):
        """Test cache hit does NOT query PostgreSQL"""
        # Setup - simulate cache hit
        decision_id = uuid4()
        mock_redis.get.return_value = str(decision_id)

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        result = await decorator.find(tenant_id, idempotency_key)

        # Verify
        mock_redis.get.assert_called_once()  # Checked cache
        mock_repository.find.assert_not_called()  # Did NOT query PostgreSQL
        assert result == decision_id

    @pytest.mark.asyncio
    async def test_find_returns_none_when_not_found(self, mock_redis, mock_repository):
        """Test find returns None when key not found"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.find.return_value = None

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "nonexistent_key"

        # Execute
        result = await decorator.find(tenant_id, idempotency_key)

        # Verify
        assert result is None
        mock_repository.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_writes_to_postgresql_first(self, mock_redis, mock_repository):
        """Test save writes to PostgreSQL FIRST (write-through pattern)"""
        # Setup
        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"
        decision_id = uuid4()
        context_hash = "sha256hash"

        call_order = []

        # Track call order
        async def track_repo_save(*args):
            call_order.append("postgresql")

        async def track_redis_set(*args, **kwargs):
            call_order.append("redis")
            return True

        mock_repository.save.side_effect = track_repo_save
        mock_redis.set.side_effect = track_redis_set

        # Execute
        await decorator.save(tenant_id, idempotency_key, decision_id, context_hash)

        # Verify - PostgreSQL written BEFORE Redis
        assert call_order == ["postgresql", "redis", "redis"]  # PostgreSQL, then Redis (decision_id), then Redis (context_hash)
        mock_repository.save.assert_called_once_with(tenant_id, idempotency_key, decision_id, context_hash)

    @pytest.mark.asyncio
    async def test_save_redis_failure_does_not_affect_postgresql(self, mock_redis, mock_repository):
        """Test Redis write failure during save does not prevent PostgreSQL write"""
        # Setup
        mock_redis.set.side_effect = Exception("Redis write error")

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"
        decision_id = uuid4()
        context_hash = "sha256hash"

        # Execute
        await decorator.save(tenant_id, idempotency_key, decision_id, context_hash)

        # Verify - PostgreSQL write still happened
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_key_format_idempotency(self, mock_redis, mock_repository):
        """Test idempotency cache key format"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.find.return_value = None

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        await decorator.find(tenant_id, idempotency_key)

        # Verify cache key format
        expected_key = f"idempotency:tenant:{tenant_id}:key:{idempotency_key}"
        mock_redis.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_cache_ttl_24_hours(self, mock_redis, mock_repository):
        """Test idempotency cache TTL is 24 hours (matches PostgreSQL)"""
        # Setup
        mock_redis.get.return_value = None
        decision_id = uuid4()
        mock_repository.find.return_value = decision_id
        mock_redis.set.return_value = True

        # Default TTL should be 86400 (24 hours)
        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        await decorator.find(tenant_id, idempotency_key)

        # Verify TTL
        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs['ttl'] == 86400

    @pytest.mark.asyncio
    async def test_get_context_hash_cache_hit(self, mock_redis, mock_repository):
        """Test get_context_hash with cache hit"""
        # Setup
        context_hash = "sha256hashvalue"
        mock_redis.get.return_value = context_hash

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        result = await decorator.get_context_hash(tenant_id, idempotency_key)

        # Verify
        assert result == context_hash
        mock_repository.get_context_hash.assert_not_called()  # Cache hit

    @pytest.mark.asyncio
    async def test_get_context_hash_cache_miss(self, mock_redis, mock_repository):
        """Test get_context_hash with cache miss"""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        context_hash = "sha256hashvalue"
        mock_repository.get_context_hash.return_value = context_hash

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        result = await decorator.get_context_hash(tenant_id, idempotency_key)

        # Verify
        assert result == context_hash
        mock_repository.get_context_hash.assert_called_once()  # PostgreSQL queried
        mock_redis.set.assert_called_once()  # Cached result

    @pytest.mark.asyncio
    async def test_context_hash_key_format(self, mock_redis, mock_repository):
        """Test context hash cache key format"""
        # Setup
        mock_redis.get.return_value = None
        mock_repository.get_context_hash.return_value = "hash"

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        await decorator.get_context_hash(tenant_id, idempotency_key)

        # Verify key format includes ":hash" suffix
        expected_key = f"idempotency:tenant:{tenant_id}:key:{idempotency_key}:hash"
        call_args_list = [call[0][0] for call in mock_redis.get.call_args_list]
        assert expected_key in call_args_list

    @pytest.mark.asyncio
    async def test_find_cache_read_error_falls_back(self, mock_redis, mock_repository):
        """Test find with cache read error falls back to PostgreSQL"""
        # Setup
        mock_redis.get.side_effect = Exception("Redis error")
        decision_id = uuid4()
        mock_repository.find.return_value = decision_id

        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()
        idempotency_key = "test_key_123"

        # Execute
        result = await decorator.find(tenant_id, idempotency_key)

        # Verify - PostgreSQL fallback worked
        mock_repository.find.assert_called_once()
        assert result == decision_id


class TestCacheDecoratorEdgeCases:
    """Test edge cases for cache decorators"""

    @pytest.mark.asyncio
    async def test_rule_cache_empty_result_not_cached(self):
        """Test empty rule list is still cached (valid result)"""
        mock_redis = MagicMock(spec=RedisClient)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)

        mock_repository = AsyncMock()
        mock_repository.find_active_rules = AsyncMock(return_value=[])

        decorator = RuleCacheDecorator(mock_repository, mock_redis, ttl=300)
        tenant_id = uuid4()

        # Execute
        result = await decorator.find_active_rules(tenant_id, "credit_approval")

        # Verify - empty list is still cached (it's a valid response)
        assert result == []
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_idempotency_cache_uuid_serialization(self):
        """Test idempotency cache correctly serializes/deserializes UUIDs"""
        mock_redis = MagicMock(spec=RedisClient)
        decision_id = uuid4()

        # Simulate cache hit with UUID as string
        mock_redis.get = AsyncMock(return_value=str(decision_id))

        mock_repository = AsyncMock()
        decorator = IdempotencyCacheDecorator(mock_repository, mock_redis, ttl=86400)
        tenant_id = uuid4()

        # Execute
        result = await decorator.find(tenant_id, "test_key")

        # Verify - UUID correctly deserialized
        assert isinstance(result, UUID)
        assert result == decision_id
