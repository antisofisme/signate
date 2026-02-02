"""
Migrate Decisions to Meilisearch

This script indexes all existing decisions from the PostgreSQL database
to Meilisearch for full-text search.

Usage:
    # Index all decisions
    python -m scripts.migrate_to_meilisearch

    # Index with specific batch size
    python -m scripts.migrate_to_meilisearch --batch-size 100

    # Dry run (show what would be indexed)
    python -m scripts.migrate_to_meilisearch --dry-run

    # Clear index before migration
    python -m scripts.migrate_to_meilisearch --clear
"""

import argparse
import asyncio
import logging
import sys
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_all_decisions() -> List:
    """Get all decisions from repository."""
    from factory.container import Container

    await Container.initialize_repository()
    repository = Container.get_decision_repository()

    # Get all decisions
    decisions = repository.list_all()
    logger.info(f"Found {len(decisions)} decisions in repository")

    return decisions


def decision_to_document(decision) -> Dict[str, Any]:
    """Convert a decision to a Meilisearch document."""
    return {
        "id": decision.id,
        "decision_code": decision.decision_code,
        "statement": decision.statement,
        "rationale": decision.rationale or "",
        "domain_id": str(decision.domain_id.value) if hasattr(decision.domain_id, 'value') else str(decision.domain_id),
        "feature_id": str(decision.feature_id) if decision.feature_id else "",
        "aspect_id": str(decision.aspect_id.value) if hasattr(decision.aspect_id, 'value') else str(decision.aspect_id),
        "tags": [str(t.value) if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
        "status": decision.status.value if hasattr(decision.status, 'value') else str(decision.status),
        "version": decision.version or "1.0.0",
        "created_at": decision.created_at.isoformat() if decision.created_at else "",
        "updated_at": decision.updated_at.isoformat() if decision.updated_at else "",
    }


async def migrate_decisions(
    batch_size: int = 50,
    dry_run: bool = False,
    clear_first: bool = False,
) -> dict:
    """
    Migrate all decisions to Meilisearch.

    Args:
        batch_size: Number of decisions per batch
        dry_run: If True, show what would be indexed without actually indexing
        clear_first: If True, clear the index before migration

    Returns:
        Migration statistics
    """
    from factory.container import Container
    from core.runtime.config import get_config

    config = get_config()

    # Check if Meilisearch is enabled
    if not config.feature_meilisearch_enabled:
        logger.error("Meilisearch is disabled. Enable with FEATURE_MEILISEARCH_ENABLED=true")
        return {"error": "Meilisearch disabled"}

    # Get text search adapter
    text_search = Container.get_text_search()
    if not text_search:
        logger.error("Failed to get text search adapter")
        return {"error": "Text search not available"}

    # Check health
    if not await text_search.health_check():
        logger.error("Meilisearch is not healthy. Check connection settings.")
        return {"error": "Meilisearch not healthy"}

    stats = {
        "total_decisions": 0,
        "indexed_count": 0,
        "failed_count": 0,
        "batches_processed": 0,
    }

    # Get all decisions
    decisions = await get_all_decisions()
    stats["total_decisions"] = len(decisions)

    if not decisions:
        logger.warning("No decisions found to migrate")
        return stats

    # Convert to documents
    documents = []
    for d in decisions:
        try:
            doc = decision_to_document(d)
            documents.append(doc)
        except Exception as e:
            logger.warning(f"Failed to convert decision {d.id}: {e}")
            stats["failed_count"] += 1

    logger.info(f"Converted {len(documents)} decisions to documents")

    if dry_run:
        logger.info("DRY RUN - Would index the following:")
        for doc in documents[:5]:
            logger.info(f"  - {doc['decision_code']}: {doc['statement'][:50]}...")
        if len(documents) > 5:
            logger.info(f"  ... and {len(documents) - 5} more")
        return stats

    # Clear index if requested
    if clear_first:
        logger.info("Clearing existing index...")
        await text_search.clear()

    # Index in batches
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(documents) + batch_size - 1) // batch_size

        logger.info(f"Indexing batch {batch_num}/{total_batches} ({len(batch)} documents)...")

        try:
            count = await text_search.index(batch)
            stats["indexed_count"] += count
            stats["batches_processed"] += 1
        except Exception as e:
            logger.error(f"Failed to index batch {batch_num}: {e}")
            stats["failed_count"] += len(batch)

    logger.info(f"Migration complete: {stats['indexed_count']} indexed, {stats['failed_count']} failed")
    return stats


async def verify_migration() -> dict:
    """Verify the migration by checking index stats."""
    from factory.container import Container

    text_search = Container.get_text_search()
    if not text_search:
        return {"error": "Text search not available"}

    stats = await text_search.get_stats()

    logger.info(f"Index stats:")
    logger.info(f"  Index name: {stats.index_name}")
    logger.info(f"  Document count: {stats.document_count}")
    logger.info(f"  Last update: {stats.last_update}")

    return {
        "index_name": stats.index_name,
        "document_count": stats.document_count,
        "field_distribution": stats.field_distribution,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate decisions to Meilisearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=50,
        help="Number of decisions per batch (default: 50)"
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be indexed without actually indexing"
    )

    parser.add_argument(
        "--clear",
        "-c",
        action="store_true",
        help="Clear the index before migration"
    )

    parser.add_argument(
        "--verify",
        "-v",
        action="store_true",
        help="Verify migration after completion"
    )

    return parser.parse_args()


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    logger.info("Starting Meilisearch migration...")
    logger.info(f"  Batch size: {args.batch_size}")
    logger.info(f"  Dry run: {args.dry_run}")
    logger.info(f"  Clear first: {args.clear}")

    try:
        stats = await migrate_decisions(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            clear_first=args.clear,
        )

        if "error" in stats:
            logger.error(f"Migration failed: {stats['error']}")
            sys.exit(1)

        if args.verify and not args.dry_run:
            logger.info("\nVerifying migration...")
            await verify_migration()

        logger.info("\nMigration summary:")
        logger.info(f"  Total decisions: {stats['total_decisions']}")
        logger.info(f"  Indexed: {stats['indexed_count']}")
        logger.info(f"  Failed: {stats['failed_count']}")
        logger.info(f"  Batches: {stats['batches_processed']}")

    finally:
        from factory.container import Container
        await Container.close_all()


if __name__ == "__main__":
    asyncio.run(main())
