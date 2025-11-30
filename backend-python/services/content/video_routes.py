"""
Video Streaming Routes with Range Request Support
Handles HTTP Range requests (RFC 7233) for video streaming
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["video-streaming"])

CONTENT_DIR = Path("/data/signage/content/uploads")

# Video MIME type mapping for common extensions
VIDEO_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".3gp": "video/3gpp",
    ".3g2": "video/3gpp2",
    ".mts": "video/mp2t",
    ".m2ts": "video/mp2t",
    ".ts": "video/mp2t",
    ".ogv": "video/ogg",
}


def get_video_mime_type(file_path: Path) -> str:
    """
    Get the MIME type for a video file based on extension.

    Args:
        file_path: Path to the video file

    Returns:
        MIME type string, defaults to video/mp4 if unknown
    """
    ext = file_path.suffix.lower()

    # Check our custom mapping first
    if ext in VIDEO_MIME_TYPES:
        return VIDEO_MIME_TYPES[ext]

    # Fallback to mimetypes library
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and mime_type.startswith("video/"):
        return mime_type

    # Default fallback
    return "video/mp4"


def get_video_path(file_path: str) -> Path:
    """
    Get full video file path and validate it exists.
    Supports both new and legacy path structures.

    Args:
        file_path: Relative path like "videos/2025/11/org_4/filename.mp4"

    Returns:
        Full resolved path

    Raises:
        HTTPException: If file not found or invalid
    """
    import glob as glob_module

    # Remove leading slash if present
    file_path = file_path.lstrip("/")

    # Try different path structures
    paths_to_try = []

    # Parse path components
    # Format: {type}s/{year}/{month}/org_{org_id}/{filename}
    parts = file_path.split("/")
    if len(parts) >= 5:
        type_plural = parts[0]  # e.g., "videos", "images", "audios"
        type_singular = type_plural.rstrip("s")  # "video", "image", "audio"
        year = parts[1]
        month = parts[2]
        org_folder = parts[3]  # "org_22"
        filename = parts[4]

        # Extract org_id from "org_22"
        org_id = org_folder.replace("org_", "") if org_folder.startswith("org_") else org_folder

        # Get filename parts (uuid and extension)
        name_without_ext = Path(filename).stem
        ext = Path(filename).suffix

        # 1. New structure (expected): uploads/{type}s/{year}/{month}/org_{org_id}/{filename}
        paths_to_try.append(CONTENT_DIR / file_path)

        # 2. Legacy structure: uploads/{org_id}/{type}/{year}/{month}/{filename}
        legacy_path = CONTENT_DIR / org_id / type_singular / year / month / filename
        paths_to_try.append(legacy_path)

        # 3. Legacy with hash suffix: uploads/{org_id}/{type}/{year}/{month}/{uuid}_*{ext}
        # Files might have hash suffix like: uuid_abc12345.ext
        legacy_dir = CONTENT_DIR / org_id / type_singular / year / month
        if legacy_dir.exists():
            pattern = str(legacy_dir / f"{name_without_ext}_*{ext}")
            matching_files = glob_module.glob(pattern)
            for match in matching_files:
                paths_to_try.append(Path(match))

    else:
        # Simple path, just try as-is
        paths_to_try.append(CONTENT_DIR / file_path)

    # Try each path
    for full_path in paths_to_try:
        try:
            full_path = full_path.resolve()
            # Security: Ensure path is within CONTENT_DIR
            if not str(full_path).startswith(str(CONTENT_DIR.resolve())):
                continue
            # Check if file exists
            if full_path.exists() and full_path.is_file():
                return full_path
        except Exception:
            continue

    # No valid path found
    raise HTTPException(status_code=404, detail=f"File not found: {file_path}")


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

    # Get appropriate MIME type based on file extension
    mime_type = get_video_mime_type(file_path)

    # No Range header - return full file
    if not range_header:
        def iter_full_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

        return StreamingResponse(
            iter_full_file(),
            media_type=mime_type,
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
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
            "Access-Control-Allow-Origin": "*",  # Allow CORS for caching
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
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
            "Access-Control-Allow-Origin": "*",  # Allow CORS for caching
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.get("/content/audios/{year}/{month:int}/org_{org_num}/{filename}")
async def serve_audio(
    year: str,
    month: int,
    org_num: int,
    filename: str
):
    """
    Serve audio files with consistent URL structure.
    """
    relative_path = f"audios/{year}/{month:02d}/org_{org_num}/{filename}"
    file_path = get_video_path(relative_path)

    # Determine content type from extension
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "audio/mpeg"

    def iter_file():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type=content_type,
        headers={
            "Content-Length": str(file_path.stat().st_size),
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )
