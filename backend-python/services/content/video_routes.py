"""
Video Streaming Routes with Range Request Support
Handles HTTP Range requests (RFC 7233) for video streaming
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["video-streaming"])

CONTENT_DIR = Path("/data/signage/content/uploads")


def get_video_path(file_path: str) -> Path:
    """
    Get full video file path and validate it exists.

    Args:
        file_path: Relative path like "videos/2025/11/org_4/filename.mp4"

    Returns:
        Full resolved path

    Raises:
        HTTPException: If file not found or invalid
    """
    # Remove leading slash if present
    file_path = file_path.lstrip("/")

    # Construct full path
    full_path = CONTENT_DIR / file_path

    # Security: Ensure path is within CONTENT_DIR
    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(CONTENT_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return full_path


def parse_range_header(range_header: str, file_size: int) -> Optional[tuple[int, int]]:
    """
    Parse Range header and return (start, end) byte positions.

    Examples:
        "bytes=0-1023" -> (0, 1023)
        "bytes=1024-" -> (1024, file_size-1)
        "bytes=-500" -> (file_size-500, file_size-1)
    """
    try:
        if not range_header.startswith("bytes="):
            return None

        range_spec = range_header[6:]  # Remove "bytes="

        if "-" not in range_spec:
            return None

        parts = range_spec.split("-", 1)

        # Handle "bytes=start-end"
        if parts[0] and parts[1]:
            start = int(parts[0])
            end = int(parts[1])

            # Validate and clamp range
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))

            return (start, end)

        # Handle "bytes=start-" (from start to end)
        elif parts[0] and not parts[1]:
            start = int(parts[0])
            if start < 0 or start >= file_size:
                return None
            return (start, file_size - 1)

        # Handle "bytes=-count" (last count bytes)
        elif not parts[0] and parts[1]:
            count = int(parts[1])
            if count <= 0:
                return None
            start = max(0, file_size - count)
            return (start, file_size - 1)

        return None

    except (ValueError, IndexError):
        return None


def iter_file_range(file_path: Path, start: int, end: int, chunk_size: int = 8192):
    """
    Generator to yield file chunks for streaming.

    Args:
        file_path: Path to file
        start: Start byte position
        end: End byte position
        chunk_size: Size of each chunk (default 8KB)

    Yields:
        bytes: File chunks
    """
    bytes_to_read = end - start + 1

    with open(file_path, "rb") as f:
        f.seek(start)

        while bytes_to_read > 0:
            chunk = f.read(min(chunk_size, bytes_to_read))
            if not chunk:
                break

            bytes_to_read -= len(chunk)
            yield chunk


@router.get("/content/videos/{year}/{month:int}/org_{org_num}/{filename}")
async def stream_video(
    year: str,
    month: int,
    org_num: int,
    filename: str,
    request: Request
):
    """
    Stream video with Range request support for seeking/scrubbing.

    Path parameters match the storage structure:
        /content/videos/{year}/{month}/org_{org_id}/{filename}

    Supports:
        - Full file download (no Range header)
        - Partial content (Range header present)
        - Multiple range requests for video seeking
    """
    # Construct relative path
    relative_path = f"videos/{year}/{month:02d}/org_{org_num}/{filename}"

    # Get file path
    file_path = get_video_path(relative_path)
    file_size = file_path.stat().st_size

    # Get Range header
    range_header = request.headers.get("range")

    # No Range header - return full file
    if not range_header:
        def iter_full_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

        return StreamingResponse(
            iter_full_file(),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
        )

    # Parse Range header
    byte_range = parse_range_header(range_header, file_size)

    if byte_range is None:
        # Invalid range - return 416 Range Not Satisfiable
        return Response(
            content=f"Invalid range",
            status_code=416,
            headers={
                "Content-Range": f"bytes */{file_size}",
            }
        )

    start, end = byte_range
    content_length = end - start + 1

    # Return partial content (206)
    return StreamingResponse(
        iter_file_range(file_path, start, end),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
        }
    )


@router.get("/content/images/{year}/{month:int}/org_{org_num}/{filename}")
async def serve_image(
    year: str,
    month: int,
    org_num: int,
    filename: str
):
    """
    Serve image files (for consistency with video endpoint).
    Images don't need Range support but we provide same URL structure.
    """
    relative_path = f"images/{year}/{month:02d}/org_{org_num}/{filename}"
    file_path = get_video_path(relative_path)

    # Determine content type from extension
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "application/octet-stream"

    def iter_file():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type=content_type,
        headers={
            "Content-Length": str(file_path.stat().st_size),
        }
    )
