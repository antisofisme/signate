"""
Example: Using Redis Caching with Validation Use Cases

This example demonstrates how to use the new async validation functions
with Redis caching for improved performance.
"""

import asyncio
import time
from typing import Dict, Any

# Import async validation functions
from core.use_cases.validate_decision import validate_decision_async
from core.use_cases.quality_scoring import assess_quality_async

# Import cache protocol (replace with actual Redis adapter)
from core.ports.cache import CacheProtocol


class MockCache(CacheProtocol):
    """
    Mock cache for demonstration purposes.
    Replace with actual Redis implementation:
    from adapters.redis_cache import RedisCache
    """

    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        self.store[key] = value

    async def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self.store

    async def get_many(self, keys: list) -> dict:
        return {k: v for k, v in self.store.items() if k in keys}

    async def set_many(self, items: dict, ttl: int = 300):
        self.store.update(items)

    async def delete_pattern(self, pattern: str) -> int:
        # Simple pattern matching for mock
        import fnmatch
        keys = [k for k in self.store.keys() if fnmatch.fnmatch(k, pattern)]
        for k in keys:
            del self.store[k]
        return len(keys)

    async def clear(self):
        self.store.clear()

    async def close(self):
        pass


# Sample decision record
SAMPLE_RECORD = {
    "decision_id": "dec-001",
    "domain_id": "FRONTEND",
    "aspect_id": "ARCHITECTURE",
    "statement": "Use React 18 with TypeScript for all frontend applications",
    "rationale": (
        "React 18 provides better performance through concurrent rendering and automatic batching. "
        "TypeScript adds type safety which reduces runtime errors and improves developer experience. "
        "This combination is well-supported by the community and has excellent tooling."
    ),
    "constraints": [
        {
            "constraint_id": "c-001",
            "statement": "All new components must use functional components with hooks",
            "type": "REQUIREMENT"
        },
        {
            "constraint_id": "c-002",
            "statement": "Class components are prohibited in new code",
            "type": "PROHIBITION"
        }
    ],
    "invariants": [
        "Type safety must be maintained at build time",
        "All components must be testable"
    ],
    "scope": "ORGANIZATION",
    "blast_radius": "HIGH",
    "version": "1.0.0",
    "tags": ["FE", "ARCHITECTURE"],
    "tech_stack": ["React", "TypeScript", "Vite"],
    "related_decisions": []
}


async def example_validation_with_cache():
    """Example: Async validation with caching."""
    print("=" * 60)
    print("Example 1: Validation with Cache")
    print("=" * 60)

    # Initialize mock cache
    cache = MockCache()

    # First validation - cache miss (slow)
    print("\n1. First validation (cache miss)...")
    start = time.time()
    result1 = await validate_decision_async(SAMPLE_RECORD, cache=cache)
    elapsed1 = time.time() - start

    print(f"   Status: {result1.status}")
    print(f"   Violations: {len(result1.violations)}")
    print(f"   Time: {elapsed1*1000:.2f}ms")

    # Second validation - cache hit (fast)
    print("\n2. Second validation (cache hit)...")
    start = time.time()
    result2 = await validate_decision_async(SAMPLE_RECORD, cache=cache)
    elapsed2 = time.time() - start

    print(f"   Status: {result2.status}")
    print(f"   Violations: {len(result2.violations)}")
    print(f"   Time: {elapsed2*1000:.2f}ms")

    print(f"\n   Speedup: {elapsed1/elapsed2:.1f}x faster")

    await cache.close()


async def example_quality_scoring_with_cache():
    """Example: Quality assessment with cached coherence."""
    print("\n" + "=" * 60)
    print("Example 2: Quality Scoring with Cached Coherence")
    print("=" * 60)

    # Initialize mock cache
    cache = MockCache()

    # First assessment - cache miss for coherence (slow)
    print("\n1. First assessment (cache miss for SBERT)...")
    start = time.time()
    assessment1 = await assess_quality_async(SAMPLE_RECORD, cache=cache)
    elapsed1 = time.time() - start

    print(f"   Overall Score: {assessment1.overall_score}")
    print(f"   Grade: {assessment1.grade}")
    print(f"   Coherence Score: {assessment1.coherence_score:.2f}")
    print(f"   Coherence Method: {assessment1.readability.get('coherence_method', 'N/A')}")
    print(f"   Time: {elapsed1*1000:.2f}ms")

    # Second assessment - cache hit for coherence (fast)
    print("\n2. Second assessment (cache hit for SBERT)...")
    start = time.time()
    assessment2 = await assess_quality_async(SAMPLE_RECORD, cache=cache)
    elapsed2 = time.time() - start

    print(f"   Overall Score: {assessment2.overall_score}")
    print(f"   Grade: {assessment2.grade}")
    print(f"   Coherence Score: {assessment2.coherence_score:.2f}")
    print(f"   Coherence Method: {assessment2.readability.get('coherence_method', 'N/A')}")
    print(f"   Time: {elapsed2*1000:.2f}ms")

    print(f"\n   Speedup: {elapsed1/elapsed2:.1f}x faster")

    await cache.close()


async def example_without_cache():
    """Example: Validation without cache (backward compatible)."""
    print("\n" + "=" * 60)
    print("Example 3: Without Cache (Backward Compatible)")
    print("=" * 60)

    print("\n1. Async validation without cache...")
    start = time.time()
    result = await validate_decision_async(SAMPLE_RECORD, cache=None)
    elapsed = time.time() - start

    print(f"   Status: {result.status}")
    print(f"   Time: {elapsed*1000:.2f}ms")

    print("\n2. Quality assessment without cache...")
    start = time.time()
    assessment = await assess_quality_async(SAMPLE_RECORD, cache=None)
    elapsed = time.time() - start

    print(f"   Overall Score: {assessment.overall_score}")
    print(f"   Grade: {assessment.grade}")
    print(f"   Time: {elapsed*1000:.2f}ms")

    print("\n   Note: No caching - every call runs full computation")


async def example_cache_invalidation():
    """Example: Cache invalidation patterns."""
    print("\n" + "=" * 60)
    print("Example 4: Cache Invalidation")
    print("=" * 60)

    cache = MockCache()

    # Populate cache
    print("\n1. Populating cache...")
    await validate_decision_async(SAMPLE_RECORD, cache=cache)
    await assess_quality_async(SAMPLE_RECORD, cache=cache)

    # Check cache status
    print(f"   Cache entries: {len(cache.store)}")

    # Invalidate validation cache
    print("\n2. Invalidating validation cache...")
    deleted = await cache.delete_pattern("mantra:validation:*")
    print(f"   Deleted {deleted} entries")

    # Invalidate coherence cache
    print("\n3. Invalidating coherence cache...")
    deleted = await cache.delete_pattern("mantra:coherence:*")
    print(f"   Deleted {deleted} entries")

    # Clear entire cache
    print("\n4. Clearing entire cache...")
    await cache.clear()
    print(f"   Cache entries after clear: {len(cache.store)}")

    await cache.close()


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  ARSAKA_MANTRA Redis Caching Examples                    ║")
    print("╚" + "=" * 58 + "╝")

    await example_validation_with_cache()
    await example_quality_scoring_with_cache()
    await example_without_cache()
    await example_cache_invalidation()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
