"""
Content Processing Background Tasks with HLS ABR Support
Handles video transcoding with adaptive bitrate, thumbnail generation, and cleanup

Features:
- Multi-quality HLS transcoding (360p, 480p, 720p, 1080p)
- Adaptive quality selection based on source resolution
- Master playlist (master.m3u8) + quality variants
- Automatic URL generation for streaming
- Better error handling with categorization
- WebSocket progress notifications (Phase 3)
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
import redis
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

from shared.database import SessionLocal
from shared.config import settings
from services.content.repositories.models import ContentModel


def send_websocket_notification(org_id: int, event_type: str, data: dict):
    """
    Send WebSocket notification from Celery task via Redis pub/sub.

    The WebSocket manager's Redis listener will pick this up and broadcast
    to all connected clients in the organization.

    Args:
        org_id: Organization ID to broadcast to
        event_type: Event type string (e.g., 'content.transcoding_progress')
        data: Event data dictionary
    """
    try:
        redis_url = settings.REDIS_URL
        r = redis.from_url(redis_url)

        message = json.dumps({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        # Publish to organization channel
        channel = f"org:{org_id}"
        r.publish(channel, message)

        print(f"[WebSocket] Sent {event_type} to {channel}")

    except Exception as e:
        # Don't fail the task if WebSocket notification fails
        print(f"[WebSocket] Failed to send notification: {e}")


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


@app.task(
    bind=True,
    name='tasks.content_tasks.transcode_to_hls',
    max_retries=3,
    default_retry_delay=300,  # Wait 5 minutes before retry
    autoretry_for=(Exception,),  # Auto-retry on any exception
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=3600,  # Max 1 hour between retries
    retry_jitter=True  # Add randomness to prevent thundering herd
)
def transcode_to_hls(self, content_id: int):
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
        # Log retry attempt
        retry_count = self.request.retries
        if retry_count > 0:
            print(f"[Transcode] Retry attempt {retry_count}/3 for content {content_id}")

        # Get content from database
        content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Update status to processing
        content.transcoding_status = 'processing'
        content.transcoding_progress = 0
        content.transcoding_job_id = self.request.id
        db.commit()

        # Send WebSocket notification - transcoding started
        send_websocket_notification(
            org_id=content.organization_id,
            event_type='content.transcoding_progress',
            data={
                'content_id': content_id,
                'title': content.title,
                'status': 'processing',
                'progress': 0,
                'message': 'Starting transcoding...'
            }
        )

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

                # Send WebSocket notification - variant completed
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_progress',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'status': 'processing',
                        'progress': progress,
                        'current_variant': variant_name,
                        'completed_variants': transcoded_variants.copy(),
                        'total_variants': len(variants),
                        'message': f'Completed {variant_name} ({idx + 1}/{len(variants)})'
                    }
                )

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

        # Calculate relative path for both path and URL
        # Path structure: /data/signage/content/uploads/videos/{year}/{month}/org_{org_id}/{uuid}_hls/master.m3u8

        # Get path components
        full_path_str = str(master_playlist_path)
        path_parts = full_path_str.split('/')

        # Find 'videos' index (plural - matches storage structure)
        try:
            videos_idx = path_parts.index('videos')
        except ValueError:
            # Fallback for legacy 'video' (singular) structure
            print(f"[Transcode] Warning: 'videos' not found, trying 'video'")
            try:
                videos_idx = path_parts.index('video')
                # Legacy path: {org_id}/video/{year}/{month}/{uuid}_hls
                org_id = path_parts[videos_idx - 1]
                year = path_parts[videos_idx + 1]
                month = path_parts[videos_idx + 2]
                hls_folder = path_parts[videos_idx + 3]
                content_uuid = hls_folder.replace('_hls', '')
                hls_url = f"{settings.PUBLIC_BASE_URL}/content/hls/{year}/{month}/org_{org_id}/{content_uuid}/master.m3u8"
                relative_path = Path(year, month, hls_folder, 'master.m3u8')
            except ValueError:
                raise ValueError(f"Could not find video folder in path: {full_path_str}")
        else:
            # New path: videos/{year}/{month}/org_{org_id}/{uuid}_hls
            year = path_parts[videos_idx + 1]       # Year (e.g., '2025')
            month = path_parts[videos_idx + 2]      # Month (e.g., '11')
            org_folder = path_parts[videos_idx + 3] # 'org_22'
            org_id = org_folder.split('_')[1]       # Extract '22' from 'org_22'
            hls_folder = path_parts[videos_idx + 4] # 'uuid_hls'
            content_uuid = hls_folder.replace('_hls', '')  # Remove '_hls' suffix

            # Relative path for database
            relative_path = Path(year, month, org_folder, hls_folder, 'master.m3u8')

            # Construct HLS URL
            # Pattern: {PUBLIC_BASE_URL}/content/hls/{year}/{month}/org_{org_id}/{uuid}/master.m3u8
            hls_url = f"{settings.PUBLIC_BASE_URL}/content/hls/{year}/{month}/{org_folder}/{content_uuid}/master.m3u8"

        # Update content record
        content.transcoding_status = 'completed'
        content.transcoding_progress = 100
        content.hls_master_playlist_path = str(relative_path)
        content.hls_master_playlist_url = hls_url  # ✅ FIX: Set HLS URL
        content.hls_variants = json.dumps({'qualities': transcoded_variants})
        db.commit()

        print(f"[Transcode] HLS URL: {hls_url}")

        print(f"[Transcode] HLS ABR transcode completed for content {content_id}")
        print(f"[Transcode] Variants: {transcoded_variants}")
        print(f"[Transcode] Total segments: {segment_count}")

        # Send WebSocket notification - transcoding completed
        send_websocket_notification(
            org_id=content.organization_id,
            event_type='content.transcoded',
            data={
                'content_id': content_id,
                'title': content.title,
                'status': 'completed',
                'progress': 100,
                'hls_url': hls_url,
                'variants': transcoded_variants,
                'segment_count': segment_count,
                'duration': duration,
                'message': 'Transcoding completed successfully'
            }
        )

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
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] Validation error: {str(e)}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg} (Attempt {retry_count + 1}/3)"[:500]
            content.transcoding_progress = 0
            db.commit()

            # Send WebSocket notification for final failure
            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'status': 'failed',
                        'error': str(e)[:200],
                        'message': f'Transcoding failed: {str(e)[:100]}'
                    }
                )

        # Re-raise to trigger retry
        raise

    except FileNotFoundError as e:
        # Source file missing
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] File not found: {str(e)}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg} (Attempt {retry_count + 1}/3)"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'status': 'failed',
                        'error': 'Source file not found',
                        'message': 'Transcoding failed: Source file not found'
                    }
                )

        # Re-raise to trigger retry
        raise

    except ffmpeg.Error as e:
        # FFmpeg-specific errors
        retry_count = self.request.retries
        error_message = e.stderr.decode() if e.stderr else str(e)
        error_msg = f"[Retry {retry_count}/3] FFmpeg error: {error_message}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"FFmpeg error: {error_message}"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'status': 'failed',
                        'error': error_message[:200],
                        'message': f'Transcoding failed: FFmpeg error'
                    }
                )

        # Re-raise to trigger auto-retry (handled by autoretry_for)
        raise

    except Exception as e:
        # Unexpected errors
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] Unexpected error: {str(e)}"
        print(error_msg)
        print(f"[Transcode] Error type: {type(e).__name__}")
        print(f"[Transcode] Content ID: {content_id}")

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg} (Attempt {retry_count + 1}/3)"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'status': 'failed',
                        'error': str(e)[:200],
                        'message': f'Transcoding failed: {type(e).__name__}'
                    }
                )

        # Re-raise to trigger retry
        raise

    finally:
        db.close()


@app.task(
    bind=True,
    name='tasks.content_tasks.transcode_audio',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def transcode_audio(self, content_id: int):
    """
    Transcode audio to AAC format for optimal browser compatibility.

    Converts any audio format to AAC (M4A container) with:
    - 192kbps bitrate (good quality, reasonable size)
    - 48kHz sample rate (standard for web)
    - Stereo output

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

        if content.content_type != 'audio':
            raise ValueError(f"Content {content_id} is not audio (type: {content.content_type})")

        # Get source file path (file_path contains full absolute path)
        source_path = Path(content.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Update status to processing
        content.transcoding_status = 'processing'
        content.transcoding_progress = 10
        db.commit()

        print(f"[AudioTranscode] Starting transcoding for content {content_id}")
        print(f"[AudioTranscode] Source: {source_path}")

        # Send WebSocket notification - started
        send_websocket_notification(
            org_id=content.organization_id,
            event_type='content.transcoding_progress',
            data={
                'content_id': content_id,
                'title': content.title,
                'type': 'audio',
                'status': 'processing',
                'progress': 10,
                'message': 'Starting audio transcoding...'
            }
        )

        # Check if already in optimal format - skip transcoding
        # These formats are universally supported in modern browsers, no need to transcode:
        # - MP3: Universal support
        # - AAC/M4A: Universal support
        # - OGG/OGA: Chrome, Firefox, Edge, modern Safari
        OPTIMAL_FORMATS = ['.mp3', '.m4a', '.aac', '.ogg', '.oga']
        ext = source_path.suffix.lower()
        if ext in OPTIMAL_FORMATS:
            print(f"[AudioTranscode] Source is already in optimal format ({ext}), marking as completed")
            content.transcoding_status = 'completed'
            content.transcoding_progress = 100
            db.commit()

            send_websocket_notification(
                org_id=content.organization_id,
                event_type='content.transcoded',
                data={
                    'content_id': content_id,
                    'title': content.title,
                    'type': 'audio',
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Audio already in optimal format'
                }
            )

            return {
                'content_id': content_id,
                'status': 'completed',
                'message': 'Already AAC format, no transcoding needed'
            }

        # Output path: same directory, .m4a extension
        output_path = source_path.with_suffix('.m4a')

        # Probe source to get duration
        try:
            probe = ffmpeg.probe(str(source_path))
            duration = float(probe['format'].get('duration', 0))
            print(f"[AudioTranscode] Duration: {duration}s")
        except Exception as e:
            print(f"[AudioTranscode] Warning: Could not probe duration: {e}")
            duration = 0

        content.transcoding_progress = 20
        db.commit()

        # Transcode to AAC
        print(f"[AudioTranscode] Transcoding to AAC: {output_path}")

        try:
            (
                ffmpeg
                .input(str(source_path))
                .output(
                    str(output_path),
                    acodec='aac',
                    audio_bitrate='192k',
                    ar='48000',
                    ac=2,
                    movflags='+faststart'  # Optimize for streaming
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            print(f"[AudioTranscode] FFmpeg error: {error_message}")
            raise

        print(f"[AudioTranscode] Transcoding completed: {output_path}")

        # Verify output exists
        if not output_path.exists():
            raise FileNotFoundError(f"Output file not created: {output_path}")

        # Get output file size
        output_size = output_path.stat().st_size
        print(f"[AudioTranscode] Output size: {output_size / 1024:.1f} KB")

        # Update storage_key and file_path to point to new file
        old_storage_key = content.storage_key
        new_storage_key = old_storage_key.rsplit('.', 1)[0] + '.m4a'
        new_file_path = str(source_path.with_suffix('.m4a'))

        # Update database
        content.storage_key = new_storage_key
        content.file_path = new_file_path
        content.transcoding_status = 'completed'
        content.transcoding_progress = 100
        content.audio_codec = 'aac'
        content.audio_bitrate = 192000
        content.audio_sample_rate = 48000
        content.audio_channels = 2
        db.commit()

        print(f"[AudioTranscode] Database updated, new storage_key: {new_storage_key}")

        # Optionally delete original file (keep for safety)
        # source_path.unlink()

        # Send WebSocket notification - completed
        send_websocket_notification(
            org_id=content.organization_id,
            event_type='content.transcoded',
            data={
                'content_id': content_id,
                'title': content.title,
                'type': 'audio',
                'status': 'completed',
                'progress': 100,
                'duration': duration,
                'output_size': output_size,
                'message': 'Audio transcoding completed'
            }
        )

        return {
            'content_id': content_id,
            'status': 'completed',
            'output_path': str(output_path),
            'output_size': output_size,
            'duration': duration
        }

    except ValueError as e:
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] Validation error: {str(e)}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg}"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'type': 'audio',
                        'status': 'failed',
                        'error': str(e)[:200],
                        'message': f'Audio transcoding failed: {str(e)[:100]}'
                    }
                )
        raise

    except FileNotFoundError as e:
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] File not found: {str(e)}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg}"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'type': 'audio',
                        'status': 'failed',
                        'error': 'Source file not found',
                        'message': 'Audio transcoding failed: Source file not found'
                    }
                )
        raise

    except ffmpeg.Error as e:
        retry_count = self.request.retries
        error_message = e.stderr.decode() if e.stderr else str(e)
        error_msg = f"[Retry {retry_count}/3] FFmpeg error: {error_message}"
        print(error_msg)

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"FFmpeg error: {error_message}"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'type': 'audio',
                        'status': 'failed',
                        'error': error_message[:200],
                        'message': 'Audio transcoding failed: FFmpeg error'
                    }
                )
        raise

    except Exception as e:
        retry_count = self.request.retries
        error_msg = f"[Retry {retry_count}/3] Unexpected error: {str(e)}"
        print(error_msg)
        print(f"[AudioTranscode] Error type: {type(e).__name__}")

        if content:
            is_final_failure = retry_count >= 2
            content.transcoding_status = 'failed' if is_final_failure else 'pending'
            content.transcoding_error = f"{error_msg}"[:500]
            content.transcoding_progress = 0
            db.commit()

            if is_final_failure:
                send_websocket_notification(
                    org_id=content.organization_id,
                    event_type='content.transcoding_failed',
                    data={
                        'content_id': content_id,
                        'title': content.title,
                        'type': 'audio',
                        'status': 'failed',
                        'error': str(e)[:200],
                        'message': f'Audio transcoding failed: {type(e).__name__}'
                    }
                )
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
        content.thumbnail_url = f"{settings.PUBLIC_BASE_URL}/thumbnails/{thumb_filename}"
        content.thumbnail_path = str(thumb_path)
        db.commit()

        # Invalidate cache so frontend gets fresh data with thumbnail
        try:
            from shared.cache import cache
            cache.invalidate_content(content_id, content.organization_id)
            print(f"[Thumbnail] Cache invalidated for content {content_id}")
        except Exception as cache_err:
            print(f"[Thumbnail] Cache invalidation failed (non-critical): {cache_err}")

        # Send WebSocket notification so frontend updates immediately
        send_websocket_notification(
            org_id=content.organization_id,
            event_type='content.thumbnail_ready',
            data={
                'content_id': content_id,
                'title': content.title,
                'thumbnail_url': content.thumbnail_url,
                'message': 'Thumbnail generated successfully'
            }
        )

        print(f"[Thumbnail] Completed for content {content_id}: {content.thumbnail_url}")

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
