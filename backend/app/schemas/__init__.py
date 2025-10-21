"""
Pydantic schemas for request/response validation
"""

from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.device import (
    TVRegisterRequest,
    MonitorGenerateRequest,
    MonitorActivateRequest,
    DeviceUpdateRequest,
    HeartbeatRequest,
    DeviceResponse,
    MonitorCodeResponse,
    DeviceListResponse,
    HeartbeatResponse
)
from app.schemas.content import (
    ContentUploadResponse,
    ContentResponse,
    ContentListResponse,
    ContentUpdateRequest,
    ContentAssignRequest,
    ContentAssignmentResponse
)
from app.schemas.client import (
    PlaylistItem,
    PlaylistResponse,
    DeviceStatusResponse
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "TVRegisterRequest",
    "MonitorGenerateRequest",
    "MonitorActivateRequest",
    "DeviceUpdateRequest",
    "HeartbeatRequest",
    "DeviceResponse",
    "MonitorCodeResponse",
    "DeviceListResponse",
    "HeartbeatResponse",
    "ContentUploadResponse",
    "ContentResponse",
    "ContentListResponse",
    "ContentUpdateRequest",
    "ContentAssignRequest",
    "ContentAssignmentResponse",
    "PlaylistItem",
    "PlaylistResponse",
    "DeviceStatusResponse"
]
