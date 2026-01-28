"""
Memory Text Search Adapter - In-memory implementation for testing.

This adapter stores documents in memory and performs simple text matching.
Perfect for unit tests and local development without Meilisearch.

Usage:
    search = MemoryTextSearchAdapter()
    await search.index([{"id": "1", "statement": "Use PostgreSQL"}])
    results = await search.search(TextSearchQuery(query="postgres"))
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.ports.text_search import (
    TextSearchProtocol,
    TextSearchQuery,
    TextSearchResult,
    TextSearchStats,
)

logger = logging.getLogger(__name__)


class MemoryTextSearchAdapter(TextSearchProtocol):
    """
    In-memory implementation of TextSearchProtocol.

    Uses simple text matching for search:
    - Case-insensitive matching
    - Partial word matching
    - Basic highlighting
    """

    def __init__(
        self,
        index_name: str = "mantra_decisions",
        searchable_fields: Optional[List[str]] = None,
    ):
        """
        Initialize in-memory search.

        Args:
            index_name: Name of the index (for stats)
            searchable_fields: Fields to search in
        """
        self.index_name = index_name
        self.searchable_fields = searchable_fields or [
            "statement",
            "rationale",
            "decision_code",
            "domain_id",
            "feature_id",
            "tags",
        ]
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._last_update: Optional[str] = None
        logger.info(f"Memory text search adapter initialized: index={index_name}")

    async def index(self, documents: List[Dict[str, Any]]) -> int:
        """Index documents for searching."""
        count = 0
        for doc in documents:
            if "id" not in doc:
                logger.warning("Document missing 'id' field, skipping")
                continue
            self._documents[doc["id"]] = doc
            count += 1

        self._last_update = datetime.utcnow().isoformat()
        logger.debug(f"Indexed {count} documents")
        return count

    async def search(self, query: TextSearchQuery) -> List[TextSearchResult]:
        """Search for documents matching query."""
        results = []
        query_lower = query.query.lower()
        query_terms = query_lower.split()

        for doc_id, doc in self._documents.items():
            # Check filters first
            if query.filters:
                if not self._matches_filters(doc, query.filters):
                    continue

            # Calculate match score
            score = self._calculate_score(doc, query_terms)
            if score <= 0:
                continue

            # Generate highlights
            highlights = self._generate_highlights(
                doc,
                query_terms,
                query.highlight_fields or ["statement", "rationale"]
            )

            results.append(TextSearchResult(
                id=doc_id,
                score=score,
                highlights=highlights,
                document=doc,
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        # Apply pagination
        start = query.offset
        end = start + query.limit
        results = results[start:end]

        logger.debug(f"Search '{query.query}' returned {len(results)} results")
        return results

    def _matches_filters(self, doc: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches all filters."""
        for field, value in filters.items():
            doc_value = doc.get(field)
            if doc_value is None:
                return False

            if isinstance(value, list):
                if doc_value not in value:
                    return False
            elif isinstance(doc_value, list):
                if value not in doc_value:
                    return False
            elif doc_value != value:
                return False

        return True

    def _calculate_score(self, doc: Dict[str, Any], query_terms: List[str]) -> float:
        """Calculate relevance score for a document."""
        score = 0.0

        for field in self.searchable_fields:
            field_value = doc.get(field)
            if field_value is None:
                continue

            # Convert to string for matching
            if isinstance(field_value, list):
                text = " ".join(str(v) for v in field_value)
            else:
                text = str(field_value)

            text_lower = text.lower()

            # Score based on term matches
            for term in query_terms:
                if term in text_lower:
                    # Exact word match scores higher
                    if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                        score += 2.0
                    else:
                        score += 1.0

                    # Bonus for match in important fields
                    if field in ["statement", "decision_code"]:
                        score += 0.5

        return score

    def _generate_highlights(
        self,
        doc: Dict[str, Any],
        query_terms: List[str],
        fields: List[str]
    ) -> Dict[str, str]:
        """Generate highlighted snippets for matching fields."""
        highlights = {}

        for field in fields:
            field_value = doc.get(field)
            if field_value is None:
                continue

            if isinstance(field_value, list):
                text = " ".join(str(v) for v in field_value)
            else:
                text = str(field_value)

            # Highlight matching terms with <em> tags
            highlighted = text
            for term in query_terms:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted = pattern.sub(f"<em>{term}</em>", highlighted)

            if highlighted != text:
                highlights[field] = highlighted

        return highlights

    async def delete(self, document_ids: List[str]) -> int:
        """Delete documents from index."""
        count = 0
        for doc_id in document_ids:
            if doc_id in self._documents:
                del self._documents[doc_id]
                count += 1

        self._last_update = datetime.utcnow().isoformat()
        logger.debug(f"Deleted {count} documents")
        return count

    async def update(self, documents: List[Dict[str, Any]]) -> int:
        """Update existing documents in index."""
        # Same as index for in-memory (upsert)
        return await self.index(documents)

    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID."""
        return self._documents.get(document_id)

    async def health_check(self) -> bool:
        """Check if the search service is healthy."""
        return True

    async def get_stats(self) -> TextSearchStats:
        """Get index statistics."""
        # Calculate field distribution for domain_id
        field_distribution = {}
        for doc in self._documents.values():
            domain = doc.get("domain_id")
            if domain:
                if "domain_id" not in field_distribution:
                    field_distribution["domain_id"] = {}
                field_distribution["domain_id"][domain] = \
                    field_distribution["domain_id"].get(domain, 0) + 1

        return TextSearchStats(
            index_name=self.index_name,
            document_count=len(self._documents),
            field_distribution=field_distribution,
            last_update=self._last_update,
        )

    async def clear(self) -> None:
        """Clear all documents from the index."""
        self._documents.clear()
        self._last_update = datetime.utcnow().isoformat()
        logger.info("Cleared all documents")

    # Test helpers

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all indexed documents (for testing)."""
        return list(self._documents.values())
