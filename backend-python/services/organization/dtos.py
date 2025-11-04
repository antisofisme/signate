"""
Organization DTOs (Data Transfer Objects)
Request and response models for API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateOrganizationRequest(BaseModel):
    """Request to create new organization"""
    name: str = Field(..., min_length=3, max_length=200, description="Organization name")
    organization_pin: Optional[str] = Field(None, min_length=4, max_length=6, description="Organization PIN (auto-generated if not provided)")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Organization name cannot be empty')
        return v.strip()

    @validator('organization_pin')
    def validate_pin(cls, v):
        if v and not v.isalnum():
            raise ValueError('Organization PIN must be alphanumeric')
        return v.upper() if v else None


class UpdateOrganizationRequest(BaseModel):
    """Request to update organization"""
    name: str = Field(..., min_length=3, max_length=200, description="Organization name")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Organization name cannot be empty')
        return v.strip()


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class OrganizationResponse(BaseModel):
    """Organization response model"""
    id: int
    name: str
    organization_pin: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Computed fields (set manually)
    user_count: Optional[int] = 0
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """List of organizations with stats"""
    organizations: list[OrganizationResponse]
    total: int
    active: int
