"""
Device Connection Log API Routes
Endpoint for player devices to send connection logs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.responses import success_response
from shared.errors import NotFoundError

# Import DTOs from central location (avoid duplication)
from .dtos import ConnectionLogEntryDTO, SaveConnectionLogsDTO

router = APIRouter()


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
