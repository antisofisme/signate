"""
Text Search Adapters - Implementations for full-text search.

Available adapters:
- MeilisearchAdapter: Meilisearch implementation (primary) - requires meilisearch-python-sdk
- MemoryTextSearchAdapter: In-memory implementation (testing)

Note: Imports are lazy to avoid requiring all dependencies.
"""


def __getattr__(name):
    """Lazy import adapters to avoid requiring all dependencies."""
    if name == "MeilisearchAdapter":
        from .meilisearch_adapter import MeilisearchAdapter
        return MeilisearchAdapter
    elif name == "MemoryTextSearchAdapter":
        from .memory_adapter import MemoryTextSearchAdapter
        return MemoryTextSearchAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "MeilisearchAdapter",
    "MemoryTextSearchAdapter",
]
