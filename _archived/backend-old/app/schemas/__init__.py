"""
Pydantic schemas for request/response validation
"""

# Common Response Schemas (Quick Wins)
from app.schemas.common import (
    APIResponse,
    PaginatedAPIResponse,
    ErrorResponse,
    ErrorDetail,
    ResponseMeta,
    PaginationMeta,
    success_response,
    error_response,
    paginated_response
)

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
    # Common schemas
    "APIResponse",
    "PaginatedAPIResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ResponseMeta",
    "PaginationMeta",
    "success_response",
    "error_response",
    "paginated_response",
    # Auth schemas
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    # Device schemas
    "TVRegisterRequest",
    "MonitorGenerateRequest",
    "MonitorActivateRequest",
    "DeviceUpdateRequest",
    "HeartbeatRequest",
    "DeviceResponse",
    "MonitorCodeResponse",
    "DeviceListResponse",
    "HeartbeatResponse",
    # Content schemas
    "ContentUploadResponse",
    "ContentResponse",
    "ContentListResponse",
    "ContentUpdateRequest",
    "ContentAssignRequest",
    "ContentAssignmentResponse",
    # Client schemas
    "PlaylistItem",
    "PlaylistResponse",
    "DeviceStatusResponse"
]
