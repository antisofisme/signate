"""
Tag Schemas - Pydantic Models for Tag API
==========================================

Request and response schemas for device tag management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class TagCreate(BaseModel):
    """Create new tag"""
    tag_name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")
    color: str = Field("#3B82F6", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    tag_priority: int = Field(0, ge=0, le=100, description="Priority (0-100, higher = more important)")
    organization_id: int = Field(..., gt=0, description="Organization ID")

    @field_validator("tag_name")
    @classmethod
    def validate_tag_name(cls, v: str) -> str:
        """Validate and normalize tag name"""
        # Strip whitespace
        v = v.strip()
        
        # Must not be empty after stripping
        if not v:
            raise ValueError("Tag name cannot be empty")
        
        # Convert to lowercase for consistency
        v = v.lower()
        
        # Check for valid characters (alphanumeric, dash, underscore)
        if not all(c.isalnum() or c in ['-', '_', ' '] for c in v):
            raise ValueError("Tag name can only contain letters, numbers, dash, underscore, and spaces")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tag_name": "lobby",
                "description": "Devices in lobby area",
                "color": "#3B82F6",
                "tag_priority": 10,
                "organization_id": 1
            }
        }


class TagUpdate(BaseModel):
    """Update tag"""
    tag_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    tag_priority: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("tag_name")
    @classmethod
    def validate_tag_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize tag name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Tag name cannot be empty")
            v = v.lower()
            if not all(c.isalnum() or c in ['-', '_', ' '] for c in v):
                raise ValueError("Tag name can only contain letters, numbers, dash, underscore, and spaces")
        return v

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "tag_name": "vip-lounge",
                "description": "VIP area devices",
                "color": "#F59E0B",
                "tag_priority": 20
            }
        }


class DeviceTagAssign(BaseModel):
    """Assign tag to device"""
    device_id: int = Field(..., gt=0, description="Device ID to assign tag to")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 5
            }
        }


class DeviceTagBulkAssign(BaseModel):
    """Assign tag to multiple devices"""
    device_ids: List[int] = Field(..., min_length=1, description="List of device IDs")

    @field_validator("device_ids")
    @classmethod
    def validate_device_ids(cls, v: List[int]) -> List[int]:
        """Validate device IDs"""
        # Remove duplicates
        v = list(set(v))
        
        # Check all positive
        if any(id <= 0 for id in v):
            raise ValueError("All device IDs must be positive")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "device_ids": [1, 2, 3, 5, 8]
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class TagResponse(BaseModel):
    """Standard tag response"""
    id: int
    tag_name: str
    description: Optional[str]
    color: str
    tag_priority: int
    organization_id: int
    created_at: datetime

    # Computed fields
    device_count: int = Field(0, description="Number of devices with this tag")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "tag_name": "lobby",
                "description": "Devices in lobby area",
                "color": "#3B82F6",
                "tag_priority": 10,
                "organization_id": 1,
                "created_at": "2025-10-30T10:00:00Z",
                "device_count": 5
            }
        }


class TagDetailResponse(TagResponse):
    """Detailed tag response with devices"""
    devices: List[dict] = Field(default_factory=list, description="Devices with this tag")

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Paginated tag list response"""
    tags: List[TagResponse]
    total: int = Field(..., description="Total number of tags")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "tags": [
                    {
                        "id": 1,
                        "tag_name": "lobby",
                        "color": "#3B82F6",
                        "tag_priority": 10,
                        "device_count": 5
                    }
                ],
                "total": 25,
                "skip": 0,
                "limit": 20
            }
        }


class DeviceTagResponse(BaseModel):
    """Device-tag assignment response"""
    device_id: int
    tag_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "device_id": 5,
                "tag_id": 1,
                "assigned_at": "2025-10-30T10:00:00Z"
            }
        }


class TagAssignmentResponse(BaseModel):
    """Response after tag assignment"""
    tag_id: int
    tag_name: str
    devices_assigned: int = Field(..., description="Number of devices assigned")
    device_ids: List[int] = Field(..., description="IDs of assigned devices")

    class Config:
        json_schema_extra = {
            "example": {
                "tag_id": 1,
                "tag_name": "lobby",
                "devices_assigned": 3,
                "device_ids": [1, 2, 5]
            }
        }


class TagStatsResponse(BaseModel):
    """Tag statistics"""
    organization_id: int
    total_tags: int
    total_assignments: int = Field(..., description="Total device-tag assignments")
    most_used_tags: List[dict] = Field(..., description="Top 5 most used tags")
    unassigned_devices: int = Field(..., description="Devices without any tags")

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "total_tags": 15,
                "total_assignments": 45,
                "most_used_tags": [
                    {"tag_name": "lobby", "device_count": 10},
                    {"tag_name": "cafe", "device_count": 8}
                ],
                "unassigned_devices": 3
            }
        }
