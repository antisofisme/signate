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


# ============================================================================
# QUOTA MODELS
# ============================================================================

class QuotaInfo(BaseModel):
    """Quota information for a resource"""
    max: int
    current: int
    available: int
    
    @property
    def percentage_used(self) -> float:
        """Percentage of quota used"""
        if self.max == 0:
            return 0
        return (self.current / self.max) * 100


class StorageQuotaInfo(BaseModel):
    """Storage quota information"""
    max_items: int
    current_items: int
    available_items: int
    max_size_gb: float
    current_size_gb: float
    available_size_gb: float
    
    @property
    def items_percentage_used(self) -> float:
        """Percentage of item quota used"""
        if self.max_items == 0:
            return 0
        return (self.current_items / self.max_items) * 100
    
    @property
    def size_percentage_used(self) -> float:
        """Percentage of size quota used"""
        if self.max_size_gb == 0:
            return 0
        return (self.current_size_gb / self.max_size_gb) * 100


class OrganizationQuotaResponse(BaseModel):
    """Organization quota status"""
    devices: QuotaInfo
    users: QuotaInfo
    content: StorageQuotaInfo
    playlists: QuotaInfo
    
    # Summary
    total_percentage_used: float = 0
    warnings: list[str] = []
    
    def calculate_summary(self):
        """Calculate summary statistics"""
        # Average percentage across all quotas
        percentages = [
            self.devices.percentage_used,
            self.users.percentage_used,
            self.content.items_percentage_used,
            self.content.size_percentage_used,
            self.playlists.percentage_used
        ]
        self.total_percentage_used = sum(percentages) / len(percentages)
        
        # Generate warnings for quotas over 80%
        self.warnings = []
        if self.devices.percentage_used >= 80:
            self.warnings.append(f"Device quota at {self.devices.percentage_used:.0f}%")
        if self.users.percentage_used >= 80:
            self.warnings.append(f"User quota at {self.users.percentage_used:.0f}%")
        if self.content.items_percentage_used >= 80:
            self.warnings.append(f"Content item quota at {self.content.items_percentage_used:.0f}%")
        if self.content.size_percentage_used >= 80:
            self.warnings.append(f"Storage quota at {self.content.size_percentage_used:.0f}%")
        if self.playlists.percentage_used >= 80:
            self.warnings.append(f"Playlist quota at {self.playlists.percentage_used:.0f}%")


class QuotaCheckResponse(BaseModel):
    """Response for quota check"""
    allowed: bool
    quota: dict
    message: Optional[str] = None


class UpdateOrganizationQuotaRequest(BaseModel):
    """Request to update organization quotas (admin only)"""
    max_devices: Optional[int] = Field(None, ge=1, le=10000, description="Maximum devices allowed")
    max_users: Optional[int] = Field(None, ge=1, le=1000, description="Maximum users allowed")
    max_content_size_gb: Optional[int] = Field(None, ge=1, le=10000, description="Maximum content storage in GB")
    max_content_items: Optional[int] = Field(None, ge=1, le=100000, description="Maximum content items allowed")
    max_playlists: Optional[int] = Field(None, ge=1, le=1000, description="Maximum playlists allowed")
