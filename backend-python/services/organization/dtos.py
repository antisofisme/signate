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
    organization_pin: Optional[str] = Field(None, min_length=8, max_length=8, description="Organization PIN (8 digits, auto-generated if not provided)")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")
    address: Optional[str] = Field(None, max_length=500, description="Organization address")
    contact_email: Optional[str] = Field(None, max_length=100, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Organization name cannot be empty')
        return v.strip()

    # REMOVED: Organization PIN validation (No-PIN flow)

    @validator('contact_email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class UpdateOrganizationRequest(BaseModel):
    """Request to update organization"""
    name: str = Field(..., min_length=3, max_length=200, description="Organization name")
    description: Optional[str] = Field(None, max_length=500, description="Organization description")
    address: Optional[str] = Field(None, max_length=500, description="Organization address")
    contact_email: Optional[str] = Field(None, max_length=100, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    is_active: bool = Field(True, description="Organization active status")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Organization name cannot be empty')
        return v.strip()

    @validator('contact_email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class OrganizationResponse(BaseModel):
    """Organization response model"""
    id: int
    name: str
    organization_pin: Optional[str] = None  # REMOVED: Organization PIN (No-PIN flow)
    description: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
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
