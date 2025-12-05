"""
Speed Test Service Routes
Phase 5: Network Upgrades

Provides endpoints for real network speed testing:
- Upload speed test (POST with payload)
- Download speed test (GET with payload)
"""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/api/v1/speed-test", tags=["Speed Test"])


class SpeedTestResult(BaseModel):
    """Speed test result response"""
    test_type: str  # "upload" or "download"
    bytes_transferred: int
    duration_ms: float
    speed_mbps: float
    server_timestamp: str


class UploadTestRequest(BaseModel):
    """Upload test request - accepts any payload"""
    # The actual payload size is measured from request body
    pass


@router.post("/upload", response_model=SpeedTestResult)
async def upload_speed_test(request: Request) -> SpeedTestResult:
    """
    Upload speed test endpoint

    Player sends a POST request with a binary payload.
    Server measures the time to receive the full payload and calculates upload speed.

    Usage:
    - Player sends 100KB-1MB of random data
    - Server measures receipt time
    - Returns speed in Mbps

    Note: This measures the upload speed from player to server,
    which is useful for understanding content submission performance.
    """
    start_time = time.perf_counter()

    # Read the entire request body
    body = await request.body()
    bytes_received = len(body)

    end_time = time.perf_counter()
    duration_seconds = end_time - start_time

    # Avoid division by zero
    if duration_seconds < 0.001:
        duration_seconds = 0.001

    # Calculate speed in Mbps (megabits per second)
    # bytes * 8 = bits, / 1_000_000 = megabits
    speed_mbps = (bytes_received * 8) / (duration_seconds * 1_000_000)

    return SpeedTestResult(
        test_type="upload",
        bytes_transferred=bytes_received,
        duration_ms=round(duration_seconds * 1000, 2),
        speed_mbps=round(speed_mbps, 2),
        server_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )


@router.get("/download")
async def download_speed_test(size_kb: int = 100) -> Response:
    """
    Download speed test endpoint

    Returns a binary payload of specified size for download speed measurement.
    Player measures the time to receive the full payload.

    Args:
        size_kb: Size of payload in kilobytes (default: 100KB, max: 1000KB)

    Usage:
    - Player starts timer
    - Player downloads this payload
    - Player stops timer and calculates speed
    """
    # Limit size to prevent abuse (max 1MB)
    size_kb = min(size_kb, 1000)
    size_bytes = size_kb * 1024

    # Generate random-ish binary data (zeros are fine for speed test)
    payload = b'\x00' * size_bytes

    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(size_bytes),
            "X-Speed-Test-Size-KB": str(size_kb),
            "Cache-Control": "no-store, no-cache, must-revalidate",
        }
    )


@router.get("/ping")
async def ping_test() -> dict:
    """
    Simple ping test for latency measurement

    Returns minimal response for RTT measurement.
    Player measures round-trip time.
    """
    return {
        "pong": True,
        "server_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
