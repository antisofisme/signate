"""
Qdrant Vector Store Adapter

Implements VectorStore interface for Qdrant.
"""

from typing import Optional, List, Dict, Any
from uuid import uuid4

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
)

from ....core.interfaces import VectorStore
from ....core.entities import SearchResult
from ....config import QdrantConfig, get_settings
from ....shared.logging import get_logger

logger = get_logger(__name__)


class QdrantAdapter(VectorStore):
    """
    Qdrant implementation of VectorStore interface.

    Supports:
    - Vector similarity search
    - Metadata filtering
    - Batch operations
    - Collection management
    """

    def __init__(
        self,
        config: Optional[QdrantConfig] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        prefer_grpc: bool = False,
    ):
        if config:
            self.config = config
        else:
            # Allow individual parameters for container injection
            settings = get_settings()
            self.config = QdrantConfig(
                host=host or settings.qdrant.host,
                port=port or settings.qdrant.port,
                api_key=api_key or settings.qdrant.api_key,
                prefer_grpc=prefer_grpc or settings.qdrant.prefer_grpc,
            )
        self._client: Optional[AsyncQdrantClient] = None

    async def connect(self) -> None:
        """Explicitly connect to Qdrant."""
        if self._client is None:
            self._client = AsyncQdrantClient(
                host=self.config.host,
                port=self.config.port,
                api_key=self.config.api_key,
                prefer_grpc=self.config.prefer_grpc,
            )
            logger.info(f"Connected to Qdrant at {self.config.url}")

    async def _get_client(self) -> AsyncQdrantClient:
        """Get or create async client."""
        if self._client is None:
            await self.connect()
        return self._client

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            collection: Collection name
            query_vector: Query embedding
            top_k: Number of results
            filters: Metadata filters (e.g., {"tenant_id": "abc"})
            score_threshold: Minimum similarity score

        Returns:
            List of SearchResult ordered by similarity
        """
        client = await self._get_client()

        # Build filter
        qdrant_filter = self._build_filter(filters) if filters else None

        # Search
        try:
            results = await client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
                search_params=SearchParams(
                    hnsw_ef=128,  # Higher = more accurate but slower
                    exact=False,
                ),
            )

            return [
                SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    content=hit.payload.get("content", ""),
                    metadata=hit.payload,
                    document_id=hit.payload.get("document_id"),
                )
                for hit in results
            ]

        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            raise

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Insert or update a vector.

        Args:
            collection: Collection name
            id: Point ID
            vector: Embedding vector
            payload: Metadata payload

        Returns:
            True if successful
        """
        client = await self._get_client()

        try:
            await client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            return True

        except Exception as e:
            logger.error(f"Qdrant upsert error: {e}")
            raise

    async def upsert_batch(
        self,
        collection: str,
        items: List[Dict[str, Any]]
    ) -> int:
        """
        Batch insert/update vectors.

        Args:
            collection: Collection name
            items: List of {id, vector, payload}

        Returns:
            Number of vectors upserted
        """
        client = await self._get_client()

        points = [
            PointStruct(
                id=item["id"],
                vector=item["vector"],
                payload=item.get("payload", {}),
            )
            for item in items
        ]

        try:
            await client.upsert(
                collection_name=collection,
                points=points,
            )
            return len(points)

        except Exception as e:
            logger.error(f"Qdrant batch upsert error: {e}")
            raise

    async def delete(self, collection: str, id: str) -> bool:
        """Delete a vector by ID."""
        client = await self._get_client()

        try:
            await client.delete(
                collection_name=collection,
                points_selector=[id],
            )
            return True

        except Exception as e:
            logger.error(f"Qdrant delete error: {e}")
            raise

    async def delete_by_filter(
        self,
        collection: str,
        filters: Dict[str, Any]
    ) -> int:
        """
        Delete vectors matching filter.

        Args:
            collection: Collection name
            filters: Metadata filters

        Returns:
            Number of vectors deleted (estimated)
        """
        client = await self._get_client()
        qdrant_filter = self._build_filter(filters)

        try:
            # Count before delete (for return value)
            count_result = await client.count(
                collection_name=collection,
                count_filter=qdrant_filter,
            )

            # Delete
            await client.delete(
                collection_name=collection,
                points_selector=qdrant_filter,
            )

            return count_result.count

        except Exception as e:
            logger.error(f"Qdrant delete_by_filter error: {e}")
            raise

    async def ensure_collection(
        self,
        collection: str,
        vector_size: int
    ) -> bool:
        """
        Ensure collection exists with correct configuration.

        Args:
            collection: Collection name
            vector_size: Dimension of vectors

        Returns:
            True if collection exists/created
        """
        client = await self._get_client()

        try:
            # Check if collection exists
            collections = await client.get_collections()
            exists = any(c.name == collection for c in collections.collections)

            if not exists:
                # Create collection
                await client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {collection} (dim={vector_size})")

                # Create indexes for common filter fields
                await self._create_payload_indexes(collection)

            return True

        except Exception as e:
            logger.error(f"Qdrant ensure_collection error: {e}")
            raise

    async def _create_payload_indexes(self, collection: str) -> None:
        """Create payload indexes for common filter fields."""
        client = await self._get_client()

        index_fields = ["tenant_id", "user_id", "source", "document_id"]

        for field in index_fields:
            try:
                await client.create_payload_index(
                    collection_name=collection,
                    field_name=field,
                    field_schema="keyword",
                )
            except Exception:
                # Index might already exist
                pass

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dict."""
        conditions = []

        for key, value in filters.items():
            if value is not None:
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

        return Filter(must=conditions) if conditions else None

    async def get_by_id(
        self,
        collection: str,
        point_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a point by ID.

        Args:
            collection: Collection name
            point_id: Point ID

        Returns:
            Point data with vector and payload, or None if not found
        """
        client = await self._get_client()

        try:
            results = await client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_vectors=True,
                with_payload=True,
            )

            if not results:
                return None

            point = results[0]
            return {
                "id": str(point.id),
                "vector": point.vector,
                "payload": point.payload,
            }

        except Exception as e:
            logger.error(f"Qdrant get_by_id error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check Qdrant connectivity."""
        try:
            client = await self._get_client()
            await client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics."""
        client = await self._get_client()

        try:
            info = await client.get_collection(collection_name=collection)
            return {
                "name": collection,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            logger.error(f"Qdrant get_collection_info error: {e}")
            return {"name": collection, "error": str(e)}
