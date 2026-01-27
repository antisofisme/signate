"""
Factory Module - Dependency Injection Container

This module provides factory methods for creating instances of
ports with their concrete adapter implementations.

Usage:
    from factory import Container
    vector_store = Container.get_vector_store()
    cache = Container.get_cache()
    embedding = Container.get_embedding()
"""

from .container import Container

__all__ = ["Container"]
