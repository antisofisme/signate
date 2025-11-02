"""
Device API Endpoints - HTTP Layer
==================================

API LAYER - Hanya handle HTTP:
- Parse request
- Call service
- Return response

TIDAK BOLEH:
- Business logic (harus di service)
- Database query (harus di repository)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.services.device_service import DeviceService
from app.core.exceptions import (
    DeviceNotFoundException,
    DeviceAlreadyActivatedException,
    InvalidActivationCodeException
)

# Pydantic schemas (TODO: import from app.schemas.device)
from pydantic import BaseModel


class DeviceResponse(BaseModel):
    """Device response schema"""
    id: int
    device_id: Optional[str]
    name: str
    location: Optional[str]
    status: str
    is_online: bool
    last_seen_human: str

    class Config:
        from_attributes = True


class DeviceCreateRequest(BaseModel):
    """Create device request"""
    name: str
    location: Optional[str] = None


class DeviceUpdateRequest(BaseModel):
    """Update device request"""
    name: Optional[str] = None
    location: Optional[str] = None


class DeviceActivateRequest(BaseModel):
    """Activate device request"""
    device_id: str
    activation_code: str


# Router setup
router = APIRouter()


def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    """Dependency injection for DeviceService"""
    return DeviceService(db)


# =============================================================================
# DEVICE CRUD ENDPOINTS
# =============================================================================

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    service: DeviceService = Depends(get_device_service)
):
    """
    Get single device by ID

    Flow:
    1. API receives HTTP request
    2. Call service.get_device()
    3. Service validates & calls repository
    4. Repository executes SQL
    5. API returns JSON response
    """
    try:
        device = service.get_device(device_id)
        return device
    except DeviceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=dict)
async def list_devices(
    organization_id: int = Query(..., description="Organization ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    service: DeviceService = Depends(get_device_service)
):
    """
    List devices dengan pagination

    Query params:
    - organization_id: Required
    - status: Optional (active, inactive, pending)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)

    Returns:
        {
            "items": [...],
            "total": 100,
            "page": 1,
            "per_page": 20,
            "pages": 5
        }
    """
    result = service.get_organization_devices(
        organization_id=organization_id,
        status=status,
        page=page,
        per_page=per_page
    )
    return result


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    organization_id: int,
    request: DeviceCreateRequest,
    service: DeviceService = Depends(get_device_service)
):
    """
    Create new device

    Returns activation code for device registration
    """
    try:
        device = service.create_device(
            organization_id=organization_id,
            name=request.name,
            location=request.location
        )
        return device
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    request: DeviceUpdateRequest,
    service: DeviceService = Depends(get_device_service)
):
    """
    Update device

    Only provided fields will be updated
    """
    try:
        updates = request.dict(exclude_unset=True)
        device = service.update_device(device_id, updates)
        return device
    except DeviceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    service: DeviceService = Depends(get_device_service)
):
    """
    Delete device (soft delete)

    Sets status to inactive
    """
    try:
        service.delete_device(device_id)
        return None
    except DeviceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# DEVICE ACTIVATION (Critical Business Flow)
# =============================================================================

@router.post("/activate", response_model=DeviceResponse)
async def activate_device(
    request: DeviceActivateRequest,
    service: DeviceService = Depends(get_device_service)
):
    """
    Activate device dengan activation code

    Flow (Viewer/TV side):
    1. Display shows activation code (dari database)
    2. User enters code + device_id di web admin
    3. Call this endpoint
    4. Device activated, ready to use

    Request:
        {
            "device_id": "unique-device-id",
            "activation_code": "123456"
        }
    """
    try:
        device = service.activate_device(
            device_id=request.device_id,
            activation_code=request.activation_code
        )
        return device
    except InvalidActivationCodeException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DeviceAlreadyActivatedException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/heartbeat")
async def device_heartbeat(
    device_id: str = Query(..., description="Device unique ID"),
    service: DeviceService = Depends(get_device_service)
):
    """
    Device heartbeat endpoint

    Called by viewer every 30 seconds
    Updates last_seen timestamp
    """
    success = service.process_heartbeat(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"status": "ok", "message": "Heartbeat received"}


# =============================================================================
# DEVICE ANALYTICS & SEARCH
# =============================================================================

@router.get("/dashboard", response_model=dict)
async def device_dashboard(
    organization_id: int = Query(..., description="Organization ID"),
    service: DeviceService = Depends(get_device_service)
):
    """
    Get device dashboard data

    Returns:
        {
            "stats": {
                "total": 100,
                "online": 85,
                "offline": 15,
                "active": 90,
                "inactive": 10
            },
            "online_devices": [...],  # Top 10
            "offline_devices": [...]  # Top 10
        }
    """
    dashboard = service.get_device_dashboard(organization_id)
    return dashboard


@router.get("/search", response_model=List[DeviceResponse])
async def search_devices(
    organization_id: int = Query(..., description="Organization ID"),
    q: str = Query(..., min_length=2, description="Search query"),
    service: DeviceService = Depends(get_device_service)
):
    """
    Search devices by name, device_id, or location

    Query params:
    - organization_id: Required
    - q: Search query (min 2 characters)
    """
    try:
        results = service.search_devices(organization_id, q)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# PATTERN SUMMARY
# =============================================================================

"""
CLEAN ARCHITECTURE PATTERN yang DIPAKAI:

1. REQUEST → API Layer (THIS FILE)
   - Parse HTTP request
   - Validate input format
   - Call service

2. API → SERVICE Layer (device_service.py)
   - Validate business rules
   - Execute business logic
   - Call repository

3. SERVICE → REPOSITORY Layer (device_repository.py)
   - Execute SQL query
   - Return raw data

4. REPOSITORY → DATABASE
   - PostgreSQL query execution

KEUNTUNGAN:
✅ API layer clean - hanya HTTP handling
✅ Business logic centralized di service
✅ Database queries centralized di repository
✅ Easy to test (mock each layer)
✅ Easy to maintain (clear separation)
✅ Easy to scale (can split services)

CONTOH FLOW LENGKAP:

GET /api/devices/123

1. API (devices.py):
   - Terima request
   - Parse device_id=123
   - Call: service.get_device(123)

2. Service (device_service.py):
   - Call: device_repo.get(123)
   - Enrich data (add is_online, last_seen_human)
   - Return enriched data

3. Repository (device_repository.py):
   - Execute: SELECT * FROM devices WHERE id=123
   - Return raw database row

4. Response:
   {
       "id": 123,
       "name": "TV-001",
       "is_online": true,
       "last_seen_human": "2m ago"
   }
"""
