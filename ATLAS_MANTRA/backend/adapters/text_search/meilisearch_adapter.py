"""
Meilisearch Text Search Adapter - Implementation using Meilisearch.

Meilisearch provides fast, typo-tolerant full-text search with:
- Instant search results
- Typo tolerance
- Faceted search
- Customizable ranking

Requirements:
    pip install meilisearch-python-sdk

Usage:
    search = MeilisearchAdapter(url="http://localhost:7700", api_key="master_key")
    await search.index([{"id": "1", "title": "Hello World"}])
    results = await search.search(TextSearchQuery(query="hello"))
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.errors import MeilisearchApiError

from core.ports.text_search import (
    TextSearchProtocol,
    TextSearchQuery,
    TextSearchResult,
    TextSearchStats,
)

logger = logging.getLogger(__name__)


class MeilisearchAdapter(TextSearchProtocol):
    """
    Meilisearch implementation of TextSearchProtocol.

    Provides fast full-text search with:
    - Sub-50ms search responses
    - Typo tolerance
    - Highlighting
    - Faceted search
    """

    def __init__(
        self,
        url: str = "http://localhost:7700",
        api_key: Optional[str] = None,
        index_name: str = "mantra_decisions",
        searchable_fields: Optional[List[str]] = None,
        filterable_fields: Optional[List[str]] = None,
        sortable_fields: Optional[List[str]] = None,
    ):
        """
        Initialize Meilisearch client.

        Args:
            url: Meilisearch server URL
            api_key: API key (master key for admin operations)
            index_name: Name of the index
            searchable_fields: Fields to search in
            filterable_fields: Fields that can be filtered
            sortable_fields: Fields that can be sorted
        """
        self.url = url
        self.api_key = api_key
        self.index_name = index_name
        self.searchable_fields = searchable_fields or [
            "statement",
            "rationale",
            "decision_code",
            "domain_id",
            "feature_id",
            "tags",
        ]
        self.filterable_fields = filterable_fields or [
            "domain_id",
            "feature_id",
            "aspect_id",
            "tags",
            "status",
            "created_at",
        ]
        self.sortable_fields = sortable_fields or [
            "created_at",
            "updated_at",
            "decision_code",
        ]
        self.client = AsyncClient(url, api_key)
        self._index = None
        logger.info(f"Meilisearch adapter initialized: {url}, index={index_name}")

    async def _get_index(self):
        """Get or create the index."""
        if self._index is None:
            try:
                self._index = await self.client.get_index(self.index_name)
            except MeilisearchApiError:
                # Index doesn't exist, create it
                await self.client.create_index(
                    self.index_name,
                    primary_key="id"
                )
                self._index = await self.client.get_index(self.index_name)

                # Configure index settings
                await self._index.update_settings({
                    "searchableAttributes": self.searchable_fields,
                    "filterableAttributes": self.filterable_fields,
                    "sortableAttributes": self.sortable_fields,
                })
                logger.info(f"Created and configured index: {self.index_name}")

        return self._index

    async def index(self, documents: List[Dict[str, Any]]) -> int:
        """Index documents for searching."""
        if not documents:
            return 0

        try:
            index = await self._get_index()
            task = await index.add_documents(documents)
            # Wait for task to complete (optional, can be async)
            await self.client.wait_for_task(task.task_uid)
            logger.debug(f"Indexed {len(documents)} documents")
            return len(documents)
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise

    async def search(self, query: TextSearchQuery) -> List[TextSearchResult]:
        """Search for documents matching query."""
        try:
            index = await self._get_index()

            # Build search options
            opt_params = {
                "limit": query.limit,
                "offset": query.offset,
            }

            # Add filters
            if query.filters:
                filter_parts = []
                for field, value in query.filters.items():
                    if isinstance(value, list):
                        # OR filter for lists
                        filter_parts.append(f"{field} IN {value}")
                    else:
                        filter_parts.append(f"{field} = '{value}'")
                opt_params["filter"] = " AND ".join(filter_parts)

            # Add sort
            if query.sort:
                opt_params["sort"] = [
                    f"{field}:{direction}" for field, direction in query.sort
                ]

            # Add highlighting
            if query.highlight_fields:
                opt_params["attributesToHighlight"] = query.highlight_fields
            else:
                opt_params["attributesToHighlight"] = ["statement", "rationale"]

            # Execute search
            result = await index.search(query.query, **opt_params)

            # Convert to TextSearchResult
            results = []
            for hit in result.hits:
                # Extract highlights
                highlights = {}
                formatted = hit.get("_formatted", {})
                for field in opt_params.get("attributesToHighlight", []):
                    if field in formatted:
                        highlights[field] = formatted[field]

                # Build result - exclude Meilisearch internal fields
                doc = {k: v for k, v in hit.items() if not k.startswith("_")}

                results.append(TextSearchResult(
                    id=hit["id"],
                    score=1.0,  # Meilisearch doesn't expose scores by default
                    highlights=highlights,
                    document=doc,
                ))

            logger.debug(f"Search '{query.query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed for '{query.query}': {e}")
            return []

    async def delete(self, document_ids: List[str]) -> int:
        """Delete documents from index."""
        if not document_ids:
            return 0

        try:
            index = await self._get_index()
            task = await index.delete_documents(document_ids)
            await self.client.wait_for_task(task.task_uid)
            logger.debug(f"Deleted {len(document_ids)} documents")
            return len(document_ids)
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    async def update(self, documents: List[Dict[str, Any]]) -> int:
        """Update existing documents in index."""
        # Meilisearch uses upsert semantics for add_documents
        return await self.index(documents)

    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID."""
        try:
            index = await self._get_index()
            doc = await index.get_document(document_id)
            return dict(doc) if doc else None
        except MeilisearchApiError:
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Meilisearch is healthy."""
        try:
            health = await self.client.health()
            return health.status == "available"
        except Exception:
            return False

    async def get_stats(self) -> TextSearchStats:
        """Get index statistics."""
        try:
            index = await self._get_index()
            stats = await index.get_stats()

            return TextSearchStats(
                index_name=self.index_name,
                document_count=stats.number_of_documents,
                field_distribution=stats.field_distribution or {},
                last_update=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return TextSearchStats(
                index_name=self.index_name,
                document_count=0,
            )

    async def clear(self) -> None:
        """Clear all documents from the index."""
        try:
            index = await self._get_index()
            task = await index.delete_all_documents()
            await self.client.wait_for_task(task.task_uid)
            logger.info(f"Cleared all documents from {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            raise

    async def close(self) -> None:
        """Close the Meilisearch client."""
        await self.client.aclose()
        logger.info("Meilisearch client closed")
