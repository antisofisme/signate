"""
Content Processing Background Tasks - V2 with HLS ABR Support
Handles video transcoding with adaptive bitrate, thumbnail generation, and cleanup

CHANGES FROM V1:
- Added multi-quality HLS transcoding (360p, 480p, 720p, 1080p)
- Improved directory structure (master.m3u8 + quality folders)
- Better error handling with categorization
- Adaptive quality selection based on source resolution
"""

import os
import ffmpeg
from pathlib import Path
from celery import current_task
from celery_app import app
from sqlalchemy.orm import Session
from PIL import Image
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

from shared.database import SessionLocal
from shared.config import settings
from services.content.repositories.models import ContentModel


def get_video_resolution(video_path: Path) -> tuple[int, int]:
    """
    Get video resolution (width, height)

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (width, height)
    """
    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            return (int(video_stream['width']), int(video_stream['height']))
        return (1920, 1080)  # Default fallback
    except Exception as e:
        print(f"[Resolution] Could not detect resolution: {e}")
        return (1920, 1080)  # Default fallback


def select_quality_variants(source_height: int) -> List[Dict]:
    """
    Select appropriate HLS quality variants based on source resolution
    Prevents upscaling which wastes storage and bandwidth

    Args:
        source_height: Source video height in pixels

    Returns:
        List of quality variant configurations
    """
    # All possible quality variants
    all_variants = [
        {'name': '360p', 'height': 360, 'bitrate': '800k', 'audio': '96k'},
        {'name': '480p', 'height': 480, 'bitrate': '1400k', 'audio': '128k'},
        {'name': '720p', 'height': 720, 'bitrate': '2800k', 'audio': '128k'},
        {'name': '1080p', 'height': 1080, 'bitrate': '5000k', 'audio': '192k'},
    ]

    # Filter variants that are <= source resolution (no upscaling)
    available_variants = [v for v in all_variants if v['height'] <= source_height]

    # Always include at least 360p
    if not available_variants:
        available_variants = [all_variants[0]]

    print(f"[Quality] Source height: {source_height}px")
    print(f"[Quality] Selected variants: {[v['name'] for v in available_variants]}")

    return available_variants


def calculate_width(height: int, aspect_ratio: float = 16/9) -> int:
    """Calculate width from height maintaining aspect ratio"""
    width = int(height * aspect_ratio)
    # Round to nearest even number (required by H.264)
    return width + (width % 2)


