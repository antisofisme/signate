"""
Locust Load Test File

Main entry point for Locust load testing.

Usage:
    # Phase 1 baseline test (no caching, no rate limiting)
    locust -f locustfile.py --host http://localhost:8001 \
           --users 10 --spawn-rate 1 --run-time 60s \
           --tags baseline

    # Phase 2 instrumented test (with caching, rate limiting)
    locust -f locustfile.py --host http://localhost:8001 \
           --users 10 --spawn-rate 1 --run-time 60s \
           --tags instrumented

    # Specific scenario
    locust -f locustfile.py --host http://localhost:8001 \
           DecisionTestScenario

    # Web UI mode (interactive)
    locust -f locustfile.py --host http://localhost:8001

Source: Phase 2 Design & Execution Plan - Section 4.4
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from infrastructure.testing.scenarios import (
    DecisionTestScenario,
    WorkflowTestScenario,
    MixedWorkloadScenario
)
from infrastructure.testing.config import LoadTestConfig, SCENARIOS

# Export test scenarios for Locust
__all__ = [
    "DecisionTestScenario",
    "WorkflowTestScenario",
    "MixedWorkloadScenario"
]


# Locust configuration from environment
def on_locust_init(environment, **kwargs):
    """
    Locust initialization hook

    Called when Locust starts. Used to:
    - Print test configuration
    - Validate environment
    - Set up test data
    """
    config = LoadTestConfig()

    print("\n" + "=" * 60)
    print("LOCUST LOAD TEST CONFIGURATION")
    print("=" * 60)
    print(f"Host: {config.host}")
    print(f"Redis Enabled: {config.redis_enabled}")
    print(f"Rate Limiting Enabled: {config.rate_limit_enabled}")
    print(f"Scenario: {config.scenario}")
    print(f"Users: {config.users}")
    print(f"Spawn Rate: {config.spawn_rate}")
    print(f"Run Time: {config.run_time}")
    print(f"Tenant ID: {config.tenant_id}")
    print(f"Decision Type: {config.decision_type}")
    print("=" * 60)
    print("\nStarting load test...\n")


def on_test_start(environment, **kwargs):
    """
    Test start hook

    Called when test starts (after all users spawned).
    """
    print("\n[TEST START] All users spawned, test running...\n")


def on_test_stop(environment, **kwargs):
    """
    Test stop hook

    Called when test stops.
    Prints summary statistics.
    """
    stats = environment.stats

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    print(f"\nLatency (ms):")
    print(f"  50th percentile: {stats.total.get_response_time_percentile(0.50):.0f}")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.0f}")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.0f}")
    print(f"  Average: {stats.total.avg_response_time:.0f}")
    print(f"  Min: {stats.total.min_response_time:.0f}")
    print(f"  Max: {stats.total.max_response_time:.0f}")
    print("=" * 60)
    print("\nTest completed. Check detailed stats in Locust UI or reports.\n")


# Register hooks (only if running as main locustfile)
if __name__ != "__main__":
    from locust import events

    events.init.add_listener(on_locust_init)
    events.test_start.add_listener(on_test_start)
    events.test_stop.add_listener(on_test_stop)
