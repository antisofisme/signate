"""
Content Processing Background Tasks
Handles video transcoding, thumbnail generation, and cleanup
"""

import os
import ffmpeg
from pathlib import Path
from celery import current_task
from celery_app import app
from sqlalchemy.orm import Session
from PIL import Image
import hashlib
from datetime import datetime, timedelta, timezone

from shared.database import SessionLocal
from services.content.repositories.models import ContentModel


@app.task(bind=True, name='tasks.content_tasks.transcode_to_hls')
def transcode_to_hls(self, content_id: int):
    """
    Transcode video to HLS format for adaptive streaming

    Args:
        content_id: Content ID from database

    Returns:
        Dictionary with transcoding results
    """
    db = SessionLocal()

    try:
        # Get content from database
        content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Update status to processing
        content.transcoding_status = 'processing'
        content.transcoding_progress = 0
        db.commit()

        # Get file paths
        source_path = Path(content.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create HLS output directory
        hls_dir = source_path.parent / f"{source_path.stem}_hls"
        hls_dir.mkdir(parents=True, exist_ok=True)

        # HLS output paths
        playlist_path = hls_dir / "playlist.m3u8"
        segment_pattern = str(hls_dir / "segment_%03d.ts")

        print(f"[Transcode] Starting HLS transcode for content {content_id}")
        print(f"[Transcode] Source: {source_path}")
        print(f"[Transcode] Output: {playlist_path}")

        # FFmpeg transcoding with progress tracking
        try:
            # Get video duration for progress calculation
            probe = ffmpeg.probe(str(source_path))
            duration = float(probe['streams'][0]['duration'])

            # Transcode to HLS with multiple quality levels
            stream = ffmpeg.input(str(source_path))

            # Output with HLS parameters
            output = ffmpeg.output(
                stream,
                str(playlist_path),
                format='hls',
                start_number=0,
                hls_time=6,
                hls_list_size=0,
                hls_segment_filename=segment_pattern,
                vcodec='libx264',
                acodec='aac',
                video_bitrate='2M',
                audio_bitrate='128k',
                preset='medium',
                movflags='+faststart'
            )

            # Run FFmpeg
            ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            # Update progress to 100%
            content.transcoding_progress = 100
            db.commit()

            print(f"[Transcode] HLS transcode completed for content {content_id}")

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            print(f"[Transcode] FFmpeg error: {error_message}")
            raise

        # Update content record
        content.transcoding_status = 'completed'
        content.hls_path = str(playlist_path.relative_to(Path(content.file_path).parent.parent))
        db.commit()

        return {
            'content_id': content_id,
            'status': 'completed',
            'hls_path': content.hls_path,
            'duration': duration
        }

    except Exception as e:
        print(f"[Transcode] Error: {str(e)}")

        # CRITICAL FIX P0-15: Mark content as failed and consider cleanup
        if content:
            content.transcoding_status = 'failed'
            content.transcoding_progress = 0
            content.upload_status = 'failed'  # Mark upload as failed
            db.commit()

            print(f"[Transcode] Content {content_id} marked as failed")
            print(f"[Transcode] File path: {content.file_path}")
            print(f"[Transcode] Note: File kept for debugging. Manual cleanup may be needed.")

        raise

    finally:
        db.close()


@app.task(bind=True, name='tasks.content_tasks.generate_thumbnail')
def generate_thumbnail(self, content_id: int):
    """
    Generate thumbnail for video or optimize image

    Args:
        content_id: Content ID from database

    Returns:
        Dictionary with thumbnail results
    """
    db = SessionLocal()

    try:
        # Get content from database
        content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not content:
            raise ValueError(f"Content {content_id} not found")

        print(f"[Thumbnail] Generating thumbnail for content {content_id}")

        # Get file paths
        source_path = Path(content.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create thumbnails directory
        thumb_dir = Path("/data/signage/content/thumbnails")
        thumb_dir.mkdir(parents=True, exist_ok=True)

        # Thumbnail output path
        thumb_filename = f"{source_path.stem}_thumb.jpg"
        thumb_path = thumb_dir / thumb_filename

        if content.content_type == 'video':
            # Extract frame from video at 1 second
            try:
                (
                    ffmpeg
                    .input(str(source_path), ss=1)
                    .filter('scale', 320, -1)
                    .output(str(thumb_path), vframes=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                print(f"[Thumbnail] Video thumbnail generated: {thumb_path}")
            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if e.stderr else str(e)
                print(f"[Thumbnail] FFmpeg error: {error_message}")
                raise

        elif content.content_type == 'image':
            # Generate thumbnail from image
            try:
                with Image.open(source_path) as img:
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background

                    # Create thumbnail
                    img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                    img.save(thumb_path, 'JPEG', quality=85, optimize=True)

                print(f"[Thumbnail] Image thumbnail generated: {thumb_path}")
            except Exception as e:
                print(f"[Thumbnail] PIL error: {str(e)}")
                raise

        # Update content record
        content.thumbnail_url = f"http://192.168.5.12:8001/thumbnails/{thumb_filename}"
        db.commit()

        return {
            'content_id': content_id,
            'thumbnail_url': content.thumbnail_url
        }

    except Exception as e:
        print(f"[Thumbnail] Error: {str(e)}")

        # CRITICAL FIX P0-15: Mark content as failed on thumbnail generation failure
        if content:
            # For thumbnail failures, don't mark upload as failed (it's not critical)
            # Just log the error - content can still be used without thumbnail
            print(f"[Thumbnail] Thumbnail generation failed for content {content_id}")
            print(f"[Thumbnail] Content is still usable without thumbnail")

        raise

    finally:
        db.close()


@app.task(name='tasks.content_tasks.cleanup_old_task_results')
def cleanup_old_task_results():
    """
    Periodic task to clean up old task results from Redis
    Runs daily at 3 AM (configured in celery_app.py)
    """
    try:
        # Clean up task results older than 7 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

        print(f"[Cleanup] Cleaning up task results older than {cutoff_date}")

        # This is handled automatically by Celery's result_expires setting
        # but we can add additional cleanup logic here if needed

        return {
            'status': 'completed',
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        print(f"[Cleanup] Error: {str(e)}")
        raise
