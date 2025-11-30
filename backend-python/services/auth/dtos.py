"""
Authentication DTOs (Data Transfer Objects)
Request/Response models for API layer
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict


# =============================================================================
# REQUEST DTOs
# =============================================================================

class DeviceInfoRequest(BaseModel):
    """Device info from frontend"""
    platform: Optional[str] = None
    user_agent: Optional[str] = None
    local_ip: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    device_info: Optional[DeviceInfoRequest] = None


class RegisterRequest(BaseModel):
    """Register request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    organization_id: Optional[int] = None


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class OrganizationResponse(BaseModel):
    """Organization response"""
    id: int
    name: str
    organization_pin: Optional[str] = None  # REMOVED: Organization PIN (No-PIN flow)
    portal_slug: Optional[str] = None  # URL-friendly slug for menu portal
    is_active: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


class LoginDataResponse(BaseModel):
    """Login data response - nested data"""
    user: UserResponse
    token: str
    organizations: List[OrganizationResponse]


class LoginResponse(BaseModel):
    """Login response - matches frontend expectations"""
    success: bool = True
    data: LoginDataResponse


class TokenResponse(BaseModel):
    """Token response (for backwards compatibility)"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordResponse(BaseModel):
    """Forgot password response"""
    message: str
    reset_token: Optional[str] = None  # Only included in development mode (no email configured)
    expires_in_minutes: int = 60


class ResetPasswordResponse(BaseModel):
    """Reset password response"""
    message: str
