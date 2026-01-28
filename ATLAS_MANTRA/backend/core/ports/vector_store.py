"""
Vector Store Port - Abstract interface for vector database operations.

This port defines the contract for vector storage operations used in
semantic search. Implementations can use Qdrant, Pinecone, Weaviate,
or any other vector database.

Usage:
    class QdrantVectorStore(VectorStoreProtocol):
        async def upsert(self, id, vector, payload):
            # Qdrant-specific implementation
            ...
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Result from vector similarity search."""
    id: str
    score: float
    payload: Dict[str, Any]


class VectorStoreProtocol(ABC):
    """
    Abstract protocol for vector store operations.

    This interface allows swapping vector database implementations
    without changing business logic. Supports:
    - Qdrant (primary)
    - Pinecone
    - In-memory (testing)
    """

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """
        Insert or update a vector with its payload.

        Args:
            id: Unique identifier for the vector (decision_id)
            vector: Embedding vector (list of floats)
            payload: Metadata to store with the vector (decision fields)
        """
        pass

    @abstractmethod
    async def upsert_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> int:
        """
        Batch upsert multiple vectors.

        Args:
            items: List of dicts with 'id', 'vector', 'payload' keys

        Returns:
            Number of items successfully upserted
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: The query embedding vector
            limit: Maximum number of results
            min_score: Minimum similarity score (0.0 to 1.0)
            filters: Optional field filters (e.g., {"domain_id": "INT"})

        Returns:
            List of VectorSearchResult ordered by similarity (highest first)
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a vector by ID.

        Args:
            id: Vector ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def delete_batch(self, ids: List[str]) -> int:
        """
        Delete multiple vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[VectorSearchResult]:
        """
        Retrieve a vector by ID.

        Args:
            id: Vector ID

        Returns:
            VectorSearchResult if found, None otherwise
        """
        pass

    @abstractmethod
    async def collection_exists(self) -> bool:
        """
        Check if the collection/index exists.

        Returns:
            True if collection exists
        """
        pass

    @abstractmethod
    async def create_collection(self, vector_size: int) -> None:
        """
        Create the collection/index if it doesn't exist.

        Args:
            vector_size: Dimension of vectors (e.g., 1536 for OpenAI)
        """
        pass

    @abstractmethod
    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection statistics and metadata.

        Returns:
            Dict with 'count', 'vector_size', 'status', etc.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
