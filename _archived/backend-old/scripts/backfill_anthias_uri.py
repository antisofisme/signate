#!/usr/bin/env python3
"""
Backfill anthias_file_uri for existing content
Phase 2 - Metadata Refactor: Populate cached URI field

This script:
1. Finds all content with NULL anthias_file_uri
2. Calls Anthias API to get the URI for each asset
3. Updates the database with cached URI
4. Logs progress and errors
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.content import Content
from app.services.anthias_service import AnthiasService
from app.core.config import settings
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


async def backfill_uri_cache():
    """Backfill anthias_file_uri for existing content"""
    db = SessionLocal()
    anthias_service = AnthiasService()

    try:
        # Get all content with NULL anthias_file_uri
        contents = db.query(Content).filter(
            Content.anthias_file_uri.is_(None),
            Content.anthias_asset_id.isnot(None)
        ).all()

        total_count = len(contents)
        success_count = 0
        error_count = 0

        logger.info(
            f"Starting backfill for {total_count} content records",
            total_count=total_count
        )
        print(f"\n{'='*80}")
        print(f"BACKFILLING ANTHIAS_FILE_URI FOR {total_count} CONTENT RECORDS")
        print(f"{'='*80}\n")

        for idx, content in enumerate(contents, 1):
            try:
                print(f"[{idx}/{total_count}] Processing content ID {content.id}: {content.title}")

                # Fetch asset details from Anthias
                asset = await anthias_service.get_asset(content.anthias_asset_id)
                uri = asset.get('uri')

                if uri:
                    content.anthias_file_uri = uri
                    db.commit()
                    success_count += 1

                    logger.info(
                        f"Backfilled URI for content {content.id}",
                        content_id=content.id,
                        title=content.title,
                        uri=uri
                    )
                    print(f"  ✓ SUCCESS: {uri}")
                else:
                    error_count += 1
                    logger.warning(
                        f"No URI found for content {content.id}",
                        content_id=content.id,
                        anthias_asset_id=content.anthias_asset_id
                    )
                    print(f"  ✗ WARNING: No URI found in Anthias response")

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error backfilling content {content.id}",
                    content_id=content.id,
                    error=str(e),
                    exc_info=True
                )
                print(f"  ✗ ERROR: {e}")

        print(f"\n{'='*80}")
        print(f"BACKFILL COMPLETED")
        print(f"{'='*80}")
        print(f"Total processed: {total_count}")
        print(f"Successful:      {success_count} ({success_count/total_count*100:.1f}%)" if total_count > 0 else "Successful:      0 (0.0%)")
        print(f"Errors:          {error_count} ({error_count/total_count*100:.1f}%)" if total_count > 0 else "Errors:          0 (0.0%)")
        print(f"{'='*80}\n")

        logger.info(
            "Backfill completed",
            total_count=total_count,
            success_count=success_count,
            error_count=error_count
        )

    except Exception as e:
        logger.error(
            "Fatal error during backfill",
            error=str(e),
            exc_info=True
        )
        print(f"\n✗ FATAL ERROR: {e}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"\nAnthias API URL: {settings.ANTHIAS_API_URL}")
    print(f"Database: {settings.DATABASE_URL}\n")

    # Run backfill
    asyncio.run(backfill_uri_cache())
