"""
IAM API Schemas

Pydantic models for IAM API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


# =============================================================================
# User Schemas
# =============================================================================

class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool = False
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None
    membership_role: Optional[str] = None
    joined_at: Optional[str] = None


class UserDetailResponse(UserResponse):
    """User detail response with roles."""
    roles: List[dict] = Field(default_factory=list)


class ListUsersResponse(BaseModel):
    """List users response."""
    success: bool = True
    data: dict  # Contains items, total, page, limit, pages


# =============================================================================
# Role Schemas
# =============================================================================

class RoleResponse(BaseModel):
    """Role response model."""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool = False
    created_at: Optional[str] = None


class RoleDetailResponse(RoleResponse):
    """Role detail response with permissions."""
    can_delete: bool = True
    can_update: bool = True
    updated_at: Optional[str] = None
    permissions: List[dict] = Field(default_factory=list)


class ListRolesResponse(BaseModel):
    """List roles response."""
    success: bool = True
    data: List[RoleResponse]


# =============================================================================
# Permission Schemas
# =============================================================================

class PermissionResponse(BaseModel):
    """Permission response model."""
    id: str
    key: str
    resource: str
    action: str
    description: Optional[str] = None


class ListPermissionsResponse(BaseModel):
    """List permissions response."""
    success: bool = True
    data: List[PermissionResponse]


class PermissionMatrixResponse(BaseModel):
    """Permission matrix response."""
    success: bool = True
    data: dict  # Contains permissions (list of keys) and roles (list with permissions)


# =============================================================================
# Service Account Schemas
# =============================================================================

class ServiceAccountResponse(BaseModel):
    """Service account response model."""
    id: str
    name: str
    description: Optional[str] = None
    client_id: str
    status: str
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None


class ListServiceAccountsResponse(BaseModel):
    """List service accounts response."""
    success: bool = True
    data: dict  # Contains items, total, page, limit, pages


# =============================================================================
# Generic Response Wrappers
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    data: dict


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: dict  # Contains code, message, details


# =============================================================================
# Request Schemas
# =============================================================================

class CreateRoleRequest(BaseModel):
    """Request schema for creating a role."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Role name (lowercase, alphanumeric with underscores)"
    )
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Display name for UI"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Role description"
    )
    permission_ids: Optional[List[UUID]] = Field(
        None,
        description="List of permission UUIDs to assign"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name format."""
        v = v.lower().strip()
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                "Role name must start with a letter and contain only "
                "lowercase letters, numbers, and underscores"
            )
        return v


class UpdateRoleRequest(BaseModel):
    """Request schema for updating a role."""
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Role name (lowercase, alphanumeric with underscores)"
    )
    display_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Display name for UI"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Role description"
    )
    permission_ids: Optional[List[UUID]] = Field(
        None,
        description="List of permission UUIDs (replaces existing)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate role name format."""
        if v is None:
            return v
        v = v.lower().strip()
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                "Role name must start with a letter and contain only "
                "lowercase letters, numbers, and underscores"
            )
        return v


class AssignRoleRequest(BaseModel):
    """Request schema for assigning a role to a user."""
    role_id: UUID = Field(..., description="Role UUID to assign")


class RevokeRoleRequest(BaseModel):
    """Request schema for revoking a role from a user."""
    # Role ID is passed in URL path


class RoleCreatedResponse(BaseModel):
    """Response for role creation."""
    success: bool = True
    data: dict  # Role details


class RoleUpdatedResponse(BaseModel):
    """Response for role update."""
    success: bool = True
    data: dict  # Updated role details


class RoleDeletedResponse(BaseModel):
    """Response for role deletion."""
    success: bool = True
    data: dict = Field(default_factory=lambda: {"deleted": True})


class RoleAssignmentResponse(BaseModel):
    """Response for role assignment/revocation."""
    success: bool = True
    data: dict  # Assignment details with updated roles list
