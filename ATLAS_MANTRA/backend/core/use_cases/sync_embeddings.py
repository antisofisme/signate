"""
Sync Embeddings Use Case - Synchronize decision embeddings to vector store.

This use case syncs all decisions from the repository to the vector store,
generating embeddings as needed. Used for:
- Initial setup
- Rebuilding the index
- Adding new decisions

Usage:
    use_case = SyncEmbeddingsUseCase(vector_store, embedding, repository)
    result = await use_case.execute()
"""

import time
import logging
from dataclasses import dataclass
from typing import List, Optional

from core.ports.vector_store import VectorStoreProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.repositories.decision_repository import DecisionRepository
from core.domain.search_result import SyncResult
from core.domain.embedding import create_embedding_text, compute_text_hash

logger = logging.getLogger(__name__)


@dataclass
class SyncEmbeddingsInput:
    """Input for embedding sync."""
    batch_size: int = 50  # Decisions per batch
    force_rebuild: bool = False  # Force re-embed all
    group_id: Optional[str] = None  # Sync specific group only


class SyncEmbeddingsUseCase:
    """
    Synchronize decision embeddings to vector store.

    Workflow:
    1. Get all decisions from repository
    2. Check which need embedding (new or changed)
    3. Generate embeddings in batches
    4. Upsert to vector store
    """

    def __init__(
        self,
        vector_store: VectorStoreProtocol,
        embedding_service: EmbeddingProtocol,
        repository: DecisionRepository,
    ):
        self.vector_store = vector_store
        self.embedding = embedding_service
        self.repository = repository

    async def _ensure_collection(self) -> None:
        """Ensure vector collection exists."""
        if not await self.vector_store.collection_exists():
            await self.vector_store.create_collection(
                vector_size=self.embedding.dimensions
            )
            logger.info(f"Created collection with dimension {self.embedding.dimensions}")

    async def _get_existing_hashes(self, decision_ids: List[str]) -> dict[str, str]:
        """Get text hashes from existing vectors for staleness check."""
        hashes = {}
        for did in decision_ids:
            existing = await self.vector_store.get(did)
            if existing and existing.payload:
                hashes[did] = existing.payload.get("text_hash", "")
        return hashes

    async def execute(
        self,
        input: SyncEmbeddingsInput = None
    ) -> SyncResult:
        """
        Execute embedding sync.

        Args:
            input: Sync parameters (optional)

        Returns:
            SyncResult with sync statistics
        """
        input = input or SyncEmbeddingsInput()
        start_time = time.time()
        errors = []
        synced = 0
        skipped = 0
        failed = 0

        try:
            # 1. Ensure collection exists
            await self._ensure_collection()

            # 2. Get all decisions (StoredDecision objects)
            stored_decisions = self.repository.find_all()
            if input.group_id:
                stored_decisions = [
                    sd for sd in stored_decisions
                    if (sd.decision.group_id.value if hasattr(sd.decision.group_id, 'value') else str(sd.decision.group_id)) == input.group_id
                ]

            # Extract Decision objects for processing
            all_decisions = [sd.decision for sd in stored_decisions]

            total_decisions = len(all_decisions)
            logger.info(f"Starting sync for {total_decisions} decisions")

            if not all_decisions:
                return SyncResult(
                    synced_count=0,
                    skipped_count=0,
                    failed_count=0,
                    total_decisions=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # 3. Get existing hashes for staleness check
            decision_ids = [d.decision_id for d in all_decisions]
            existing_hashes = {}
            if not input.force_rebuild:
                existing_hashes = await self._get_existing_hashes(decision_ids)

            # 4. Process in batches
            for i in range(0, len(all_decisions), input.batch_size):
                batch = all_decisions[i:i + input.batch_size]
                texts_to_embed = []
                decisions_to_sync = []

                # Check which need embedding
                for decision in batch:
                    text = create_embedding_text(
                        statement=decision.statement,
                        rationale=decision.rationale,
                        tags=[t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
                    )
                    text_hash = compute_text_hash(text)

                    # Skip if hash matches (unchanged)
                    if not input.force_rebuild and existing_hashes.get(decision.decision_id) == text_hash:
                        skipped += 1
                        continue

                    texts_to_embed.append(text)
                    decisions_to_sync.append((decision, text_hash))

                if not texts_to_embed:
                    continue

                # Generate embeddings
                try:
                    vectors = await self.embedding.embed_batch(texts_to_embed)

                    # Prepare batch upsert
                    items = []
                    for idx, (decision, text_hash) in enumerate(decisions_to_sync):
                        payload = {
                            "decision_id": decision.decision_id,
                            "decision_code": decision.decision_code,
                            "statement": decision.statement,
                            "rationale": decision.rationale,
                            "group_id": decision.group_id.value if hasattr(decision.group_id, 'value') else str(decision.group_id),
                            "feature_id": decision.feature_id.value if hasattr(decision.feature_id, 'value') else str(decision.feature_id),
                            "version": decision.version,
                            "tags": [t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
                            "text_hash": text_hash,
                        }
                        items.append({
                            "id": decision.decision_id,
                            "vector": vectors[idx],
                            "payload": payload,
                        })

                    # Upsert batch
                    await self.vector_store.upsert_batch(items)
                    synced += len(items)
                    logger.debug(f"Synced batch of {len(items)} decisions")

                except Exception as e:
                    logger.error(f"Batch sync error: {e}")
                    failed += len(decisions_to_sync)
                    errors.append(str(e))

            result = SyncResult(
                synced_count=synced,
                skipped_count=skipped,
                failed_count=failed,
                total_decisions=total_decisions,
                execution_time_ms=(time.time() - start_time) * 1000,
                errors=errors,
            )

            logger.info(
                f"Sync completed: synced={synced}, skipped={skipped}, "
                f"failed={failed}, time={result.execution_time_ms:.1f}ms"
            )
            return result

        except Exception as e:
            logger.error(f"Sync error: {e}")
            return SyncResult(
                synced_count=synced,
                skipped_count=skipped,
                failed_count=failed,
                total_decisions=len(all_decisions) if 'all_decisions' in locals() else 0,
                execution_time_ms=(time.time() - start_time) * 1000,
                errors=[str(e)],
            )


async def sync_embeddings(
    vector_store: VectorStoreProtocol,
    embedding_service: EmbeddingProtocol,
    repository: DecisionRepository,
    batch_size: int = 50,
    force_rebuild: bool = False,
    group_id: Optional[str] = None,
) -> SyncResult:
    """
    Convenience function for embedding sync.

    Args:
        vector_store: Vector store implementation
        embedding_service: Embedding service implementation
        repository: Decision repository
        batch_size: Decisions per batch
        force_rebuild: Force re-embed all
        group_id: Sync specific group only

    Returns:
        SyncResult
    """
    use_case = SyncEmbeddingsUseCase(
        vector_store=vector_store,
        embedding_service=embedding_service,
        repository=repository,
    )
    return await use_case.execute(SyncEmbeddingsInput(
        batch_size=batch_size,
        force_rebuild=force_rebuild,
        group_id=group_id,
    ))


async def sync_single_decision(
    decision_id: str,
    vector_store: VectorStoreProtocol,
    embedding_service: EmbeddingProtocol,
    repository: DecisionRepository,
) -> bool:
    """
    Sync a single decision's embedding.

    Useful after storing a new decision.

    Args:
        decision_id: Decision ID to sync
        vector_store: Vector store implementation
        embedding_service: Embedding service implementation
        repository: Decision repository

    Returns:
        True if synced successfully
    """
    try:
        stored = repository.find_by_id(decision_id)
        if not stored:
            logger.warning(f"Decision not found for sync: {decision_id}")
            return False

        # Extract Decision from StoredDecision
        decision = stored.decision

        # Create embedding text
        text = create_embedding_text(
            statement=decision.statement,
            rationale=decision.rationale,
            tags=[t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
        )
        text_hash = compute_text_hash(text)

        # Generate embedding
        vector = await embedding_service.embed(text)

        # Build payload
        payload = {
            "decision_id": decision.decision_id,
            "decision_code": decision.decision_code,
            "statement": decision.statement,
            "rationale": decision.rationale,
            "group_id": decision.group_id.value if hasattr(decision.group_id, 'value') else str(decision.group_id),
            "feature_id": decision.feature_id.value if hasattr(decision.feature_id, 'value') else str(decision.feature_id),
            "version": decision.version,
            "tags": [t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
            "text_hash": text_hash,
        }

        # Upsert
        await vector_store.upsert(
            id=decision_id,
            vector=vector,
            payload=payload,
        )

        logger.info(f"Synced single decision: {decision_id}")
        return True

    except Exception as e:
        logger.error(f"Single decision sync error for {decision_id}: {e}")
        return False
