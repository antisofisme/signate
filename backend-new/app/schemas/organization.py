"""
Organization Schemas
===================

Pydantic schemas for organization API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================

class OrganizationCreate(BaseModel):
    """Schema for creating new organization."""

    name: str = Field(..., min_length=3, max_length=200, description="Organization name")
    slug: str = Field(..., min_length=3, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    max_devices: int = Field(10, ge=1, le=1000, description="Maximum devices allowed")
    max_users: int = Field(5, ge=1, le=500, description="Maximum users allowed")
    max_storage_gb: int = Field(10, ge=1, le=10000, description="Maximum storage in GB")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format (lowercase alphanumeric + hyphens)."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Digital signage for all Acme locations",
                "max_devices": 50,
                "max_users": 10,
                "max_storage_gb": 100
            }
        }


class OrganizationUpdate(BaseModel):
    """Schema for updating organization."""

    name: Optional[str] = Field(None, min_length=3, max_length=200)
    slug: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    max_devices: Optional[int] = Field(None, ge=1, le=1000)
    max_users: Optional[int] = Field(None, ge=1, le=500)
    max_storage_gb: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate slug format if provided."""
        if v is not None:
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation Updated",
                "max_devices": 100,
                "max_storage_gb": 200
            }
        }


class OrganizationPinVerify(BaseModel):
    """Schema for PIN verification request."""

    pin: str = Field(..., min_length=8, max_length=8, description="8-digit organization PIN")

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Validate PIN is exactly 8 digits."""
        if not v.isdigit():
            raise ValueError("PIN must contain only digits")
        if len(v) != 8:
            raise ValueError("PIN must be exactly 8 digits")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "pin": "12345678"
            }
        }


# ==================== Response Schemas ====================

class OrganizationBase(BaseModel):
    """Base organization response schema."""

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    organization_pin: Optional[str] = Field(None, description="Only returned on creation")
    max_devices: int
    max_users: int
    max_storage_gb: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Digital signage for all Acme locations",
                "organization_pin": "12345678",
                "max_devices": 50,
                "max_users": 10,
                "max_storage_gb": 100,
                "is_active": True,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-20T14:45:00Z"
            }
        }


class OrganizationResponse(OrganizationBase):
    """Standard organization response."""
    pass


class OrganizationQuotaResponse(BaseModel):
    """Response for quota check."""

    organization_id: int
    quota_type: str
    max_allowed: int
    current_usage: int
    available: int
    can_add: bool
    usage_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "quota_type": "devices",
                "max_allowed": 50,
                "current_usage": 35,
                "available": 15,
                "can_add": True,
                "usage_percentage": 70.0
            }
        }


class OrganizationStatsBase(BaseModel):
    """Base stats model."""

    total: int
    active: int
    inactive: int


class OrganizationDeviceStats(OrganizationStatsBase):
    """Device statistics."""

    approved: int
    pending: int
    max_devices: int
    available_slots: int


class OrganizationUserStats(OrganizationStatsBase):
    """User statistics."""

    max_users: int
    available_slots: int


class OrganizationStorageStats(BaseModel):
    """Storage statistics."""

    total_size_bytes: int
    total_size_gb: float
    max_storage_gb: int
    available_gb: float
    usage_percentage: float


class OrganizationContentStats(BaseModel):
    """Content statistics."""

    total: int
    by_type: Dict[str, int]


class OrganizationPlaylistStats(BaseModel):
    """Playlist statistics."""

    total: int
    active: int
    with_content: int
    assigned_to_devices: int


class OrganizationStatsResponse(BaseModel):
    """Comprehensive organization statistics."""

    organization_id: int
    organization_name: str
    devices: OrganizationDeviceStats
    users: OrganizationUserStats
    storage: OrganizationStorageStats
    content: OrganizationContentStats
    playlists: OrganizationPlaylistStats

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "organization_name": "Acme Corporation",
                "devices": {
                    "total": 45,
                    "active": 42,
                    "inactive": 3,
                    "approved": 40,
                    "pending": 5,
                    "max_devices": 50,
                    "available_slots": 5
                },
                "users": {
                    "total": 8,
                    "active": 7,
                    "inactive": 1,
                    "max_users": 10,
                    "available_slots": 2
                },
                "storage": {
                    "total_size_bytes": 75000000000,
                    "total_size_gb": 69.85,
                    "max_storage_gb": 100,
                    "available_gb": 30.15,
                    "usage_percentage": 69.85
                },
                "content": {
                    "total": 150,
                    "by_type": {
                        "video": 80,
                        "image": 60,
                        "web": 10
                    }
                },
                "playlists": {
                    "total": 12,
                    "active": 10,
                    "with_content": 9,
                    "assigned_to_devices": 8
                }
            }
        }


class OrganizationListResponse(BaseModel):
    """Response for list organizations endpoint."""

    organizations: List[OrganizationResponse]
    total: int
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "organizations": [
                    {
                        "id": 1,
                        "name": "Acme Corporation",
                        "slug": "acme-corp",
                        "description": "Digital signage for all Acme locations",
                        "max_devices": 50,
                        "max_users": 10,
                        "max_storage_gb": 100,
                        "is_active": True,
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-01-20T14:45:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }
