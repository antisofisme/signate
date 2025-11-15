"""
User Management DTOs (Data Transfer Objects)
Request and response models for User Management API
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateUserRequest(BaseModel):
    """Request to create new user"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: str = Field(..., min_length=3, max_length=100, description="Full name")
    role: str = Field(..., description="User role: admin, manager, viewer")
    organization_id: int = Field(..., description="Organization ID")

    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.strip()

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['super_admin', 'admin', 'manager', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class UpdateUserRequest(BaseModel):
    """Request to update user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            valid_roles = ['super_admin', 'admin', 'manager', 'viewer']
            if v not in valid_roles:
                raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class ChangePasswordRequest(BaseModel):
    """Request to change user password"""
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class UserResponse(BaseModel):
    """User response model (without password)"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[int] = None  # Optional untuk backward compatibility dengan data lama
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Computed field (set manually)
    organization_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """List of users"""
    users: list[UserResponse]
    total: int
    active: int
