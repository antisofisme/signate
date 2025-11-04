"""
Authentication DTOs (Data Transfer Objects)
Request/Response models for API layer
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


# =============================================================================
# REQUEST DTOs
# =============================================================================

class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Register request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=100)
    organization_id: Optional[int] = None


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class OrganizationResponse(BaseModel):
    """Organization response"""
    id: int
    name: str
    organization_pin: str
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
