#!/usr/bin/env python3
"""
Backfill metadata for existing content
Downloads content from Anthias and extracts metadata
"""

import sys
import os
import tempfile
import urllib.request
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.content import Content
from app.utils.media_metadata import MediaMetadataExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_file(url: str, output_path: str) -> bool:
    """Download file from URL"""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def backfill_content_metadata(db: Session, content_id: int = None):
    """
    Backfill metadata for content

    Args:
        db: Database session
        content_id: Specific content ID to backfill, or None for all
    """
    # Query content without metadata
    query = db.query(Content).filter(
        (Content.resolution == None) | (Content.resolution == "")
    )

    if content_id:
        query = query.filter(Content.id == content_id)

    contents = query.all()

    logger.info(f"Found {len(contents)} content items to backfill")

    for content in contents:
        logger.info(f"Processing content ID {content.id}: {content.title}")

        # Create temp file
        temp_dir = tempfile.mkdtemp()

        try:
            # Download file from Anthias
            file_ext = ""
            if content.mime_type:
                if "video" in content.mime_type:
                    file_ext = ".mp4"
                elif "image" in content.mime_type:
                    if "jpeg" in content.mime_type or "jpg" in content.mime_type:
                        file_ext = ".jpg"
                    elif "png" in content.mime_type:
                        file_ext = ".png"

            temp_file = os.path.join(temp_dir, f"content_{content.id}{file_ext}")

            logger.info(f"Downloading from {content.anthias_url}")
            if not download_file(content.anthias_url, temp_file):
                logger.error(f"Failed to download content {content.id}")
                continue

            # Extract metadata
            logger.info(f"Extracting metadata for {content.content_type}")
            metadata = MediaMetadataExtractor.extract_metadata(temp_file, content.content_type)

            if not metadata:
                logger.warning(f"No metadata extracted for content {content.id}")
                continue

            # Update database
            content.resolution = metadata.get("resolution")
            content.width = metadata.get("width")
            content.height = metadata.get("height")
            content.codec = metadata.get("codec")
            content.fps = metadata.get("fps")
            content.bitrate = metadata.get("bitrate")
            content.video_duration = metadata.get("duration")
            content.audio_codec = metadata.get("audio_codec")
            content.audio_bitrate = metadata.get("audio_bitrate")
            content.audio_sample_rate = metadata.get("audio_sample_rate")

            # Update file_size if not set
            if not content.file_size and metadata.get("file_size"):
                content.file_size = metadata.get("file_size")

            db.commit()
            logger.info(f"✓ Updated metadata for content {content.id}: {metadata.get('resolution', 'N/A')}")

        except Exception as e:
            logger.error(f"Error processing content {content.id}: {e}")
            db.rollback()
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                os.rmdir(temp_dir)
            except:
                pass


if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Check for specific content ID
        content_id = None
        if len(sys.argv) > 1:
            content_id = int(sys.argv[1])
            logger.info(f"Backfilling metadata for content ID: {content_id}")
        else:
            logger.info("Backfilling metadata for all content without metadata")

        backfill_content_metadata(db, content_id)
        logger.info("Backfill complete!")
    finally:
        db.close()
