"""
Tenant API Schemas

Pydantic request/response models for tenant endpoints.

Source: INFRA-LAY2-005-identity-api-contracts.md
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

from ..domain.membership import MemberRole


# ============================================
# Request Models
# ============================================

class CreateTenantRequest(BaseModel):
    """Request to create a new tenant."""
    name: str = Field(..., min_length=2, max_length=100, description="Tenant name")
    slug: Optional[str] = Field(None, min_length=2, max_length=50, pattern="^[a-z0-9-]+$", description="URL-friendly slug")
    billing_email: Optional[EmailStr] = Field(None, description="Billing email address")


class UpdateTenantRequest(BaseModel):
    """Request to update tenant details."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="New name")
    billing_email: Optional[EmailStr] = Field(None, description="New billing email")
    settings: Optional[Dict[str, Any]] = Field(None, description="Settings to merge")


class InviteMemberRequest(BaseModel):
    """Request to invite a member."""
    email: EmailStr = Field(..., description="Email to invite")
    role: str = Field(..., description="Role to assign (admin, member, viewer)")
    message: Optional[str] = Field(None, max_length=500, description="Personal message")


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""
    token: str = Field(..., description="Invitation token from email")


class UpdateMemberRoleRequest(BaseModel):
    """Request to update member role."""
    role: str = Field(..., description="New role (owner, admin, member, viewer)")


class RemoveMemberRequest(BaseModel):
    """Request to remove a member."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for removal")


class TransferOwnershipRequest(BaseModel):
    """Request to transfer ownership."""
    new_owner_user_id: UUID = Field(..., description="User ID of new owner")


# ============================================
# Response Models
# ============================================

class TenantPlanLimits(BaseModel):
    """Plan limits info."""
    max_projects: int
    max_members: int
    max_decisions_per_month: int


class TenantResponse(BaseModel):
    """Tenant details response."""
    tenant_id: str
    name: str
    slug: str
    owner_user_id: str
    plan: str
    status: str
    settings: Dict[str, Any]
    billing_email: Optional[str]
    limits: TenantPlanLimits
    created_at: datetime
    updated_at: datetime


class TenantWithMembershipResponse(BaseModel):
    """Tenant with user's membership info."""
    tenant: TenantResponse
    role: str
    member_count: int


class MembershipResponse(BaseModel):
    """Membership details response."""
    membership_id: str
    user_id: str
    tenant_id: str
    role: str
    status: str
    invited_by_user_id: Optional[str]
    invited_at: Optional[datetime]
    joined_at: Optional[datetime]
    created_at: datetime


class MemberResponse(BaseModel):
    """Member with user details."""
    membership: MembershipResponse
    user_email: Optional[str]
    user_name: Optional[str]


class InvitationResponse(BaseModel):
    """Invitation details response."""
    invitation_id: str
    email: str
    tenant_id: str
    role: str
    status: str
    invited_by_user_id: str
    message: Optional[str]
    expires_at: datetime
    is_expired: bool
    created_at: datetime


# ============================================
# List Responses
# ============================================

class ListTenantsResponse(BaseModel):
    """List tenants response."""
    success: bool = True
    data: List[TenantWithMembershipResponse]
    meta: Dict[str, Any]


class ListMembersResponse(BaseModel):
    """List members response."""
    success: bool = True
    data: Dict[str, Any]  # {members: [], pending_invitations: []}
    meta: Dict[str, Any]


class ListInvitationsResponse(BaseModel):
    """List invitations response."""
    success: bool = True
    data: List[InvitationResponse]
    meta: Dict[str, Any]


# ============================================
# Standard Responses
# ============================================

class TenantCreateResponse(BaseModel):
    """Create tenant response."""
    success: bool = True
    data: Dict[str, Any]  # {tenant, membership}
    message: str = "Tenant created successfully"


class TenantDetailResponse(BaseModel):
    """Get tenant response."""
    success: bool = True
    data: TenantWithMembershipResponse


class TenantUpdateResponse(BaseModel):
    """Update tenant response."""
    success: bool = True
    data: TenantResponse
    message: str = "Tenant updated successfully"


class TenantDeleteResponse(BaseModel):
    """Delete tenant response."""
    success: bool = True
    message: str = "Tenant deleted successfully"


class InvitationCreateResponse(BaseModel):
    """Create invitation response."""
    success: bool = True
    data: InvitationResponse
    message: str = "Invitation sent successfully"


class InvitationAcceptResponse(BaseModel):
    """Accept invitation response."""
    success: bool = True
    data: Dict[str, Any]  # {membership, tenant_id}
    message: str = "Invitation accepted"


class MemberRoleUpdateResponse(BaseModel):
    """Update member role response."""
    success: bool = True
    data: Dict[str, Any]  # {old_role, new_role}
    message: str = "Member role updated"


class MemberRemoveResponse(BaseModel):
    """Remove member response."""
    success: bool = True
    message: str = "Member removed"


# ============================================
# Error Response
# ============================================

class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail
