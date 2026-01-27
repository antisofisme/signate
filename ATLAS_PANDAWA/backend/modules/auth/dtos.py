"""
ATLAS_PANDAWA Backend - Auth Module DTOs
Request/Response data transfer objects
Follows CORE-STD-02 validation standards
"""

from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime


# ============================================
# Authentication DTOs
# ============================================

class LoginRequest(BaseModel):
    """Login request DTO"""

    username: str = Field(..., min_length=3, max_length=100, description="Username or email")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    tenant_slug: Optional[str] = Field(None, max_length=100, description="Tenant slug for multi-tenant login")


class LoginResponse(BaseModel):
    """Login response DTO"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserResponse"
    tenant: Optional["TenantResponse"] = None


class RegisterRequest(BaseModel):
    """Registration request DTO"""

    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    full_name: Optional[str] = Field(None, max_length=200, description="User full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    # Tenant creation (optional - for SaaS mode)
    create_tenant: bool = Field(default=False, description="Create new tenant on registration")
    tenant_name: Optional[str] = Field(None, max_length=200, description="Tenant name")


class RefreshTokenRequest(BaseModel):
    """Refresh token request DTO"""

    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response DTO"""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


# ============================================
# User DTOs
# ============================================

class UserResponse(BaseModel):
    """User response DTO"""

    id: UUID4
    username: str
    email: EmailStr
    full_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update DTO"""

    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class ChangePasswordRequest(BaseModel):
    """Change password request DTO"""

    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


# ============================================
# Tenant DTOs
# ============================================

class TenantResponse(BaseModel):
    """Tenant response DTO"""

    id: UUID4
    name: str
    slug: str
    description: Optional[str]
    subscription_status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    """Tenant creation DTO"""

    name: str = Field(..., min_length=3, max_length=200, description="Tenant name")
    slug: str = Field(..., min_length=3, max_length=100, description="Tenant slug (URL-friendly)")
    description: Optional[str] = Field(None, max_length=500, description="Tenant description")


class TenantMemberResponse(BaseModel):
    """Tenant member response DTO"""

    id: UUID4
    tenant_id: UUID4
    user_id: UUID4
    role: str
    is_active: bool
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    """Invite member to tenant DTO"""

    email: EmailStr = Field(..., description="Email of user to invite")
    role: str = Field(default="member", description="Role within tenant")
