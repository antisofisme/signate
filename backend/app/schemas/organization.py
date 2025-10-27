"""
Organization Schemas
Pydantic models for organization-related requests and responses
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=2, max_length=100, description="Organization name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, regex="^[a-z0-9-]+$", description="URL-friendly identifier")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")

    @validator('slug')
    def validate_slug(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only lowercase letters, numbers, hyphens, and underscores')
        return v.lower() if v else v

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization"""
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")
    max_devices: int = Field(10, ge=1, le=1000, description="Maximum number of devices")
    max_users: int = Field(5, ge=1, le=100, description="Maximum number of users")
    max_storage_gb: int = Field(10, ge=1, le=1000, description="Maximum storage in GB")

    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading provider of innovative solutions",
                "max_devices": 50,
                "max_users": 20,
                "max_storage_gb": 100,
                "settings": {
                    "theme": "dark",
                    "timezone": "America/New_York"
                }
            }
        }


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Organization Name",
                "description": "Updated description",
                "settings": {
                    "theme": "light"
                }
            }
        }


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: int
    settings: Dict[str, Any]
    max_devices: int
    max_users: int
    max_storage_gb: int
    subscription_tier: str
    subscription_expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed fields (populated by service layer)
    device_count: Optional[int] = 0
    user_count: Optional[int] = 0
    content_count: Optional[int] = 0
    storage_used_gb: Optional[float] = 0.0

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OrganizationStats(BaseModel):
    """Organization statistics"""
    total_devices: int = Field(..., description="Total number of devices")
    active_devices: int = Field(..., description="Number of active devices")
    total_content: int = Field(..., description="Total content items")
    total_playlists: int = Field(..., description="Total playlists")
    total_users: int = Field(..., description="Total users")
    storage_used_gb: float = Field(..., description="Storage used in GB")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OrganizationSettings(BaseModel):
    """Organization settings schema"""
    theme: Optional[str] = Field("light", regex="^(light|dark)$")
    timezone: Optional[str] = Field("UTC")
    language: Optional[str] = Field("en", regex="^[a-z]{2}$")
    date_format: Optional[str] = Field("YYYY-MM-DD")
    time_format: Optional[str] = Field("24h", regex="^(12h|24h)$")
    allow_device_self_registration: bool = Field(False)
    default_content_duration: int = Field(30, ge=5, le=300, description="Default content duration in seconds")
    maintenance_mode: bool = Field(False)
    maintenance_message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "theme": "dark",
                "timezone": "America/New_York",
                "language": "en",
                "allow_device_self_registration": True,
                "default_content_duration": 30
            }
        }


class OrganizationInvite(BaseModel):
    """Schema for inviting user to organization"""
    email: EmailStr = Field(..., description="Email address to invite")
    role_id: int = Field(..., description="Role to assign to invited user")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")
    send_email: bool = Field(True, description="Whether to send invitation email")

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "role_id": 3,
                "message": "Welcome to our organization! Please join us.",
                "send_email": True
            }
        }


class OrganizationSwitchRequest(BaseModel):
    """Schema for switching organization"""
    organization_id: int = Field(..., description="Organization ID to switch to")

    class Config:
        schema_extra = {
            "example": {
                "organization_id": 2
            }
        }


class OrganizationSwitchResponse(BaseModel):
    """Response after switching organization"""
    success: bool
    organization: OrganizationResponse
    new_token: str = Field(..., description="New JWT token with updated organization context")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "organization": {
                    "id": 2,
                    "name": "New Organization",
                    "slug": "new-org"
                },
                "new_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }