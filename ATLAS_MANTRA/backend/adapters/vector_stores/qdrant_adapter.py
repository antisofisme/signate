"""
Qdrant Vector Store Adapter - Implementation using Qdrant vector database.

Qdrant is a high-performance vector database optimized for
similarity search with filtering capabilities.

Requirements:
    pip install qdrant-client>=1.6.0

Usage:
    store = QdrantVectorStore(url="http://localhost:6333")
    await store.create_collection(vector_size=1536)
    await store.upsert(id="dec-001", vector=[...], payload={...})
    results = await store.search(query_vector=[...], limit=10)
"""

import logging
from typing import List, Optional, Dict, Any

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from core.ports.vector_store import VectorStoreProtocol, VectorSearchResult

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStoreProtocol):
    """
    Qdrant implementation of VectorStoreProtocol.

    Provides high-performance vector similarity search with:
    - Payload filtering
    - Batch operations
    - Efficient memory usage
    - True async operations (non-blocking)
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "mantra_decisions",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Qdrant async client.

        Args:
            url: Qdrant server URL
            collection_name: Name of the collection to use
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.url = url
        self.collection_name = collection_name
        self.api_key = api_key
        self.timeout = timeout

        # Initialize async client (non-blocking)
        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
            timeout=timeout,
        )
        logger.info(f"Qdrant async client initialized: {url}, collection={collection_name}")

    async def upsert(
        self,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """Insert or update a single vector."""
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.debug(f"Upserted vector: {id}")
        except Exception as e:
            logger.error(f"Upsert failed for {id}: {e}")
            raise

    async def upsert_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> int:
        """Batch upsert multiple vectors."""
        if not items:
            return 0

        try:
            points = [
                models.PointStruct(
                    id=item["id"],
                    vector=item["vector"],
                    payload=item.get("payload", {}),
                )
                for item in items
            ]

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.debug(f"Batch upserted {len(items)} vectors")
            return len(items)
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors with optional filtering."""
        try:
            # Build filter conditions
            filter_obj = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle list values (e.g., tags)
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value),
                            )
                        )
                    else:
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value),
                            )
                        )
                filter_obj = models.Filter(must=conditions)

            # Perform search
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=min_score if min_score > 0 else None,
                query_filter=filter_obj,
            )

            # Convert to VectorSearchResult
            return [
                VectorSearchResult(
                    id=str(r.id),
                    score=r.score,
                    payload=r.payload or {},
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[id]),
            )
            logger.debug(f"Deleted vector: {id}")
            return True
        except Exception as e:
            logger.error(f"Delete failed for {id}: {e}")
            return False

    async def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors by ID."""
        if not ids:
            return 0

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=ids),
            )
            logger.debug(f"Deleted {len(ids)} vectors")
            return len(ids)
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            raise

    async def get(self, id: str) -> Optional[VectorSearchResult]:
        """Retrieve a vector by ID."""
        try:
            results = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=[id],
                with_vectors=True,
                with_payload=True,
            )
            if results:
                point = results[0]
                return VectorSearchResult(
                    id=str(point.id),
                    score=1.0,  # Exact match
                    payload=point.payload or {},
                )
            return None
        except Exception as e:
            logger.error(f"Get failed for {id}: {e}")
            return None

    async def collection_exists(self) -> bool:
        """Check if collection exists."""
        try:
            collections = await self.client.get_collections()
            return any(c.name == self.collection_name for c in collections.collections)
        except Exception as e:
            logger.error(f"Collection check failed: {e}")
            return False

    async def create_collection(self, vector_size: int) -> None:
        """Create collection if it doesn't exist."""
        try:
            if await self.collection_exists():
                logger.info(f"Collection {self.collection_name} already exists")
                return

            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Created collection {self.collection_name} with size {vector_size}")

            # Create payload indexes for filtering
            for field in ["domain_id", "aspect_id", "decision_code"]:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            logger.info("Created payload indexes")
        except Exception as e:
            logger.error(f"Create collection failed: {e}")
            raise

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "count": info.points_count,
                "vector_size": info.config.params.vectors.size if info.config else 0,
                "status": info.status.value if info.status else "unknown",
                "indexed_count": info.indexed_vectors_count,
            }
        except Exception as e:
            logger.error(f"Get collection info failed: {e}")
            return {
                "name": self.collection_name,
                "count": 0,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close the client connection."""
        # Qdrant client doesn't require explicit cleanup
        logger.info("Qdrant client closed")
