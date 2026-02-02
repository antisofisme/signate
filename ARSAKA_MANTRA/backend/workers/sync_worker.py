"""
Sync Worker - Handles embedding and search index synchronization.

This worker subscribes to sync queue and:
1. Receives sync requests for decisions
2. Generates/updates embeddings in vector store
3. Updates text search index
4. Publishes sync completion events

Usage:
    worker = SyncWorker(queue)
    await worker.start()
"""

import logging
from typing import Optional, List

from core.ports.message_queue import MessageQueueProtocol, Message, MantraEvents
from core.ports.cache import CacheProtocol, CacheKeys
from core.ports.text_search import TextSearchProtocol
from core.runtime.config import get_config
from .base import BaseWorker

logger = logging.getLogger(__name__)


class SyncWorker(BaseWorker):
    """
    Worker that handles embedding and index synchronization.

    Listens for sync events and updates:
    - Vector embeddings (Qdrant)
    - Text search index (Meilisearch)
    - Cache invalidation
    """

    def __init__(
        self,
        queue: MessageQueueProtocol,
        cache: Optional[CacheProtocol] = None,
        text_search: Optional[TextSearchProtocol] = None,
    ):
        """
        Initialize sync worker.

        Args:
            queue: Message queue implementation
            cache: Optional cache for invalidation
            text_search: Optional text search for indexing
        """
        super().__init__(queue, name="sync")
        self.cache = cache
        self.text_search = text_search
        self.config = get_config()

    async def setup(self) -> None:
        """Subscribe to sync queue."""
        queue_name = self.config.rabbitmq_queue_sync

        await self.queue.subscribe(
            queue_name,
            self._handle_sync_request,
            prefetch_count=10,
        )
        logger.info(f"Sync worker subscribed to: {queue_name}")

    async def _handle_sync_request(self, message: Message) -> None:
        """
        Handle incoming sync request.

        Args:
            message: Message containing sync request
        """
        logger.debug(f"Processing sync request: {message.id}")

        event_type = message.event_type
        payload = message.payload

        try:
            if event_type == MantraEvents.EMBEDDING_SYNC_REQUESTED:
                await self._sync_embeddings(message)
            elif event_type == MantraEvents.SEARCH_INDEX_REQUESTED:
                await self._sync_text_index(message)
            elif event_type == MantraEvents.DECISION_APPROVED:
                await self._sync_approved_decision(message)
            elif event_type == MantraEvents.CACHE_INVALIDATE:
                await self._invalidate_cache(message)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Sync error for message {message.id}: {e}")
            raise

    async def _sync_embeddings(self, message: Message) -> None:
        """
        Sync embeddings for decisions.

        Args:
            message: Message with sync parameters
        """
        from factory.container import Container

        payload = message.payload
        decision_ids = payload.get("decision_ids", [])
        force_rebuild = payload.get("force_rebuild", False)
        batch_size = payload.get("batch_size", 50)

        logger.info(f"Syncing embeddings: {len(decision_ids) or 'all'} decisions")

        if not Container.is_semantic_search_enabled():
            logger.warning("Semantic search disabled, skipping embedding sync")
            return

        try:
            from core.use_cases.sync_embeddings import SyncEmbeddingsUseCase, SyncEmbeddingsInput

            use_case = SyncEmbeddingsUseCase(
                vector_store=Container.get_vector_store(),
                embedding_service=Container.get_embedding(),
                repository=Container.get_decision_repository(),
            )

            result = await use_case.execute(SyncEmbeddingsInput(
                decision_ids=decision_ids if decision_ids else None,
                batch_size=batch_size,
                force_rebuild=force_rebuild,
            ))

            # Publish completion
            await self.queue.publish("sync_results", Message(
                event_type=MantraEvents.EMBEDDING_SYNC_COMPLETED,
                payload={
                    "synced_count": result.synced_count,
                    "failed_count": result.failed_count,
                    "execution_time_ms": result.execution_time_ms,
                },
                correlation_id=message.correlation_id,
            ))

            logger.info(f"Embedding sync completed: {result.synced_count} synced, {result.failed_count} failed")

        except Exception as e:
            logger.error(f"Embedding sync failed: {e}")

            # Publish failure
            await self.queue.publish("sync_results", Message(
                event_type=MantraEvents.EMBEDDING_SYNC_FAILED,
                payload={"error": str(e)},
                correlation_id=message.correlation_id,
            ))
            raise

    async def _sync_text_index(self, message: Message) -> None:
        """
        Sync text search index.

        Args:
            message: Message with index parameters
        """
        from factory.container import Container

        payload = message.payload
        decision_ids = payload.get("decision_ids", [])

        logger.info(f"Syncing text index: {len(decision_ids) or 'all'} decisions")

        text_search = self.text_search or Container.get_text_search()
        if not text_search:
            logger.warning("Text search disabled, skipping index sync")
            return

        try:
            repository = Container.get_decision_repository()

            # Get decisions to index
            if decision_ids:
                decisions = [repository.find_by_id(d_id) for d_id in decision_ids]
                decisions = [d for d in decisions if d]
            else:
                decisions = repository.list_all()

            # Build documents for indexing
            documents = []
            for d in decisions:
                documents.append({
                    "id": d.id,
                    "decision_code": d.decision_code,
                    "statement": d.statement,
                    "rationale": d.rationale or "",
                    "domain_id": str(d.domain_id.value) if hasattr(d.domain_id, 'value') else str(d.domain_id),
                    "feature_id": str(d.feature_id) if d.feature_id else "",
                    "aspect_id": str(d.aspect_id.value) if hasattr(d.aspect_id, 'value') else str(d.aspect_id),
                    "tags": [str(t.value) if hasattr(t, 'value') else str(t) for t in (d.tags or [])],
                    "status": d.status.value if hasattr(d.status, 'value') else str(d.status),
                    "created_at": d.created_at.isoformat() if d.created_at else "",
                })

            # Index documents
            indexed_count = await text_search.index(documents)

            # Publish completion
            await self.queue.publish("sync_results", Message(
                event_type=MantraEvents.SEARCH_INDEX_COMPLETED,
                payload={
                    "indexed_count": indexed_count,
                    "total_documents": len(documents),
                },
                correlation_id=message.correlation_id,
            ))

            logger.info(f"Text index sync completed: {indexed_count} documents indexed")

        except Exception as e:
            logger.error(f"Text index sync failed: {e}")
            raise

    async def _sync_approved_decision(self, message: Message) -> None:
        """
        Sync a newly approved decision to all indexes.

        Args:
            message: Message with decision data
        """
        payload = message.payload
        decision_id = payload.get("decision_id")

        if not decision_id:
            logger.warning("No decision_id in approved decision event")
            return

        logger.info(f"Syncing approved decision: {decision_id}")

        # Sync embeddings
        await self._sync_embeddings(Message(
            event_type=MantraEvents.EMBEDDING_SYNC_REQUESTED,
            payload={"decision_ids": [decision_id]},
            correlation_id=message.correlation_id,
        ))

        # Sync text index
        await self._sync_text_index(Message(
            event_type=MantraEvents.SEARCH_INDEX_REQUESTED,
            payload={"decision_ids": [decision_id]},
            correlation_id=message.correlation_id,
        ))

        # Invalidate related caches
        await self._invalidate_decision_cache(decision_id)

    async def _invalidate_cache(self, message: Message) -> None:
        """
        Invalidate cache entries.

        Args:
            message: Message with cache keys to invalidate
        """
        if not self.cache:
            return

        payload = message.payload
        patterns = payload.get("patterns", [])
        keys = payload.get("keys", [])

        # Delete by pattern
        for pattern in patterns:
            count = await self.cache.delete_pattern(pattern)
            logger.debug(f"Deleted {count} keys matching {pattern}")

        # Delete specific keys
        for key in keys:
            await self.cache.delete(key)

        logger.info(f"Cache invalidation completed: {len(patterns)} patterns, {len(keys)} keys")

    async def _invalidate_decision_cache(self, decision_id: str) -> None:
        """
        Invalidate caches related to a decision.

        Args:
            decision_id: Decision identifier
        """
        if not self.cache:
            return

        # Invalidate decision cache
        await self.cache.delete(CacheKeys.decision(decision_id))

        # Invalidate search caches (they may contain this decision)
        await self.cache.delete_pattern(CacheKeys.pattern_search())

        # Invalidate stats caches
        await self.cache.delete_pattern(CacheKeys.pattern_stats())

        logger.debug(f"Invalidated caches for decision: {decision_id}")
