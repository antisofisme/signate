"""
Pydantic Schemas
================

Request/Response schemas for API endpoints.
"""

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)

from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationStatsResponse,
    OrganizationPinVerify,
    OrganizationQuotaResponse
)

from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    DeviceTagAssign,
    DeviceTagBulkAssign,
    TagResponse,
    TagDetailResponse,
    TagListResponse,
    TagAssignmentResponse,
    TagStatsResponse
)

from app.schemas.content import (
    ContentUploadMetadata,
    ContentUpdate,
    ContentResponse,
    ContentUploadResponse,
    ContentListResponse,
    ContentStatsResponse,
    StorageUsageResponse,
    ContentFileServeResponse
)

from app.schemas.device import (
    DeviceRegister,
    DeviceUpdate,
    DeviceHeartbeat,
    DeviceResponse,
    DeviceRegisterResponse,
    DeviceListResponse,
    DeviceStatsResponse,
    DeviceHeartbeatResponse
)

from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistContentAdd,
    PlaylistContentReorder,
    PlaylistAssignDevice,
    PlaylistDuplicate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistListResponse,
    PlaylistStatsResponse,
    PlaylistContentAddResponse,
    PlaylistAssignmentResponse,
    DevicePlaylistResponse
)

from app.schemas.command import (
    CommandExecute,
    BatchCommandExecute,
    CommandResponse,
    BatchCommandResponse,
    CommandListResponse,
    CommandStatusUpdate
)

__all__ = [
    # Authentication
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",

    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationListResponse",
    "OrganizationStatsResponse",
    "OrganizationPinVerify",
    "OrganizationQuotaResponse",

    # Tag
    "TagCreate",
    "TagUpdate",
    "DeviceTagAssign",
    "DeviceTagBulkAssign",
    "TagResponse",
    "TagDetailResponse",
    "TagListResponse",
    "TagAssignmentResponse",
    "TagStatsResponse",

    # Content
    "ContentUploadMetadata",
    "ContentUpdate",
    "ContentResponse",
    "ContentUploadResponse",
    "ContentListResponse",
    "ContentStatsResponse",
    "StorageUsageResponse",
    "ContentFileServeResponse",

    # Device
    "DeviceRegister",
    "DeviceUpdate",
    "DeviceHeartbeat",
    "DeviceResponse",
    "DeviceRegisterResponse",
    "DeviceListResponse",
    "DeviceStatsResponse",
    "DeviceHeartbeatResponse",

    # Playlist
    "PlaylistCreate",
    "PlaylistUpdate",
    "PlaylistContentAdd",
    "PlaylistContentReorder",
    "PlaylistAssignDevice",
    "PlaylistDuplicate",
    "PlaylistResponse",
    "PlaylistDetailResponse",
    "PlaylistListResponse",
    "PlaylistStatsResponse",
    "PlaylistContentAddResponse",
    "PlaylistAssignmentResponse",
    "DevicePlaylistResponse",

    # Commands
    "CommandExecute",
    "BatchCommandExecute",
    "CommandResponse",
    "BatchCommandResponse",
    "CommandListResponse",
    "CommandStatusUpdate",
]
