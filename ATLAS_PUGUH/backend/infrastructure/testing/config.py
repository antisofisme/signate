"""
Load Test Configuration

Configuration for Locust load testing scenarios.

Source: Phase 2 Design & Execution Plan - Section 4.4
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LoadTestConfig:
    """
    Load test configuration

    Configuration for Locust load testing to compare:
    - Phase 1 Baseline: Without caching, rate limiting
    - Phase 2 Instrumented: With Redis caching, rate limiting, connection pooling

    Example:
        # Phase 1 baseline test
        config = LoadTestConfig(
            host="http://localhost:8001",
            redis_enabled=False
        )

        # Phase 2 instrumented test
        config = LoadTestConfig(
            host="http://localhost:8001",
            redis_enabled=True
        )
    """

    # Target host
    host: str = os.getenv("LOAD_TEST_HOST", "http://localhost:8001")

    # Redis configuration (for Phase 2 tests)
    redis_enabled: bool = os.getenv("LOAD_TEST_REDIS_ENABLED", "true").lower() == "true"

    # Test parameters
    users: int = int(os.getenv("LOAD_TEST_USERS", "10"))
    spawn_rate: float = float(os.getenv("LOAD_TEST_SPAWN_RATE", "1"))
    run_time: str = os.getenv("LOAD_TEST_RUN_TIME", "60s")

    # Test data
    tenant_id: str = os.getenv("LOAD_TEST_TENANT_ID", "550e8400-e29b-41d4-a716-446655440000")
    decision_type: str = os.getenv("LOAD_TEST_DECISION_TYPE", "credit_approval")

    # Rate limits (for Phase 2 tests)
    rate_limit_enabled: bool = os.getenv("LOAD_TEST_RATE_LIMIT_ENABLED", "true").lower() == "true"

    # Load test scenarios
    scenario: str = os.getenv("LOAD_TEST_SCENARIO", "mixed")  # decisions, workflows, mixed

    # Output
    output_dir: str = os.getenv("LOAD_TEST_OUTPUT_DIR", "./load_test_results")

    @classmethod
    def phase1_baseline(cls) -> "LoadTestConfig":
        """
        Configuration for Phase 1 baseline test

        - Redis disabled
        - Rate limiting disabled
        - Measures raw performance without optimizations
        """
        return cls(
            redis_enabled=False,
            rate_limit_enabled=False
        )

    @classmethod
    def phase2_instrumented(cls) -> "LoadTestConfig":
        """
        Configuration for Phase 2 instrumented test

        - Redis enabled (caching)
        - Rate limiting enabled
        - Measures optimized performance
        """
        return cls(
            redis_enabled=True,
            rate_limit_enabled=True
        )


# Load test scenarios configuration
SCENARIOS = {
    "decisions": {
        "weight": 100,
        "description": "Decision creation and retrieval load test"
    },
    "workflows": {
        "weight": 50,
        "description": "Workflow approval load test"
    },
    "mixed": {
        "decisions_weight": 70,
        "workflows_weight": 30,
        "description": "Mixed workload (70% decisions, 30% workflows)"
    }
}


# Expected performance targets (Phase 2 goals)
PERFORMANCE_TARGETS = {
    "p95_latency_ms": 200,        # 95th percentile < 200ms
    "p99_latency_ms": 500,        # 99th percentile < 500ms
    "error_rate_percent": 0.1,    # < 0.1% errors
    "throughput_rps": 100,        # > 100 requests/sec
    "cache_hit_rate_percent": 80  # > 80% cache hits (Phase 2)
}
