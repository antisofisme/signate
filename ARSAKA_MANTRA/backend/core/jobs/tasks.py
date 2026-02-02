"""
Celery Task Definitions

Background tasks for MANTRA:
- Embedding computation
- Document generation
- Export synchronization
- Analytics aggregation
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


# ============================================================================
# Embedding Tasks
# ============================================================================


@shared_task(
    bind=True,
    name="core.jobs.tasks.compute_embeddings_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def compute_embeddings_task(
    self,
    decision_ids: list[str],
    force_recompute: bool = False,
) -> dict[str, Any]:
    """
    Compute embeddings for decisions.

    Args:
        decision_ids: List of decision IDs to compute embeddings for
        force_recompute: If True, recompute even if embeddings exist

    Returns:
        Result with success count and any errors
    """
    try:
        logger.info(f"Computing embeddings for {len(decision_ids)} decisions")

        # Import here to avoid circular imports
        from factory.container import Container
        import asyncio

        async def _compute():
            embedding_service = Container.get_embedding()
            vector_store = Container.get_vector_store()
            repository = Container.get_decision_repository()

            computed = 0
            errors = []

            for decision_id in decision_ids:
                try:
                    # Get decision
                    result = await repository.get_by_id(decision_id)
                    if not result.decision:
                        errors.append(f"{decision_id}: not found")
                        continue

                    decision = result.decision

                    # Check if embedding exists (unless force recompute)
                    if not force_recompute:
                        existing = await vector_store.get_by_id(decision_id)
                        if existing:
                            continue

                    # Create text for embedding
                    text = f"{decision.code}: {decision.statement}\n\n{decision.rationale}"
                    if decision.scope:
                        text += f"\n\nScope: {', '.join(decision.scope)}"

                    # Compute embedding
                    embedding = await embedding_service.embed(text)

                    # Store in vector store
                    await vector_store.upsert(
                        id=decision_id,
                        vector=embedding,
                        metadata={
                            "code": decision.code,
                            "domain_id": decision.domain_id,
                            "aspect_id": decision.aspect_id,
                        },
                    )

                    computed += 1

                except Exception as e:
                    errors.append(f"{decision_id}: {str(e)}")

            return {"computed": computed, "errors": errors}

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_compute())
        finally:
            loop.close()

        logger.info(f"Computed {result['computed']} embeddings, {len(result['errors'])} errors")
        return {
            "success": True,
            "computed": result["computed"],
            "errors": result["errors"],
            "total_requested": len(decision_ids),
        }

    except SoftTimeLimitExceeded:
        logger.warning("Embedding computation soft time limit exceeded")
        raise

    except Exception as e:
        logger.error(f"Embedding computation failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="core.jobs.tasks.reindex_decisions_task",
    max_retries=3,
)
def reindex_decisions_task(self) -> dict[str, Any]:
    """
    Reindex all decisions in vector store.

    This is a heavy operation - use sparingly.
    """
    try:
        logger.info("Starting full decision reindex")

        from factory.container import Container
        import asyncio

        async def _reindex():
            repository = Container.get_decision_repository()
            embedding_service = Container.get_embedding()
            vector_store = Container.get_vector_store()

            # Get all decisions
            result = await repository.list_decisions(limit=10000)
            decisions = result.decisions

            reindexed = 0
            errors = []

            for decision in decisions:
                try:
                    text = f"{decision.code}: {decision.statement}\n\n{decision.rationale}"
                    embedding = await embedding_service.embed(text)

                    await vector_store.upsert(
                        id=str(decision.id),
                        vector=embedding,
                        metadata={
                            "code": decision.code,
                            "domain_id": decision.domain_id,
                            "aspect_id": decision.aspect_id,
                        },
                    )
                    reindexed += 1

                except Exception as e:
                    errors.append(f"{decision.code}: {str(e)}")

            return {"reindexed": reindexed, "errors": errors}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_reindex())
        finally:
            loop.close()

        logger.info(f"Reindexed {result['reindexed']} decisions")
        return {
            "success": True,
            "reindexed": result["reindexed"],
            "errors": result["errors"],
        }

    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise self.retry(exc=e)


# ============================================================================
# Document Generation Tasks
# ============================================================================


@shared_task(
    bind=True,
    name="core.jobs.tasks.generate_document_task",
    max_retries=2,
)
def generate_document_task(
    self,
    doc_type: str,
    title: Optional[str] = None,
    domain_filter: Optional[str] = None,
    scope_filter: Optional[str] = None,
    max_decisions: int = 100,
    notify_email: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generate a document in the background.

    Args:
        doc_type: Document type to generate
        title: Optional custom title
        domain_filter: Optional domain filter
        scope_filter: Optional scope filter
        max_decisions: Maximum decisions to include
        notify_email: Email to notify when complete

    Returns:
        Generated document info
    """
    try:
        logger.info(f"Generating document: {doc_type}")

        from core.docs.generator import DocumentGenerator
        from core.docs.types import DocumentType

        generator = DocumentGenerator()
        document = generator.generate(
            doc_type=DocumentType(doc_type),
            decisions=[],  # Will fetch based on filters
            title=title,
            domain_filter=domain_filter,
            scope_filter=scope_filter,
            max_decisions=max_decisions,
        )

        # TODO: Store document or notify user
        result = {
            "success": True,
            "title": document.title,
            "doc_type": doc_type,
            "word_count": document.word_count,
            "decision_count": document.decision_count,
            "generated_at": document.generated_at.isoformat(),
        }

        if notify_email:
            # TODO: Send email notification
            logger.info(f"Would notify {notify_email} of document generation")

        logger.info(f"Generated document: {document.title}")
        return result

    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        raise self.retry(exc=e)


