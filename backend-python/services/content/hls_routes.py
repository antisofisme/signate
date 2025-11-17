"""
HLS Streaming Routes
Provides HTTP Live Streaming endpoints for adaptive bitrate video playback

Architecture:
- Master playlist: Lists available quality variants
- Variant playlist: Lists segments for specific quality
- Segments: Video chunks (.ts files)

Directory Structure:
/data/signage/content/uploads/videos/{year}/{month}/org_{org_id}/
└── {uuid}_hls/
    ├── master.m3u8              # Entry point
    ├── 360p/
    │   ├── playlist.m3u8
    │   └── segment_*.ts
    ├── 480p/
    │   ├── playlist.m3u8
    │   └── segment_*.ts
    └── 720p/
        ├── playlist.m3u8
        └── segment_*.ts
"""

from fastapi import APIRouter, HTTPException, Path as PathParam, Response
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from typing import Optional
import os

router = APIRouter(prefix="/content/hls", tags=["HLS Streaming"])

# Base directory for video content
CONTENT_BASE_DIR = Path("/data/signage/content/uploads/videos")


def validate_path_traversal(path: Path) -> None:
    """
    Validate that resolved path is within content directory
    Prevents path traversal attacks (e.g., ../../etc/passwd)

    Args:
        path: Path to validate

    Raises:
        HTTPException: If path is outside content directory
    """
    try:
        resolved = path.resolve()
        base_resolved = CONTENT_BASE_DIR.resolve()

        if not str(resolved).startswith(str(base_resolved)):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Path traversal detected"
            )
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="Invalid path"
        )


@router.get(
    "/{year}/{month}/org_{org_id}/{content_uuid}/master.m3u8",
    response_class=Response,
    summary="Get master playlist",
    description="Returns master HLS playlist with available quality variants"
)
async def get_master_playlist(
    year: str = PathParam(..., regex=r"^\d{4}$"),
    month: str = PathParam(..., regex=r"^(0[1-9]|1[0-2])$"),
    org_id: int = PathParam(..., ge=1),
    content_uuid: str = PathParam(..., regex=r"^[a-f0-9-]{36}$")
):
    """
    Serve master HLS playlist

    Master playlist contains:
    - #EXTM3U header
    - #EXT-X-STREAM-INF for each quality variant
    - Relative paths to variant playlists

    Args:
        year: Year (YYYY)
        month: Month (01-12)
        org_id: Organization ID
        content_uuid: Content UUID

    Returns:
        Master playlist (application/vnd.apple.mpegurl)
    """
    # Construct path
    playlist_path = CONTENT_BASE_DIR / year / month / f"org_{org_id}" / f"{content_uuid}_hls" / "master.m3u8"

    # Validate path
    validate_path_traversal(playlist_path)

    # Check if file exists
    if not playlist_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Master playlist not found: {content_uuid}"
        )

    # Read and return playlist
    try:
        content = playlist_path.read_text()
        return Response(
            content=content,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "public, max-age=3600, immutable",
                "Access-Control-Allow-Origin": "*",
                "X-Content-Type-Options": "nosniff"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading master playlist: {str(e)}"
        )


@router.get(
    "/{year}/{month}/org_{org_id}/{content_uuid}/{quality}/playlist.m3u8",
    response_class=Response,
    summary="Get variant playlist",
    description="Returns HLS variant playlist for specific quality level"
)
async def get_variant_playlist(
    year: str = PathParam(..., regex=r"^\d{4}$"),
    month: str = PathParam(..., regex=r"^(0[1-9]|1[0-2])$"),
    org_id: int = PathParam(..., ge=1),
    content_uuid: str = PathParam(..., regex=r"^[a-f0-9-]{36}$"),
    quality: str = PathParam(..., regex=r"^(360p|480p|720p|1080p)$")
):
    """
    Serve variant HLS playlist

    Variant playlist contains:
    - #EXTM3U header
    - #EXT-X-TARGETDURATION (segment duration)
    - #EXTINF for each segment
    - Segment file names

    Args:
        year: Year (YYYY)
        month: Month (01-12)
        org_id: Organization ID
        content_uuid: Content UUID
        quality: Quality level (360p, 480p, 720p, 1080p)

    Returns:
        Variant playlist (application/vnd.apple.mpegurl)
    """
    # Construct path
    playlist_path = CONTENT_BASE_DIR / year / month / f"org_{org_id}" / f"{content_uuid}_hls" / quality / "playlist.m3u8"

    # Validate path
    validate_path_traversal(playlist_path)

    # Check if file exists
    if not playlist_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Variant playlist not found: {quality}"
        )

    # Read and return playlist
    try:
        content = playlist_path.read_text()
        return Response(
            content=content,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "public, max-age=3600, immutable",
                "Access-Control-Allow-Origin": "*",
                "X-Content-Type-Options": "nosniff"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading variant playlist: {str(e)}"
        )


