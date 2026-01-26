"""
Database Infrastructure

Provides database connection pool configuration and optimization.

Source: Phase 2 Design & Execution Plan - Section 4.2
"""

from .pool_config import create_optimized_engine, get_pool_stats

__all__ = [
    "create_optimized_engine",
    "get_pool_stats",
]