# ============================================================================
# Export Tasks
# ============================================================================


@shared_task(
    bind=True,
    name="core.jobs.tasks.export_document_task",
    max_retries=3,
    default_retry_delay=120,
)
def export_document_task(
    self,
    content: str,
    title: str,
    target: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Export a document to an external platform.

    Args:
        content: Markdown content to export
        title: Document title
        target: Export target (confluence, notion, github_wiki)
        config: Export configuration

    Returns:
        Export result with URL if successful
    """
    try:
        logger.info(f"Exporting document to {target}: {title}")

        from core.export import (
            ExportConfig,
            ExportTarget,
            ConfluenceExporter,
            NotionExporter,
            GitHubWikiExporter,
        )
        import asyncio

        # Build config
        export_config = ExportConfig(
            target=ExportTarget(target),
            api_key=config.get("api_key"),
            api_token=config.get("api_token"),
            space_key=config.get("space_key"),
            parent_page_id=config.get("parent_page_id"),
            database_id=config.get("database_id"),
            repo_owner=config.get("repo_owner"),
            repo_name=config.get("repo_name"),
            extra=config.get("extra", {}),
        )

        # Get exporter
        exporters = {
            "confluence": ConfluenceExporter,
            "notion": NotionExporter,
            "github_wiki": GitHubWikiExporter,
        }
        exporter = exporters[target]()

        async def _export():
            return await exporter.export_document(content, title, export_config)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_export())
        finally:
            loop.close()

        logger.info(f"Export result: success={result.success}, url={result.url}")
        return {
            "success": result.success,
            "target": target,
            "url": result.url,
            "page_id": result.page_id,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="core.jobs.tasks.sync_export_task",
)
def sync_export_task(self) -> dict[str, Any]:
    """
    Synchronize all configured exports.

    This is a periodic task that checks for changes and updates
    exported documents accordingly.
    """
    try:
        logger.info("Starting export synchronization")

        # TODO: Implement export sync logic
        # 1. Get list of exported documents from database
        # 2. Check if source decisions have changed
        # 3. Re-export documents that need updating

        return {
            "success": True,
            "synced": 0,
            "errors": [],
        }

    except Exception as e:
        logger.error(f"Export sync failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================================
# Analytics Tasks
# ============================================================================


@shared_task(
    bind=True,
    name="core.jobs.tasks.aggregate_analytics_task",
)
def aggregate_analytics_task(self) -> dict[str, Any]:
    """
    Aggregate analytics data.

    This is a periodic task that:
    - Aggregates hourly metrics
    - Updates health scores
    - Identifies hot/stale/problematic decisions
    """
    try:
        logger.info("Starting analytics aggregation")

        from factory.container import Container
        import asyncio

        async def _aggregate():
            analytics_tracker = Container.get_analytics_tracker()

            if not analytics_tracker:
                return {"aggregated": False, "reason": "Analytics tracker not available"}

            # Get summary for health calculation
            summary = analytics_tracker.get_summary()

            # Update decision health based on usage
            updated_count = 0

            # Get hot decisions
            hot_decisions = analytics_tracker.get_hot_decisions(limit=50)

            # Get stale decisions (no access in 30 days)
            stale_decisions = analytics_tracker.get_stale_decisions(days=30)

            # Get problematic decisions
            problematic = analytics_tracker.get_problematic_decisions()

            return {
                "aggregated": True,
                "hot_count": len(hot_decisions),
                "stale_count": len(stale_decisions),
                "problematic_count": len(problematic),
                "total_events": summary.total_events,
            }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_aggregate())
        finally:
            loop.close()

        logger.info(f"Analytics aggregation complete: {result}")
        return {
            "success": True,
            **result,
        }

    except Exception as e:
        logger.error(f"Analytics aggregation failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