@app.task(bind=True, name='tasks.content_tasks.transcode_to_hls_v2', max_retries=3)
def transcode_to_hls_v2(self, content_id: int):
    """
    Transcode video to HLS format with adaptive bitrate streaming

    Creates multiple quality variants (360p, 480p, 720p, 1080p) based on source resolution.
    Each variant is stored in its own directory with segments and playlist.

    Directory Structure:
        {video_uuid}_hls/
            ├── master.m3u8          # Master playlist (ABR)
            ├── 360p/
            │   ├── playlist.m3u8
            │   └── segment_*.ts
            ├── 480p/
            │   ├── playlist.m3u8
            │   └── segment_*.ts
            └── 720p/
                ├── playlist.m3u8
                └── segment_*.ts

    Args:
        content_id: Content ID from database

    Returns:
        Dictionary with transcoding results
    """
    db = SessionLocal()
    content = None

    try:
        # Get content from database
        content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Update status to processing
        content.transcoding_status = 'processing'
        content.transcoding_progress = 0
        content.transcoding_job_id = self.request.id
        db.commit()

        # Get file paths
        source_path = Path(content.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Get video metadata
        probe = ffmpeg.probe(str(source_path))
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if not video_stream:
            raise ValueError("No video stream found in file")

        duration = float(video_stream.get('duration', 0))
        source_width, source_height = get_video_resolution(source_path)

        # Create HLS output directory
        hls_dir = source_path.parent / f"{source_path.stem}_hls"
        hls_dir.mkdir(parents=True, exist_ok=True)

        print(f"[Transcode] Starting HLS ABR transcode for content {content_id}")
        print(f"[Transcode] Source: {source_path}")
        print(f"[Transcode] Resolution: {source_width}x{source_height}")
        print(f"[Transcode] Duration: {duration}s")
        print(f"[Transcode] Output: {hls_dir}")

        # Select quality variants based on source resolution
        variants = select_quality_variants(source_height)

        # Transcode each quality variant
        master_playlist_lines = ['#EXTM3U', '#EXT-X-VERSION:3']
        transcoded_variants = []

        for idx, variant in enumerate(variants):
            variant_name = variant['name']
            variant_dir = hls_dir / variant_name
            variant_dir.mkdir(parents=True, exist_ok=True)

            playlist_path = variant_dir / 'playlist.m3u8'
            segment_pattern = str(variant_dir / 'segment_%03d.ts')

            print(f"[Transcode] Processing variant {idx+1}/{len(variants)}: {variant_name}")

            try:
                # Input stream
                input_stream = ffmpeg.input(str(source_path))

                # Calculate width maintaining aspect ratio
                variant_width = calculate_width(variant['height'], source_width/source_height)

                # Output with specific quality settings
                output = ffmpeg.output(
                    input_stream,
                    str(playlist_path),
                    format='hls',
                    start_number=0,
                    hls_time=6,  # 6-second segments (balance between startup and overhead)
                    hls_list_size=0,  # Include all segments
                    hls_segment_filename=segment_pattern,

                    # Video encoding
                    vcodec='libx264',
                    vf=f"scale={variant_width}:{variant['height']}",  # Scale to target resolution
                    video_bitrate=variant['bitrate'],
                    maxrate=variant['bitrate'],
                    bufsize=f"{int(variant['bitrate'][:-1]) * 2}k",  # 2x bitrate for buffer

                    # Audio encoding
                    acodec='aac',
                    audio_bitrate=variant['audio'],
                    ar='48000',  # 48kHz sample rate
                    ac='2',  # Stereo

                    # Quality settings
                    preset='medium',  # Balance between speed and quality
                    profile='high',  # H.264 profile
                    level='4.0',  # Compatibility level
                    movflags='+faststart',  # Enable streaming

                    # HLS-specific
                    hls_flags='independent_segments',  # Enable seeking

                    # GOP (Group of Pictures) settings
                    g=180,  # GOP size (6 seconds * 30 fps = 180 frames)
                    keyint_min=180,
                    sc_threshold=0,  # Disable scene change detection
                )

                # Run FFmpeg for this variant
                ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)

                print(f"[Transcode] Variant {variant_name} completed")

                # Calculate bandwidth for master playlist
                video_bps = int(variant['bitrate'][:-1]) * 1000  # Convert k to bps
                audio_bps = int(variant['audio'][:-1]) * 1000
                bandwidth = video_bps + audio_bps

                # Add to master playlist
                master_playlist_lines.append(
                    f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},"
                    f"RESOLUTION={variant_width}x{variant['height']},"
                    f"CODECS=\"avc1.640028,mp4a.40.2\""
                )
                master_playlist_lines.append(f"{variant_name}/playlist.m3u8")

                transcoded_variants.append(variant_name)

                # Update progress
                progress = int(((idx + 1) / len(variants)) * 100)
                content.transcoding_progress = progress
                db.commit()

            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if e.stderr else str(e)
                print(f"[Transcode] FFmpeg error for variant {variant_name}: {error_message}")
                # Continue with next variant instead of failing completely
                continue

        # Write master playlist
        master_playlist_path = hls_dir / 'master.m3u8'
        master_playlist_path.write_text('\n'.join(master_playlist_lines))

        print(f"[Transcode] Master playlist created: {master_playlist_path}")

        # Count total segments
        segment_count = sum(len(list((hls_dir / variant['name']).glob('*.ts'))) for variant in variants if (hls_dir / variant['name']).exists())

        # Update content record
        content.transcoding_status = 'completed'
        content.transcoding_progress = 100
        content.hls_master_playlist_path = str(master_playlist_path.relative_to(source_path.parent.parent.parent))
        content.hls_variants = json.dumps({'qualities': transcoded_variants})
        db.commit()

        print(f"[Transcode] HLS ABR transcode completed for content {content_id}")
        print(f"[Transcode] Variants: {transcoded_variants}")
        print(f"[Transcode] Total segments: {segment_count}")

        return {
            'content_id': content_id,
            'status': 'completed',
            'hls_master_playlist_path': content.hls_master_playlist_path,
            'variants': transcoded_variants,
            'segment_count': segment_count,
            'duration': duration
        }

    except ValueError as e:
        # Invalid input (content not found, no video stream)
        print(f"[Transcode] Validation error: {str(e)}")
        if content:
            content.transcoding_status = 'failed'
            content.transcoding_error = str(e)[:500]
            content.transcoding_progress = 0
            db.commit()
        raise

    except FileNotFoundError as e:
        # Source file missing
        print(f"[Transcode] File not found: {str(e)}")
        if content:
            content.transcoding_status = 'failed'
            content.transcoding_error = f"Source file not found: {str(e)}"[:500]
            content.transcoding_progress = 0
            db.commit()
        raise

    except ffmpeg.Error as e:
        # FFmpeg-specific errors
        error_message = e.stderr.decode() if e.stderr else str(e)
        print(f"[Transcode] FFmpeg error: {error_message}")

        if content:
            content.transcoding_status = 'failed'
            content.transcoding_error = f"FFmpeg error: {error_message}"[:500]
            content.transcoding_progress = 0
            db.commit()

        # Retry for transient errors
        if self.request.retries < self.max_retries:
            print(f"[Transcode] Retrying (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

        raise

    except Exception as e:
        # Unexpected errors
        print(f"[Transcode] Unexpected error: {str(e)}")

        if content:
            content.transcoding_status = 'failed'
            content.transcoding_error = str(e)[:500]
            content.transcoding_progress = 0
            db.commit()

        raise

    finally:
        db.close()


# Keep original transcode_to_hls for backward compatibility
@app.task(bind=True, name='tasks.content_tasks.transcode_to_hls')
def transcode_to_hls(self, content_id: int):
    """
    DEPRECATED: Use transcode_to_hls_v2 instead
    Kept for backward compatibility with existing queued tasks
    """
    print(f"[Transcode] Legacy task called, delegating to transcode_to_hls_v2")
    return transcode_to_hls_v2(content_id)


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
        content.thumbnail_url = f"{settings.PUBLIC_BASE_URL}/thumbnails/{thumb_filename}"
        db.commit()

        return {
            'content_id': content_id,
            'thumbnail_url': content.thumbnail_url
        }

    except Exception as e:
        print(f"[Thumbnail] Error: {str(e)}")
        # For thumbnail failures, don't mark content as failed (it's not critical)
        print(f"[Thumbnail] Content {content_id} is still usable without thumbnail")
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
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        print(f"[Cleanup] Cleaning up task results older than {cutoff_date}")

        # This is handled automatically by Celery's result_expires setting
        return {
            'status': 'completed',
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        print(f"[Cleanup] Error: {str(e)}")
        raise
