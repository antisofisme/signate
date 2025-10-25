"""
Speed Test API endpoints
Provides endpoints for upload speed testing (discards data)
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter(prefix="/api/speedtest", tags=["speedtest"])


@router.post("/upload")
async def upload_speed_test(request: Request):
    """
    Upload speed test endpoint

    Simply receives data and discards it
    Used by clients to measure upload speed
    """
    # Read the body but don't store it
    # This just measures how fast the client can upload
    await request.body()

    # Return minimal response
    return Response(status_code=200, content="OK")


@router.get("/download")
async def download_speed_test(bytes: int = 1000000):
    """
    Download speed test endpoint

    Returns dummy data of specified size for download speed testing
    Default: 1MB
    """
    # Generate dummy data
    dummy_data = b'0' * bytes

    return Response(
        content=dummy_data,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
