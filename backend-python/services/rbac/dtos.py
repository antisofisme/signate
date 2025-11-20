"""
RBAC DTOs (Data Transfer Objects)
Request/Response models for Role API
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class RoleCreateRequest(BaseModel):
    """Create role request"""
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=200, description="Role description")
    organization_id: Optional[int] = Field(None, description="Organization ID (None for system roles)")
    permissions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Permissions dict: {resource: [actions]}"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate role name"""
        if not v or not v.strip():
            raise ValueError("Role name cannot be empty")
        # Convert to lowercase with underscores
        return v.strip().lower().replace(" ", "_")

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate permissions structure"""
        if not isinstance(v, dict):
            raise ValueError("Permissions must be a dictionary")

        for resource, actions in v.items():
            if not isinstance(actions, list):
                raise ValueError(f"Actions for '{resource}' must be a list")
            if not all(isinstance(a, str) for a in actions):
                raise ValueError(f"All actions for '{resource}' must be strings")

        return v


class RoleUpdateRequest(BaseModel):
    """Update role request"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="Full permissions dict")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate role name"""
        if v is not None:
            if not v.strip():
                raise ValueError("Role name cannot be empty")
            return v.strip().lower().replace(" ", "_")
        return v

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v: Optional[Dict[str, List[str]]]) -> Optional[Dict[str, List[str]]]:
        """Validate permissions structure"""
        if v is None:
            return v

        if not isinstance(v, dict):
            raise ValueError("Permissions must be a dictionary")

        for resource, actions in v.items():
            if not isinstance(actions, list):
                raise ValueError(f"Actions for '{resource}' must be a list")
            if not all(isinstance(a, str) for a in actions):
                raise ValueError(f"All actions for '{resource}' must be strings")

        return v


class PermissionAddRequest(BaseModel):
    """Add permission to role request"""
    resource: str = Field(..., min_length=1, description="Resource name (e.g., 'devices', 'content')")
    action: str = Field(..., min_length=1, description="Action name (e.g., 'read', 'write', 'delete')")


class PermissionRemoveRequest(BaseModel):
    """Remove permission from role request"""
    resource: str = Field(..., min_length=1, description="Resource name")
    action: str = Field(..., min_length=1, description="Action name")


class PermissionCheckRequest(BaseModel):
    """Check permission request"""
    resource: str = Field(..., min_length=1, description="Resource name")
    action: str = Field(..., min_length=1, description="Action name")


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class RoleResponse(BaseModel):
    """Role response"""
    id: int
    name: str
    description: Optional[str]
    organization_id: Optional[int]
    is_system_role: bool
    permissions: Dict[str, List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    # Audit trail fields (Migration 046)
    created_by_id: Optional[int] = Field(None, description="User who created this role")
    updated_by_id: Optional[int] = Field(None, description="User who last updated this role")

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """Role list response"""
    roles: List[RoleResponse]
    total: int


class PermissionCheckResponse(BaseModel):
    """Permission check response"""
    has_permission: bool
    role_id: int
    role_name: str
    resource: str
    action: str


class PermissionListResponse(BaseModel):
    """List all permissions for a role"""
    role_id: int
    role_name: str
    permissions: Dict[str, List[str]]
    total_resources: int
    total_actions: int


# =============================================================================
# FILTER DTOs
# =============================================================================

class RoleFilterParams(BaseModel):
    """Role filter parameters for list endpoint"""
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    include_system: bool = Field(True, description="Include system roles")
    name: Optional[str] = Field(None, description="Filter by name (partial match)")
