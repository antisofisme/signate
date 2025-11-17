"""
Range-supporting Static Files Middleware for Video Streaming
Extends FastAPI StaticFiles to support HTTP Range requests (RFC 7233)
"""

import os
import stat
from typing import Optional
from pathlib import Path

from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response as StarletteResponse
from starlette.types import Scope


class RangeStaticFiles(StaticFiles):
    """
    Static files middleware with HTTP Range request support.

    Enables video streaming by supporting partial content requests.
    Browsers send Range headers like "Range: bytes=0-1023" to request
    specific byte ranges of large files like videos.
    """

    async def __call__(self, scope: Scope, receive, send) -> None:
        """
        Handle incoming requests with Range header support.
        """
        assert scope["type"] == "http"

        # Get request path
        path = scope["path"]
        request = Request(scope, receive=receive)

        # Get full file path
        full_path, stat_result = self.lookup_path_sync(path)

        if full_path is None or not os.path.isfile(full_path):
            # File not found, let parent handle it
            await super().__call__(scope, receive, send)
            return

        # Check for Range header
        range_header = request.headers.get("range")

        if not range_header:
            # No range header, return full file
            await super().__call__(scope, receive, send)
            return

        # Parse Range header
        try:
            byte_range = self._parse_range_header(range_header, stat_result.st_size)
            if byte_range is None:
                # Invalid range, return full file
                await super().__call__(scope, receive, send)
                return

            start, end = byte_range
            content_length = end - start + 1

            # Read file chunk
            with open(full_path, "rb") as f:
                f.seek(start)
                content = f.read(content_length)

            # Get media type
            media_type = self._get_media_type(full_path)

            # Create partial content response
            response = Response(
                content=content,
                status_code=206,  # Partial Content
                media_type=media_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Range": f"bytes {start}-{end}/{stat_result.st_size}",
                    "Content-Length": str(content_length),
                }
            )

            await response(scope, receive, send)

        except Exception as e:
            print(f"Range request error: {e}")
            # Fallback to full file
            await super().__call__(scope, receive, send)

    def _parse_range_header(self, range_header: str, file_size: int) -> Optional[tuple[int, int]]:
        """
        Parse Range header and return (start, end) byte positions.

        Examples:
        - "bytes=0-1023" -> (0, 1023)
        - "bytes=1024-" -> (1024, file_size-1)
        - "bytes=-500" -> (file_size-500, file_size-1)
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

                # Validate range
                if start < 0 or end < start or end >= file_size:
                    # Clamp to valid range
                    start = max(0, start)
                    end = min(end, file_size - 1)

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

    def _get_media_type(self, file_path: str) -> str:
        """Get media type from file extension."""
        import mimetypes
        media_type, _ = mimetypes.guess_type(file_path)
        return media_type or "application/octet-stream"

    def lookup_path_sync(self, path: str):
        """
        Lookup file path and return (full_path, stat_result).
        Synchronous version for our use case.
        """
        for directory in self.all_directories:
            full_path = os.path.normpath(os.path.join(directory, path.lstrip("/")))

            # Security check: ensure path is within directory
            directory_path = os.path.normpath(directory)
            if not full_path.startswith(directory_path):
                continue

            try:
                stat_result = os.stat(full_path)
                if stat.S_ISREG(stat_result.st_mode):
                    return full_path, stat_result
            except (OSError, ValueError):
                continue

        return None, None
