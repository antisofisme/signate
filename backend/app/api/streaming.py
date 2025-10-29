"""
HLS Streaming API endpoints for Smart TV Digital Signage
Serves transcoded HLS content with HTTP Range Request support
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import os
import json
import hashlib
import asyncio
import aiofiles
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    ValidationException,
    InternalServerException
)
from app.core.cache import cache_get, cache_set, invalidate_by_prefix, CACHE_KEY_PREFIXES
from app.schemas.common import success_response, APIResponse
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.models.content import Content
from app.services.transcoding_service import TranscodingService
from app.schemas.transcoding import TranscodingStatus
from app.core.config import settings

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/content", tags=["streaming"])

# Initialize transcoding service with HLS base directory
HLS_BASE_PATH = os.path.join(settings.DATA_DIRECTORY, "hls")
transcoding_service = TranscodingService(base_hls_dir=HLS_BASE_PATH)

# MIME types for HLS
MIME_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".mp4": "video/mp4",
}

# Cache durations (in seconds)
CACHE_DURATIONS = {
    ".m3u8": 10,      # Playlists - short cache for live updates
    ".ts": 31536000,  # Segments - cache for 1 year (immutable)
    ".mp4": 31536000, # MP4 segments - cache for 1 year
}


def get_etag(file_path: str, mtime: float) -> str:
    """Generate ETag for a file based on path and modification time"""
    etag_base = f"{file_path}:{mtime}"
    return hashlib.md5(etag_base.encode()).hexdigest()


def parse_range_header(range_header: str, file_size: int) -> tuple:
    """
    Parse Range header and return start and end byte positions

    Args:
        range_header: Range header value (e.g., "bytes=0-1023")
        file_size: Total file size in bytes

    Returns:
        Tuple of (start, end, total) byte positions
    """
    try:
        range_spec = range_header.replace("bytes=", "")
        range_parts = range_spec.split("-")

        start = int(range_parts[0]) if range_parts[0] else 0
        end = int(range_parts[1]) if range_parts[1] else file_size - 1

        # Validate range
        if start < 0 or start >= file_size:
            start = 0
        if end >= file_size:
            end = file_size - 1
        if start > end:
            raise ValueError("Invalid range")

        return start, end, file_size
    except Exception as e:
        logger.warning(f"Failed to parse range header: {range_header}, error: {e}")
        return 0, file_size - 1, file_size


async def stream_file_range(file_path: str, start: int, end: int, chunk_size: int = 8192):
    """Async generator to stream file content in chunks"""
    async with aiofiles.open(file_path, 'rb') as file:
        await file.seek(start)
        bytes_to_read = end - start + 1

        while bytes_to_read > 0:
            chunk_size_to_read = min(chunk_size, bytes_to_read)
            chunk = await file.read(chunk_size_to_read)

            if not chunk:
                break

            bytes_to_read -= len(chunk)
            yield chunk


@router.post("/{content_id}/transcode")
async def trigger_transcoding(
    content_id: int,
    quality_levels: List[str] = Query(default=["1080p", "720p", "480p"]),
    force: bool = Query(default=False, description="Force re-transcoding even if files exist"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Trigger HLS transcoding for video content

    Args:
        content_id: Content ID to transcode
        quality_levels: Quality levels to generate (1080p, 720p, 480p, 360p)
        force: Force re-transcoding even if HLS files already exist

    Returns:
        Job ID and status
    """
    request_id = get_request_id(request)

    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(
            message=f"Content not found",
            details={"content_id": content_id}
        )

    # Validate content type
    if content.content_type != "video":
        raise BadRequestException(
            message="Only video content can be transcoded",
            details={"content_type": content.content_type}
        )

    # Check if already transcoded (unless force=True)
    hls_path = os.path.join(HLS_BASE_PATH, str(content_id), "master.m3u8")
    if os.path.exists(hls_path) and not force:
        return success_response(
            data={
                "content_id": content_id,
                "status": "completed",
                "message": "Content already transcoded",
                "master_playlist": f"/api/content/{content_id}/stream/master.m3u8",
                "available_qualities": transcoding_service.get_available_qualities(content_id)
            },
            request_id=request_id
        )

    # Prepare output directory
    output_dir = os.path.join(HLS_BASE_PATH, str(content_id))

    # Start transcoding job (async but runs in background)
    try:
        # Download source file if it's a URL (anthias_url)
        source_path = content.anthias_url

        # Run transcoding asynchronously
        async def run_transcoding():
            await transcoding_service.transcode_to_hls(
                source_path=source_path,
                output_dir=output_dir,
                content_id=content_id,
                quality_levels=quality_levels if quality_levels else None,
                overwrite=force
            )

        # Add to background tasks
        background_tasks.add_task(run_transcoding)

        # Generate job ID
        job_id = transcoding_service._generate_job_id(content_id)

    except Exception as e:
        logger.error(f"Failed to start transcoding: {e}")
        raise InternalServerException(
            message="Failed to start transcoding",
            details={"error": str(e)}
        )

    logger.info(
        "Transcoding job started",
        request_id=request_id,
        content_id=content_id,
        job_id=job_id,
        quality_levels=quality_levels
    )

    # Invalidate content cache to reflect transcoding status
    invalidate_by_prefix(f"content:{content_id}")

    return success_response(
        data={
            "job_id": job_id,
            "content_id": content_id,
            "status": "processing",
            "message": "Transcoding job started",
            "quality_levels": quality_levels
        },
        request_id=request_id
    )


