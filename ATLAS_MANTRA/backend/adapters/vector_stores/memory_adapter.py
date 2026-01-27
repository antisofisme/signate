"""
Memory Vector Store Adapter - In-memory implementation for testing.

This adapter stores vectors in memory using numpy for similarity
calculations. Useful for testing and development without external
dependencies.

Usage:
    store = MemoryVectorStore()
    await store.upsert(id="dec-001", vector=[...], payload={...})
    results = await store.search(query_vector=[...], limit=10)
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np

from core.ports.vector_store import VectorStoreProtocol, VectorSearchResult

logger = logging.getLogger(__name__)


@dataclass
class StoredVector:
    """Internal representation of a stored vector."""
    id: str
    vector: np.ndarray
    payload: Dict[str, Any]


class MemoryVectorStore(VectorStoreProtocol):
    """
    In-memory implementation of VectorStoreProtocol.

    Stores vectors in a dictionary and uses numpy for cosine
    similarity calculations. Suitable for:
    - Unit testing
    - Local development
    - Small datasets
    """

    def __init__(self, collection_name: str = "mantra_decisions"):
        """
        Initialize in-memory store.

        Args:
            collection_name: Name of the collection (for identification)
        """
        self.collection_name = collection_name
        self._vectors: Dict[str, StoredVector] = {}
        self._vector_size: Optional[int] = None
        self._initialized = False
        logger.info(f"Memory vector store initialized: {collection_name}")

    async def upsert(
        self,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """Insert or update a single vector."""
        self._vectors[id] = StoredVector(
            id=id,
            vector=np.array(vector, dtype=np.float32),
            payload=payload,
        )
        if self._vector_size is None:
            self._vector_size = len(vector)
        logger.debug(f"Upserted vector: {id}")

    async def upsert_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> int:
        """Batch upsert multiple vectors."""
        for item in items:
            await self.upsert(
                id=item["id"],
                vector=item["vector"],
                payload=item.get("payload", {}),
            )
        logger.debug(f"Batch upserted {len(items)} vectors")
        return len(items)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors with optional filtering."""
        if not self._vectors:
            return []

        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query)

        results = []
        for stored in self._vectors.values():
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    payload_value = stored.payload.get(key)
                    if isinstance(value, list):
                        # Handle list values (e.g., tags)
                        if payload_value not in value:
                            match = False
                            break
                    elif payload_value != value:
                        match = False
                        break
                if not match:
                    continue

            # Calculate cosine similarity
            stored_norm = np.linalg.norm(stored.vector)
            if query_norm == 0 or stored_norm == 0:
                score = 0.0
            else:
                score = float(np.dot(query, stored.vector) / (query_norm * stored_norm))

            if score >= min_score:
                results.append(
                    VectorSearchResult(
                        id=stored.id,
                        score=score,
                        payload=stored.payload,
                    )
                )

        # Sort by score descending and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        if id in self._vectors:
            del self._vectors[id]
            logger.debug(f"Deleted vector: {id}")
            return True
        return False

    async def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors by ID."""
        count = 0
        for id in ids:
            if id in self._vectors:
                del self._vectors[id]
                count += 1
        logger.debug(f"Deleted {count} vectors")
        return count

    async def get(self, id: str) -> Optional[VectorSearchResult]:
        """Retrieve a vector by ID."""
        if id in self._vectors:
            stored = self._vectors[id]
            return VectorSearchResult(
                id=stored.id,
                score=1.0,
                payload=stored.payload,
            )
        return None

    async def collection_exists(self) -> bool:
        """Check if collection is initialized."""
        return self._initialized

    async def create_collection(self, vector_size: int) -> None:
        """Initialize the collection."""
        self._vector_size = vector_size
        self._initialized = True
        logger.info(f"Memory collection initialized with size {vector_size}")

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "name": self.collection_name,
            "count": len(self._vectors),
            "vector_size": self._vector_size or 0,
            "status": "ready" if self._initialized else "not_initialized",
            "indexed_count": len(self._vectors),
        }

    async def close(self) -> None:
        """Clear the in-memory store."""
        self._vectors.clear()
        logger.info("Memory vector store closed")
