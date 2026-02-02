"""
Text Search Port - Abstract interface for full-text search operations.

This port defines the contract for full-text search used to complement
semantic vector search. Implementations can use:
- Meilisearch (primary)
- Elasticsearch (alternative)
- In-memory (testing)

Usage:
    class MeilisearchAdapter(TextSearchProtocol):
        async def search(self, query):
            # Meilisearch-specific implementation
            ...
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TextSearchResult:
    """
    A single text search result.

    Attributes:
        id: Document identifier
        score: Relevance score (implementation-specific)
        highlights: Matched text snippets by field
        document: Full document data
    """
    id: str
    score: float
    highlights: Dict[str, str]
    document: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "id": self.id,
            "score": self.score,
            "highlights": self.highlights,
            "document": self.document,
        }


@dataclass
class TextSearchQuery:
    """
    Query parameters for text search.

    Attributes:
        query: Search query string
        filters: Field filters (e.g., {"domain_id": "INT"})
        limit: Maximum results to return
        offset: Results to skip (pagination)
        highlight_fields: Fields to include highlights for
        sort: Sort field and direction (e.g., [("created_at", "desc")])
    """
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 20
    offset: int = 0
    highlight_fields: Optional[List[str]] = None
    sort: Optional[List[tuple]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize query to dictionary."""
        return {
            "query": self.query,
            "filters": self.filters,
            "limit": self.limit,
            "offset": self.offset,
            "highlight_fields": self.highlight_fields,
            "sort": self.sort,
        }


@dataclass
class TextSearchStats:
    """
    Statistics about a text search index.

    Attributes:
        index_name: Name of the index
        document_count: Number of documents
        field_distribution: Count per field value (for facets)
        last_update: Last index update timestamp
    """
    index_name: str
    document_count: int
    field_distribution: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_update: Optional[str] = None


class TextSearchProtocol(ABC):
    """
    Abstract protocol for text search operations.

    This interface allows swapping search implementations
    without changing business logic. Supports:
    - Meilisearch (primary)
    - Elasticsearch (alternative)
    - In-memory (testing/development)
    """

    @abstractmethod
    async def index(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index documents for searching.

        Args:
            documents: List of documents to index (must have "id" field)

        Returns:
            Number of documents indexed
        """
        pass

    @abstractmethod
    async def search(self, query: TextSearchQuery) -> List[TextSearchResult]:
        """
        Search for documents matching query.

        Args:
            query: Search query parameters

        Returns:
            List of search results ranked by relevance
        """
        pass

    @abstractmethod
    async def delete(self, document_ids: List[str]) -> int:
        """
        Delete documents from index.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    async def update(self, documents: List[Dict[str, Any]]) -> int:
        """
        Update existing documents in index.

        Args:
            documents: List of documents to update (must have "id" field)

        Returns:
            Number of documents updated
        """
        pass

    @abstractmethod
    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document data if found, None otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the search service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_stats(self) -> TextSearchStats:
        """
        Get index statistics.

        Returns:
            TextSearchStats with index information
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the index."""
        pass

    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass

    # Convenience methods

    async def index_one(self, document: Dict[str, Any]) -> bool:
        """
        Index a single document.

        Args:
            document: Document to index

        Returns:
            True if indexed successfully
        """
        count = await self.index([document])
        return count > 0

    async def delete_one(self, document_id: str) -> bool:
        """
        Delete a single document.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted successfully
        """
        count = await self.delete([document_id])
        return count > 0

    async def update_one(self, document: Dict[str, Any]) -> bool:
        """
        Update a single document.

        Args:
            document: Document to update

        Returns:
            True if updated successfully
        """
        count = await self.update([document])
        return count > 0