@router.get("/{content_id}/stream")
async def get_stream_info(
    content_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get streaming information for content

    Returns master playlist URL and available qualities
    """
    request_id = get_request_id(request)

    # Get content from database
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(
            message="Content not found",
            details={"content_id": content_id}
        )

    # Check if transcoded
    hls_path = os.path.join(HLS_BASE_PATH, str(content_id), "master.m3u8")
    if not os.path.exists(hls_path):
        # Check if transcoding is in progress
        job_id = transcoding_service._generate_job_id(content_id)
        job_status = transcoding_service.get_job_progress(job_id)
        if job_status and job_status.status == TranscodingStatus.PROCESSING:
            return success_response(
                data={
                    "content_id": content_id,
                    "status": "processing",
                    "message": "Transcoding in progress",
                    "progress": job_status.progress
                },
                request_id=request_id,
                status_code=status.HTTP_202_ACCEPTED
            )
        else:
            raise NotFoundException(
                message="HLS stream not available",
                details={"content_id": content_id, "reason": "Not transcoded"}
            )

    # Get available qualities by checking the directory
    available_qualities = []
    if os.path.exists(hls_path):
        for item in os.listdir(os.path.dirname(hls_path)):
            item_path = os.path.join(os.path.dirname(hls_path), item)
            if os.path.isdir(item_path) and item in ["1080p", "720p", "480p", "360p"]:
                available_qualities.append(item)
        available_qualities.sort(key=lambda x: int(x[:-1]), reverse=True)

    return success_response(
        data={
            "content_id": content_id,
            "title": content.title,
            "content_type": content.content_type,
            "master_playlist": f"/api/content/{content_id}/stream/master.m3u8",
            "available_qualities": available_qualities,
            "duration": content.video_duration,
            "status": "ready"
        },
        request_id=request_id
    )


@router.get("/{content_id}/stream/master.m3u8")
async def serve_master_playlist(
    content_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Serve HLS master playlist

    Returns master.m3u8 file with appropriate cache headers
    """
    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(message="Content not found")

    # Get master playlist path
    master_path = os.path.join(HLS_BASE_PATH, str(content_id), "master.m3u8")
    if not os.path.exists(master_path):
        raise NotFoundException(
            message="Master playlist not found",
            details={"content_id": content_id}
        )

    # Get file stats for ETag
    file_stat = os.stat(master_path)
    etag = get_etag(master_path, file_stat.st_mtime)

    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    # Return playlist with cache headers
    return FileResponse(
        path=master_path,
        media_type=MIME_TYPES[".m3u8"],
        headers={
            "Cache-Control": f"public, max-age={CACHE_DURATIONS['.m3u8']}",
            "ETag": etag,
            "Accept-Ranges": "none",  # Playlists don't support range requests
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.get("/{content_id}/stream/{quality}/{segment}")
async def serve_segment(
    content_id: int,
    quality: str,
    segment: str,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Serve HLS segment with HTTP Range Request support

    Args:
        content_id: Content ID
        quality: Quality level (e.g., "1080p", "720p")
        segment: Segment filename (e.g., "segment0.ts", "playlist.m3u8")

    Returns:
        Segment file with appropriate headers and Range support
    """
    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(message="Content not found")

    # Validate quality level
    if quality not in ["1080p", "720p", "480p", "360p"]:
        raise BadRequestException(
            message="Invalid quality level",
            details={"quality": quality}
        )

    # Get segment path
    segment_path = os.path.join(HLS_BASE_PATH, str(content_id), quality, segment)
    if not os.path.exists(segment_path):
        raise NotFoundException(
            message="Segment not found",
            details={"segment": segment}
        )

    # Determine file extension and MIME type
    file_ext = os.path.splitext(segment)[1].lower()
    mime_type = MIME_TYPES.get(file_ext, "application/octet-stream")

    # Get file stats
    file_stat = os.stat(segment_path)
    file_size = file_stat.st_size
    etag = get_etag(segment_path, file_stat.st_mtime)

    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    # Handle Range requests for .ts segments
    range_header = request.headers.get("range")
    if range_header and file_ext == ".ts":
        # Parse Range header
        start, end, total = parse_range_header(range_header, file_size)

        # Create streaming response for range request
        headers = {
            "Content-Type": mime_type,
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{total}",
            "Content-Length": str(end - start + 1),
            "Cache-Control": f"public, max-age={CACHE_DURATIONS.get(file_ext, 3600)}, immutable",
            "ETag": etag,
            "X-Content-Type-Options": "nosniff"
        }

        return StreamingResponse(
            stream_file_range(segment_path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers
        )

    # Regular response (no range request or for .m3u8 files)
    headers = {
        "Cache-Control": f"public, max-age={CACHE_DURATIONS.get(file_ext, 3600)}",
        "ETag": etag,
        "Accept-Ranges": "bytes" if file_ext == ".ts" else "none",
        "X-Content-Type-Options": "nosniff"
    }

    # Add immutable for .ts segments
    if file_ext == ".ts":
        headers["Cache-Control"] += ", immutable"

    return FileResponse(
        path=segment_path,
        media_type=mime_type,
        headers=headers
    )


@router.get("/{content_id}/transcode/status")
async def get_transcode_status(
    content_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get transcoding job status

    Returns current progress and status of transcoding job
    """
    request_id = get_request_id(request)

    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(message="Content not found")

    # Get job status from transcoding service
    job_id = transcoding_service._generate_job_id(content_id)
    job_status = transcoding_service.get_job_progress(job_id)

    if not job_status:
        # Check if already transcoded
        hls_path = os.path.join(HLS_BASE_PATH, str(content_id), "master.m3u8")
        if os.path.exists(hls_path):
            # Get available qualities
            available_qualities = []
            content_dir = os.path.dirname(hls_path)
            for item in os.listdir(content_dir):
                item_path = os.path.join(content_dir, item)
                if os.path.isdir(item_path) and item in ["1080p", "720p", "480p", "360p"]:
                    available_qualities.append(item)
            available_qualities.sort(key=lambda x: int(x[:-1]), reverse=True)

            return success_response(
                data={
                    "content_id": content_id,
                    "status": "completed",
                    "message": "Transcoding completed",
                    "master_playlist": f"/api/content/{content_id}/stream/master.m3u8",
                    "available_qualities": available_qualities
                },
                request_id=request_id
            )
        else:
            return success_response(
                data={
                    "content_id": content_id,
                    "status": "not_started",
                    "message": "No transcoding job found"
                },
                request_id=request_id
            )

    # Convert job status to response format
    status_map = {
        TranscodingStatus.PENDING: "pending",
        TranscodingStatus.PROCESSING: "processing",
        TranscodingStatus.COMPLETED: "completed",
        TranscodingStatus.FAILED: "failed",
        TranscodingStatus.CANCELLED: "cancelled"
    }

    response_data = {
        "content_id": content_id,
        "job_id": job_status.job_id,
        "status": status_map.get(job_status.status, "unknown"),
        "progress": job_status.progress,
        "message": job_status.error_message if job_status.error_message else f"Transcoding {status_map.get(job_status.status, 'in progress')}",
    }

    if job_status.status == TranscodingStatus.COMPLETED:
        response_data["master_playlist"] = f"/api/content/{content_id}/stream/master.m3u8"
        response_data["completed_variants"] = job_status.completed_variants

    return success_response(
        data=response_data,
        request_id=request_id
    )


@router.delete("/{content_id}/transcode")
async def cancel_transcoding(
    content_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Cancel ongoing transcoding job

    Stops the transcoding process and cleans up partial files
    """
    request_id = get_request_id(request)

    # Validate content exists
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundException(message="Content not found")

    # Cancel transcoding job
    job_id = transcoding_service._generate_job_id(content_id)
    result = transcoding_service.cancel_job(job_id)

    if not result:
        raise NotFoundException(
            message="No active transcoding job found",
            details={"content_id": content_id}
        )

    logger.info(
        "Transcoding job cancelled",
        request_id=request_id,
        content_id=content_id
    )

    # Invalidate content cache
    invalidate_by_prefix(f"content:{content_id}")

    return success_response(
        data={
            "content_id": content_id,
            "status": "cancelled",
            "message": "Transcoding job cancelled successfully"
        },
        request_id=request_id
    )