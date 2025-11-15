"""
Device Connection Log API Routes
Endpoint for player devices to send connection logs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.responses import success_response
from shared.errors import NotFoundError
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

router = APIRouter()


# ============================================================================
# DTOs
# ============================================================================

class ConnectionLogEntryDTO(BaseModel):
    """Single connection log entry from player"""
    logged_at: datetime = Field(..., description="Timestamp when event occurred")
    event_type: str = Field(..., description="Type: network, server, speed_test")
    status: str = Field(..., max_length=20, description="Event status")
    latency_ms: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = Field(None, max_length=1000)
    download_speed_mbps: Optional[float] = Field(None, ge=0)
    upload_speed_mbps: Optional[float] = Field(None, ge=0)

    # Dedicated fields for better query performance (added in migration 046)
    connection_type: Optional[str] = Field(None, max_length=20, description="Network type: wifi, ethernet, cellular, etc")
    effective_type: Optional[str] = Field(None, max_length=10, description="Effective network type: 4g, 3g, 2g, etc")
    rtt_ms: Optional[int] = Field(None, ge=0, description="Round-trip time in milliseconds")
    endpoint: Optional[str] = Field(None, max_length=200, description="API endpoint accessed")
    http_status: Optional[int] = Field(None, description="HTTP status code")
    test_trigger: Optional[str] = Field(None, max_length=10, description="Speed test trigger: auto or manual")
    test_duration_ms: Optional[int] = Field(None, ge=0, description="Speed test duration in milliseconds")

    metadata: Optional[dict] = Field(default={})


class SaveConnectionLogsDTO(BaseModel):
    """Batch connection logs from player"""
    logs: List[ConnectionLogEntryDTO] = Field(..., min_items=1, max_items=100)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/devices/{device_id}/connection-logs", status_code=status.HTTP_201_CREATED)
def save_connection_logs(
    device_id: int,
    dto: SaveConnectionLogsDTO,
    db: Session = Depends(get_db)
):
    """Save batch of connection logs from player device"""
    from services.device.use_cases.save_connection_logs import SaveConnectionLogs

    try:
        use_case = SaveConnectionLogs(db)
        result = use_case.execute(device_id=device_id, dto=dto)

        return success_response(
            data=result,
            message=f"Successfully saved {result['count']} connection logs"
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