@router.get(
    "/{year}/{month}/org_{org_id}/{content_uuid}/{quality}/{segment_name}",
    response_class=FileResponse,
    summary="Get video segment",
    description="Returns video segment (.ts file) for HLS playback"
)
async def get_video_segment(
    year: str = PathParam(..., regex=r"^\d{4}$"),
    month: str = PathParam(..., regex=r"^(0[1-9]|1[0-2])$"),
    org_id: int = PathParam(..., ge=1),
    content_uuid: str = PathParam(..., regex=r"^[a-f0-9-]{36}$"),
    quality: str = PathParam(..., regex=r"^(360p|480p|720p|1080p)$"),
    segment_name: str = PathParam(..., regex=r"^segment_\d{3}\.ts$")
):
    """
    Serve video segment

    Segments are MPEG-TS chunks containing video and audio data.
    Each segment is typically 6 seconds of content.

    Args:
        year: Year (YYYY)
        month: Month (01-12)
        org_id: Organization ID
        content_uuid: Content UUID
        quality: Quality level (360p, 480p, 720p, 1080p)
        segment_name: Segment filename (segment_XXX.ts)

    Returns:
        Video segment (video/mp2t)
    """
    # Construct path
    segment_path = CONTENT_BASE_DIR / year / month / f"org_{org_id}" / f"{content_uuid}_hls" / quality / segment_name

    # Validate path
    validate_path_traversal(segment_path)

    # Check if file exists
    if not segment_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Segment not found: {segment_name}"
        )

    # Return segment with proper headers
    return FileResponse(
        path=segment_path,
        media_type="video/mp2t",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",  # 1 year (segments never change)
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff",
            "Accept-Ranges": "bytes"
        }
    )


@router.head(
    "/{year}/{month}/org_{org_id}/{content_uuid}/{quality}/{segment_name}",
    summary="Check segment existence",
    description="HEAD request for segment metadata (used by players for preflight checks)"
)
async def head_video_segment(
    year: str = PathParam(..., regex=r"^\d{4}$"),
    month: str = PathParam(..., regex=r"^(0[1-9]|1[0-2])$"),
    org_id: int = PathParam(..., ge=1),
    content_uuid: str = PathParam(..., regex=r"^[a-f0-9-]{36}$"),
    quality: str = PathParam(..., regex=r"^(360p|480p|720p|1080p)$"),
    segment_name: str = PathParam(..., regex=r"^segment_\d{3}\.ts$")
):
    """
    HEAD request for segment

    Video players often send HEAD requests to check if segments exist
    before downloading them.

    Args:
        year: Year (YYYY)
        month: Month (01-12)
        org_id: Organization ID
        content_uuid: Content UUID
        quality: Quality level
        segment_name: Segment filename

    Returns:
        Empty response with headers
    """
    # Construct path
    segment_path = CONTENT_BASE_DIR / year / month / f"org_{org_id}" / f"{content_uuid}_hls" / quality / segment_name

    # Validate path
    validate_path_traversal(segment_path)

    # Check if file exists
    if not segment_path.exists():
        raise HTTPException(status_code=404, detail="Segment not found")

    # Get file size
    file_size = segment_path.stat().st_size

    # Return headers only
    return Response(
        status_code=200,
        headers={
            "Content-Type": "video/mp2t",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=31536000, immutable",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff",
            "Accept-Ranges": "bytes"
        }
    )
