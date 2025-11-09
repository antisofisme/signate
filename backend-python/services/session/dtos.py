"""
Session DTOs (Data Transfer Objects)
Request/Response models for Session API
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class SessionCreateRequest(BaseModel):
    """Create session request (internal use)"""
    user_id: int
    organization_id: int
    access_token: str
    refresh_token: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    device_info: Optional[Dict] = None
    session_type: str = Field(default="web", pattern="^(web|api|mobile|device)$")
    expires_in_minutes: int = Field(default=30, ge=1, le=525600)  # Max 1 year


class SessionRevokeRequest(BaseModel):
    """Revoke session request"""
    session_id: Optional[int] = Field(None, description="Session ID to revoke")
    revoke_all: bool = Field(False, description="Revoke all user sessions")


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class SessionResponse(BaseModel):
    """Session response"""
    id: int
    user_id: int
    organization_id: int
    ip_address: str
    user_agent: Optional[str]
    device_info: Optional[Dict]
    session_type: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[SessionResponse]
    total: int
    active: int
    expired: int
    revoked: int


class SessionStatsResponse(BaseModel):
    """Session statistics response"""
    total: int
    active: int
    expired: int
    revoked: int
    by_type: Optional[Dict[str, int]] = None
    by_organization: Optional[Dict[int, int]] = None


class SessionRevokeResponse(BaseModel):
    """Session revoke response"""
    success: bool
    sessions_revoked: int
    message: str


# =============================================================================
# FILTER DTOs
# =============================================================================

class SessionFilterParams(BaseModel):
    """Session filter parameters"""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    session_type: Optional[str] = Field(None, description="Filter by type")
    active_only: bool = Field(True, description="Only show active sessions")
    include_revoked: bool = Field(False, description="Include revoked sessions")
    include_expired: bool = Field(False, description="Include expired sessions")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    limit: int = Field(50, ge=1, le=1000, description="Maximum results")
