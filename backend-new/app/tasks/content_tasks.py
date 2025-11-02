"""
Content Processing Background Tasks
====================================

Celery tasks untuk video transcoding, image optimization,
dan content processing lainnya.

Dependencies:
- FFmpeg for video transcoding
- Pillow for image optimization
"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from celery import Task
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.repositories import ContentRepository
from app.utils.activity_logger import log_activity, ActivityAction, EntityType

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.content_tasks.process_video_upload",
    queue="transcoding"
)
def process_video_upload(
    self: Task,
    content_id: int,
    source_file_path: str,
    organization_id: int
) -> Dict[str, Any]:
    """
    Process uploaded video - extract metadata and trigger transcoding.

    Flow:
    1. Extract video metadata (duration, resolution, codec)
    2. Generate thumbnail
    3. Update content record
    4. Trigger transcoding task (async)

    Args:
        content_id: Content ID
        source_file_path: Path to uploaded video file
        organization_id: Organization ID

    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    try:
        logger.info(f"Processing video upload for content {content_id}...")

        content_repo = ContentRepository(db)
        content = content_repo.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            return {
                "status": "error",
                "message": f"Content {content_id} not found",
                "task_id": self.request.id
            }

        # Extract video metadata using FFprobe
        metadata = _extract_video_metadata(source_file_path)

        # Update content with metadata
        update_data = {
            "video_duration": metadata.get("duration"),
            "resolution": metadata.get("resolution"),
            "width": metadata.get("width"),
            "height": metadata.get("height"),
            "codec": metadata.get("video_codec"),
            "fps": metadata.get("fps"),
            "bitrate": metadata.get("bitrate"),
            "audio_codec": metadata.get("audio_codec"),
            "audio_bitrate": metadata.get("audio_bitrate"),
            "audio_sample_rate": metadata.get("audio_sample_rate"),
            "transcoding_status": "pending"
        }

        content_repo.update(content_id, update_data)

        # Generate thumbnail
        thumbnail_path = _generate_thumbnail(source_file_path, content_id)
        if thumbnail_path:
            content_repo.update(content_id, {"thumbnail_url": thumbnail_path})

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.CREATE,
            entity_type=EntityType.CONTENT,
            entity_id=content_id,
            organization_id=organization_id,
            description=f"Video uploaded and processing started: {content.title}",
            metadata={"metadata": metadata, "thumbnail": thumbnail_path}
        )

        logger.info(f"Video processing completed for content {content_id}")

        # Trigger transcoding task (async)
        transcode_video.delay(content_id, source_file_path)

        return {
            "status": "success",
            "content_id": content_id,
            "metadata": metadata,
            "thumbnail": thumbnail_path,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error processing video upload {content_id}: {str(e)}")
        db.rollback()
        
        # Update content status to failed
        try:
            content_repo = ContentRepository(db)
            content_repo.update(content_id, {
                "transcoding_status": "failed",
                "transcoding_error": str(e)
            })
        except:
            pass

        raise self.retry(exc=e, countdown=60, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.content_tasks.transcode_video",
    queue="transcoding",
    time_limit=1800  # 30 minutes
)
def transcode_video(
    self: Task,
    content_id: int,
    source_file_path: str,
    target_resolutions: list = None
) -> Dict[str, Any]:
    """
    Transcode video to multiple resolutions using FFmpeg.

    Creates HLS (HTTP Live Streaming) variants:
    - 1080p (1920x1080) @ 5000kbps
    - 720p (1280x720) @ 2500kbps
    - 480p (854x480) @ 1000kbps

    Args:
        content_id: Content ID
        source_file_path: Path to source video
        target_resolutions: List of target resolutions (default: [1080p, 720p, 480p])

    Returns:
        Dict with transcoding results
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting video transcoding for content {content_id}...")

        content_repo = ContentRepository(db)
        content = content_repo.get(content_id)

        if not content:
            logger.error(f"Content {content_id} not found")
            return {
                "status": "error",
                "message": f"Content {content_id} not found"
            }

        # Update status to processing
        content_repo.update(content_id, {
            "transcoding_status": "processing",
            "transcoding_job_id": self.request.id,
            "transcoding_progress": 0
        })

        # Default resolutions if not specified
        if not target_resolutions:
            target_resolutions = [
                {"name": "1080p", "width": 1920, "height": 1080, "bitrate": "5000k"},
                {"name": "720p", "width": 1280, "height": 720, "bitrate": "2500k"},
                {"name": "480p", "width": 854, "height": 480, "bitrate": "1000k"},
            ]

        # Create output directory
        output_dir = Path(source_file_path).parent / f"transcoded_{content_id}"
        output_dir.mkdir(exist_ok=True)

        # Transcode to HLS variants
        variants = []
        for resolution in target_resolutions:
            variant_path = output_dir / f"{resolution['name']}.m3u8"
            
            # FFmpeg transcoding command
            cmd = [
                "ffmpeg",
                "-i", source_file_path,
                "-vf", f"scale={resolution['width']}:{resolution['height']}",
                "-c:v", "libx264",
                "-b:v", resolution["bitrate"],
                "-c:a", "aac",
                "-b:a", "128k",
                "-hls_time", "10",
                "-hls_list_size", "0",
                "-f", "hls",
                str(variant_path)
            ]

            # Execute FFmpeg
            logger.info(f"Transcoding {resolution['name']} variant...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg error for {resolution['name']}: {result.stderr}")
                continue

            variants.append({
                "resolution": resolution["name"],
                "playlist": str(variant_path),
                "bitrate": resolution["bitrate"]
            })

            # Update progress
            progress = int((len(variants) / len(target_resolutions)) * 100)
            content_repo.update(content_id, {"transcoding_progress": progress})

        # Create master playlist
        master_playlist_path = output_dir / "master.m3u8"
        _create_master_playlist(master_playlist_path, variants)

        # Update content record
        content_repo.update(content_id, {
            "transcoding_status": "completed",
            "transcoding_progress": 100,
            "hls_master_playlist_path": str(master_playlist_path),
            "hls_variants": variants
        })

        # Log activity
        log_activity(
            db=db,
            action=ActivityAction.UPDATE,
            entity_type=EntityType.CONTENT,
            entity_id=content_id,
            organization_id=content.organization_id,
            description=f"Video transcoding completed: {content.title}",
            metadata={"variants": len(variants), "master_playlist": str(master_playlist_path)}
        )

        logger.info(f"Video transcoding completed for content {content_id}")

        return {
            "status": "success",
            "content_id": content_id,
            "variants": variants,
            "master_playlist": str(master_playlist_path),
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error transcoding video {content_id}: {str(e)}")
        db.rollback()

        # Update status to failed
        try:
            content_repo = ContentRepository(db)
            content_repo.update(content_id, {
                "transcoding_status": "failed",
                "transcoding_error": str(e)
            })
        except:
            pass

        raise self.retry(exc=e, countdown=120, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.content_tasks.generate_video_thumbnail",
    queue="default"
)
def generate_video_thumbnail(
    self: Task,
    content_id: int,
    source_file_path: str,
    timestamp: float = 1.0
) -> Dict[str, Any]:
    """
    Generate thumbnail from video at specific timestamp.

    Args:
        content_id: Content ID
        source_file_path: Path to video file
        timestamp: Timestamp in seconds (default: 1.0)

    Returns:
        Dict with thumbnail path
    """
    try:
        logger.info(f"Generating thumbnail for content {content_id}...")

        thumbnail_path = _generate_thumbnail(source_file_path, content_id, timestamp)

        if thumbnail_path:
            db = SessionLocal()
            try:
                content_repo = ContentRepository(db)
                content_repo.update(content_id, {"thumbnail_url": thumbnail_path})
            finally:
                db.close()

        return {
            "status": "success",
            "content_id": content_id,
            "thumbnail": thumbnail_path,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error generating thumbnail for content {content_id}: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=2)


@celery_app.task(
    bind=True,
    name="app.tasks.content_tasks.optimize_image",
    queue="default"
)
def optimize_image(
    self: Task,
    content_id: int,
    source_file_path: str,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85
) -> Dict[str, Any]:
    """
    Optimize image - resize and compress.

    Args:
        content_id: Content ID
        source_file_path: Path to image file
        max_width: Maximum width (default: 1920)
        max_height: Maximum height (default: 1080)
        quality: JPEG quality (default: 85)

    Returns:
        Dict with optimization results
    """
    try:
        from PIL import Image

        logger.info(f"Optimizing image for content {content_id}...")

        # Open image
        with Image.open(source_file_path) as img:
            # Get original dimensions
            original_width, original_height = img.size
            original_size = os.path.getsize(source_file_path)

            # Calculate new dimensions (maintain aspect ratio)
            if original_width > max_width or original_height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Save optimized image
            optimized_path = source_file_path.replace('.', '_optimized.')
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)

            optimized_size = os.path.getsize(optimized_path)
            new_width, new_height = img.size

        # Update content record
        db = SessionLocal()
        try:
            content_repo = ContentRepository(db)
            content_repo.update(content_id, {
                "width": new_width,
                "height": new_height,
                "resolution": f"{new_width}x{new_height}",
                "file_size": optimized_size
            })

            # Log activity
            log_activity(
                db=db,
                action=ActivityAction.UPDATE,
                entity_type=EntityType.CONTENT,
                entity_id=content_id,
                description=f"Image optimized: {original_width}x{original_height} → {new_width}x{new_height}",
                metadata={
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "reduction_percent": round((1 - optimized_size/original_size) * 100, 2)
                }
            )
        finally:
            db.close()

        logger.info(f"Image optimization completed for content {content_id}")

        return {
            "status": "success",
            "content_id": content_id,
            "original_size": original_size,
            "optimized_size": optimized_size,
            "reduction_percent": round((1 - optimized_size/original_size) * 100, 2),
            "new_dimensions": f"{new_width}x{new_height}",
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error optimizing image for content {content_id}: {str(e)}")
        raise self.retry(exc=e, countdown=30, max_retries=2)


@celery_app.task(
    bind=True,
    name="app.tasks.content_tasks.cleanup_failed_transcoding",
    queue="maintenance"
)
def cleanup_failed_transcoding(self: Task, hours_threshold: int = 24) -> Dict[str, Any]:
    """
    Cleanup failed transcoding jobs and temporary files.

    Args:
        hours_threshold: Remove failed jobs older than X hours (default: 24)

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        logger.info(f"Cleaning up failed transcoding jobs (threshold: {hours_threshold} hours)...")

        content_repo = ContentRepository(db)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        # Find failed transcoding jobs
        failed_content = db.query(content_repo.model).filter(
            content_repo.model.transcoding_status == "failed",
            content_repo.model.updated_at < cutoff_time
        ).all()

        cleaned_count = 0
        for content in failed_content:
            # Remove temporary transcoding files
            if content.anthias_file_uri:
                file_path = Path(content.anthias_file_uri)
                transcode_dir = file_path.parent / f"transcoded_{content.id}"
                
                if transcode_dir.exists():
                    import shutil
                    shutil.rmtree(transcode_dir, ignore_errors=True)
                    cleaned_count += 1

            # Reset transcoding status to allow retry
            content_repo.update(content.id, {
                "transcoding_status": "pending",
                "transcoding_error": None,
                "transcoding_job_id": None
            })

        logger.info(f"Cleaned up {cleaned_count} failed transcoding jobs")

        return {
            "status": "success",
            "cleaned_count": cleaned_count,
            "threshold_hours": hours_threshold,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Error cleaning up failed transcoding: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_video_metadata(file_path: str) -> Dict[str, Any]:
    """Extract video metadata using FFprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFprobe error: {result.stderr}")
            return {}

        import json
        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})

        return {
            "duration": float(data.get("format", {}).get("duration", 0)),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream.get('width') else None,
            "video_codec": video_stream.get("codec_name"),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")),
            "bitrate": int(data.get("format", {}).get("bit_rate", 0)) // 1000,  # Convert to kbps
            "audio_codec": audio_stream.get("codec_name"),
            "audio_bitrate": int(audio_stream.get("bit_rate", 0)) // 1000 if audio_stream.get("bit_rate") else None,
            "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream.get("sample_rate") else None
        }

    except Exception as e:
        logger.error(f"Error extracting video metadata: {str(e)}")
        return {}


def _generate_thumbnail(file_path: str, content_id: int, timestamp: float = 1.0) -> Optional[str]:
    """Generate thumbnail from video."""
    try:
        output_path = Path(file_path).parent / f"thumbnail_{content_id}.jpg"

        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-ss", str(timestamp),
            "-vframes", "1",
            "-vf", "scale=320:180",
            "-y",  # Overwrite
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg thumbnail error: {result.stderr}")
            return None

        return str(output_path)

    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        return None


def _create_master_playlist(output_path: Path, variants: list):
    """Create HLS master playlist."""
    with open(output_path, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n\n")

        for variant in variants:
            # Extract bitrate number from string like "5000k"
            bitrate = int(variant["bitrate"].replace("k", "")) * 1000
            
            f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bitrate},RESOLUTION={variant['resolution']}\n")
            f.write(f"{Path(variant['playlist']).name}\n\n")
