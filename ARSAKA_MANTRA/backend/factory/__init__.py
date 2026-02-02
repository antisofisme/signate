"""
Factory Module - Dependency Injection Container and Factories

This module provides factory methods for creating instances of
ports with their concrete adapter implementations.

Factory Modules:
- Container: Main facade (backward compatible)
- CacheFactory: Cache adapters (Redis, Memory)
- SearchFactory: Vector store, embedding, text search
- StorageFactory: Repository, message queue
- ValidationFactory: Validation pipeline, approval manager

Usage:
    # Using main container (recommended)
    from factory import Container
    cache = Container.get_cache()
    repository = Container.get_decision_repository()

    # Using specific factories (for team isolation)
    from factory import SearchFactory
    vector_store = SearchFactory.get_vector_store()

    from factory import ValidationFactory
    pipeline = ValidationFactory.get_validation_pipeline()
"""

from .container import Container
from .cache_factory import CacheFactory
from .search_factory import SearchFactory
from .storage_factory import StorageFactory
from .validation_factory import ValidationFactory

__all__ = [
    "Container",
    "CacheFactory",
    "SearchFactory",
    "StorageFactory",
    "ValidationFactory",
]
