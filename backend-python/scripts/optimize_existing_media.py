#!/usr/bin/env python3
"""
Batch optimize existing menu media images.
Generates WebP variants for all images that don't have variants yet.

Usage:
    python scripts/optimize_existing_media.py
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from shared.config import settings
from services.menu.image_optimizer import get_image_optimizer

def main():
    print("=" * 60)
    print("Menu Media Batch Optimization")
    print("=" * 60)

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get all media without variants
    result = session.execute(text("""
        SELECT id, organization_id, file_path, original_filename, file_size
        FROM menu_media
        WHERE deleted_at IS NULL
          AND (variants IS NULL OR variants = '{}')
        ORDER BY id
    """))

    media_list = result.fetchall()
    total = len(media_list)

    print(f"\nFound {total} images to optimize\n")

    if total == 0:
        print("All images are already optimized!")
        return

    # Initialize optimizer
    optimizer = get_image_optimizer()

    success_count = 0
    failed_count = 0

    for idx, media in enumerate(media_list, 1):
        media_id = media.id
        org_id = media.organization_id
        file_path = media.file_path
        filename = media.original_filename

        print(f"[{idx}/{total}] Processing: {filename} (ID: {media_id})")

        # Build full path
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)

        if not os.path.exists(full_path):
            print(f"  ⚠ File not found: {full_path}")
            failed_count += 1

            # Mark as failed in database
            session.execute(text("""
                UPDATE menu_media
                SET processing_status = 'failed',
                    updated_at = NOW()
                WHERE id = :media_id
            """), {"media_id": media_id})
            session.commit()
            continue

        try:
            # Optimize image
            result = optimizer.optimize_image(
                media_id=media_id,
                organization_id=org_id,
                source_path=full_path
            )

            if result.get("processing_status") == "completed":
                # Update database
                session.execute(text("""
                    UPDATE menu_media
                    SET variants = :variants,
                        content_hash = :content_hash,
                        original_width = :original_width,
                        original_height = :original_height,
                        is_animated = :is_animated,
                        processing_status = 'completed',
                        optimized_at = NOW(),
                        updated_at = NOW()
                    WHERE id = :media_id
                """), {
                    "media_id": media_id,
                    "variants": json.dumps(result.get("variants")) if result.get("variants") else None,
                    "content_hash": result.get("content_hash"),
                    "original_width": result.get("original_width"),
                    "original_height": result.get("original_height"),
                    "is_animated": result.get("is_animated", False)
                })
                session.commit()

                print(f"  ✓ Optimized: {result.get('original_width')}x{result.get('original_height')}")
                success_count += 1
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                failed_count += 1

                session.execute(text("""
                    UPDATE menu_media
                    SET processing_status = 'failed',
                        updated_at = NOW()
                    WHERE id = :media_id
                """), {"media_id": media_id})
                session.commit()

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed_count += 1

            session.execute(text("""
                UPDATE menu_media
                SET processing_status = 'failed',
                    updated_at = NOW()
                WHERE id = :media_id
            """), {"media_id": media_id})
            session.commit()

    session.close()

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print("=" * 60)
    print(f"  Total:   {total}")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {failed_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
